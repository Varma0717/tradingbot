"""
Grid Trading + DCA (Dollar Cost Averaging) Strategy

This strategy combines:
1. Grid Trading: Places buy/sell orders at predetermined price levels
2. DCA: Averages down on positions during dips
3. Take Profit: Automatically takes profits at key levels

Grid Trading + DCA is considered one of the most profitable strategies
for crypto because it:
- Profits from volatility (which crypto has plenty of)
- Reduces average cost basis through DCA
- Provides consistent returns in ranging markets
- Can be profitable in both bull and bear markets
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional, Tuple, Any
import json

from ..core.config import Config
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class GridDCAStrategy(BaseStrategy):
    """
    Grid Trading + DCA Strategy Implementation

    This strategy places buy orders below current price and sell orders above,
    creating a "grid" of orders. When crypto dips, it uses DCA to average down.
    """

    def __init__(self, strategy_config: Dict[str, Any], config: Config):
        """Initialize the Grid DCA strategy."""
        super().__init__(strategy_config, config)

        self.symbol = strategy_config.get("symbol", "BTC/USDT")
        self.base_asset = self.symbol.split("/")[0]
        self.quote_asset = self.symbol.split("/")[1]

        # Grid Configuration
        self.grid_size = strategy_config.get("grid_size", 10)  # Number of grid levels
        self.grid_spacing = strategy_config.get(
            "grid_spacing", 0.02
        )  # 2% between levels
        self.initial_investment = Decimal(
            str(strategy_config.get("initial_investment", 1000))
        )
        self.max_investment = Decimal(str(strategy_config.get("max_investment", 5000)))

        # DCA Configuration
        self.dca_enabled = strategy_config.get("dca_enabled", True)
        self.dca_percentage = strategy_config.get(
            "dca_percentage", 0.05
        )  # 5% price drop triggers DCA
        self.dca_multiplier = strategy_config.get(
            "dca_multiplier", 1.5
        )  # Increase position size by 50%
        self.max_dca_levels = strategy_config.get("max_dca_levels", 5)

        # Take Profit Configuration
        self.take_profit_percentage = strategy_config.get(
            "take_profit_percentage", 0.03
        )  # 3% profit target
        self.partial_profit_levels = strategy_config.get(
            "partial_profit_levels", [0.02, 0.04, 0.06]
        )  # 2%, 4%, 6%

        # Risk Management
        self.max_position_size = Decimal(
            str(strategy_config.get("max_position_size", 0.1))
        )  # 10% of portfolio
        self.stop_loss_percentage = strategy_config.get(
            "stop_loss_percentage", 0.15
        )  # 15% stop loss

        # State tracking
        self.active_grids = {}
        self.dca_levels = []
        self.current_position = Decimal("0")
        self.average_entry_price = Decimal("0")
        self.total_invested = Decimal("0")
        self.profit_taken = Decimal("0")

        # Statistics
        self.stats = {
            "total_trades": 0,
            "profitable_trades": 0,
            "total_profit": Decimal("0"),
            "total_fees": Decimal("0"),
            "grid_trades": 0,
            "dca_trades": 0,
            "max_drawdown": Decimal("0"),
            "win_rate": 0.0,
        }

        logger.info(f"Grid DCA Strategy initialized for {self.symbol}")
        logger.info(f"Grid size: {self.grid_size}, Spacing: {self.grid_spacing*100}%")
        logger.info(f"Initial investment: ${self.initial_investment}")

    async def initialize(self) -> bool:
        """Initialize the strategy and create initial grid."""
        try:
            # Get current market price
            ticker = await self.exchange.fetch_ticker(self.symbol)
            current_price = Decimal(str(ticker["last"]))

            logger.info(f"Initializing Grid DCA for {self.symbol} at ${current_price}")

            # Create initial grid
            await self.create_initial_grid(current_price)

            return True

        except Exception as e:
            logger.error(f"Error initializing Grid DCA strategy: {e}")
            return False

    async def create_initial_grid(self, current_price: Decimal):
        """Create the initial grid of buy and sell orders."""
        try:
            # Calculate grid levels
            buy_levels = []
            sell_levels = []

            # Create buy levels below current price
            for i in range(1, self.grid_size // 2 + 1):
                price = current_price * (1 - Decimal(str(self.grid_spacing * i)))
                buy_levels.append(price)

            # Create sell levels above current price
            for i in range(1, self.grid_size // 2 + 1):
                price = current_price * (1 + Decimal(str(self.grid_spacing * i)))
                sell_levels.append(price)

            # Calculate order sizes
            base_order_size = self.initial_investment / Decimal(str(len(buy_levels)))

            # Place buy orders
            for i, price in enumerate(buy_levels):
                try:
                    # Calculate quantity
                    quantity = base_order_size / price
                    quantity = self._round_quantity(quantity)

                    if quantity > 0:
                        order = await self.exchange.create_limit_buy_order(
                            self.symbol, quantity, float(price)
                        )

                        self.active_grids[order["id"]] = {
                            "type": "buy",
                            "price": price,
                            "quantity": quantity,
                            "level": i + 1,
                            "timestamp": datetime.now(),
                        }

                        logger.info(
                            f"Placed grid buy order: {quantity} {self.base_asset} at ${price}"
                        )

                except Exception as e:
                    logger.error(f"Error placing buy order at ${price}: {e}")

            # Place initial small position if we have funds
            initial_position_size = self.initial_investment * Decimal(
                "0.1"
            )  # 10% initial position
            initial_quantity = initial_position_size / current_price
            initial_quantity = self._round_quantity(initial_quantity)

            if initial_quantity > 0:
                try:
                    order = await self.exchange.create_market_buy_order(
                        self.symbol, initial_quantity
                    )

                    self.current_position += initial_quantity
                    self.average_entry_price = current_price
                    self.total_invested += initial_position_size

                    logger.info(
                        f"Initial position: {initial_quantity} {self.base_asset} at ${current_price}"
                    )

                    # Place sell orders for the initial position
                    await self._place_take_profit_orders(
                        current_price, initial_quantity
                    )

                except Exception as e:
                    logger.error(f"Error creating initial position: {e}")

        except Exception as e:
            logger.error(f"Error creating initial grid: {e}")

    async def _place_take_profit_orders(self, entry_price: Decimal, quantity: Decimal):
        """Place take profit orders for a position."""
        try:
            # Place partial profit orders
            remaining_quantity = quantity

            for i, profit_level in enumerate(self.partial_profit_levels):
                profit_price = entry_price * (1 + Decimal(str(profit_level)))
                profit_quantity = quantity * Decimal(
                    "0.3"
                )  # 30% of position at each level

                if remaining_quantity > profit_quantity:
                    profit_quantity = self._round_quantity(profit_quantity)

                    if profit_quantity > 0:
                        order = await self.exchange.create_limit_sell_order(
                            self.symbol, profit_quantity, float(profit_price)
                        )

                        self.active_grids[order["id"]] = {
                            "type": "sell",
                            "price": profit_price,
                            "quantity": profit_quantity,
                            "level": f"tp_{i+1}",
                            "timestamp": datetime.now(),
                        }

                        remaining_quantity -= profit_quantity

                        logger.info(
                            f"Placed take profit order: {profit_quantity} {self.base_asset} at ${profit_price}"
                        )

            # Place final take profit order for remaining quantity
            if remaining_quantity > 0:
                final_profit_price = entry_price * (
                    1 + Decimal(str(self.take_profit_percentage))
                )
                remaining_quantity = self._round_quantity(remaining_quantity)

                if remaining_quantity > 0:
                    order = await self.exchange.create_limit_sell_order(
                        self.symbol, remaining_quantity, float(final_profit_price)
                    )

                    self.active_grids[order["id"]] = {
                        "type": "sell",
                        "price": final_profit_price,
                        "quantity": remaining_quantity,
                        "level": "final_tp",
                        "timestamp": datetime.now(),
                    }

                    logger.info(
                        f"Placed final take profit: {remaining_quantity} {self.base_asset} at ${final_profit_price}"
                    )

        except Exception as e:
            logger.error(f"Error placing take profit orders: {e}")

    async def check_dca_opportunity(self, current_price: Decimal) -> bool:
        """Check if DCA conditions are met."""
        if not self.dca_enabled or len(self.dca_levels) >= self.max_dca_levels:
            return False

        if self.average_entry_price == 0:
            return False

        # Check if price has dropped enough to trigger DCA
        price_drop = (
            self.average_entry_price - current_price
        ) / self.average_entry_price

        if price_drop >= self.dca_percentage:
            return True

        return False

    async def execute_dca(self, current_price: Decimal):
        """Execute Dollar Cost Averaging buy."""
        try:
            # Calculate DCA position size (increasing with each level)
            dca_level = len(self.dca_levels) + 1
            dca_amount = self.initial_investment * (
                self.dca_multiplier ** (dca_level - 1)
            )
            dca_amount = min(dca_amount, self.max_investment - self.total_invested)

            if dca_amount <= 0:
                logger.warning("Maximum investment reached, skipping DCA")
                return

            dca_quantity = dca_amount / current_price
            dca_quantity = self._round_quantity(dca_quantity)

            if dca_quantity > 0:
                order = await self.exchange.create_market_buy_order(
                    self.symbol, dca_quantity
                )

                # Update position tracking
                old_total_value = self.current_position * self.average_entry_price
                new_total_value = old_total_value + (dca_quantity * current_price)

                self.current_position += dca_quantity
                self.average_entry_price = new_total_value / self.current_position
                self.total_invested += dca_amount  # Record DCA level
                self.dca_levels.append(
                    {
                        "price": current_price,
                        "quantity": dca_quantity,
                        "amount": dca_amount,
                        "timestamp": datetime.now(),
                    }
                )

                # Update stats
                self.stats["dca_trades"] += 1

                logger.info(
                    f"DCA executed: {dca_quantity} {self.base_asset} at ${current_price}"
                )
                logger.info(f"New average entry: ${self.average_entry_price}")

                # Place new take profit orders for DCA position
                await self._place_take_profit_orders(current_price, dca_quantity)

        except Exception as e:
            logger.error(f"Error executing DCA: {e}")

    async def process_filled_order(self, order_id: str, order_info: Dict):
        """Process a filled grid order."""
        try:
            if order_id not in self.active_grids:
                return

            grid_order = self.active_grids[order_id]
            order_type = grid_order["type"]
            price = grid_order["price"]
            quantity = grid_order["quantity"]

            if order_type == "buy":
                # Buy order filled - update position and place corresponding sell order
                quantity_decimal = Decimal(str(quantity))
                self.current_position += quantity_decimal

                # Update average entry price
                if self.average_entry_price == 0:
                    self.average_entry_price = price
                else:
                    old_total_value = (
                        self.current_position - quantity_decimal
                    ) * self.average_entry_price
                    new_total_value = old_total_value + (quantity_decimal * price)
                    self.average_entry_price = new_total_value / self.current_position

                # Place corresponding sell order
                sell_price = price * (1 + Decimal(str(self.take_profit_percentage)))
                sell_order = await self.exchange.create_limit_sell_order(
                    self.symbol, quantity, float(sell_price)
                )

                self.active_grids[sell_order["id"]] = {
                    "type": "sell",
                    "price": sell_price,
                    "quantity": quantity,
                    "level": f"grid_sell_{grid_order['level']}",
                    "timestamp": datetime.now(),
                }

                # Place new buy order at lower level
                new_buy_price = price * (1 - Decimal(str(self.grid_spacing)))
                new_buy_quantity = (quantity * price) / new_buy_price
                new_buy_quantity = self._round_quantity(new_buy_quantity)

                if new_buy_quantity > 0:
                    buy_order = await self.exchange.create_limit_buy_order(
                        self.symbol, new_buy_quantity, float(new_buy_price)
                    )

                    self.active_grids[buy_order["id"]] = {
                        "type": "buy",
                        "price": new_buy_price,
                        "quantity": new_buy_quantity,
                        "level": grid_order["level"] + 1,
                        "timestamp": datetime.now(),
                    }

                logger.info(
                    f"Grid buy filled: {quantity} {self.base_asset} at ${price}"
                )
                self.stats["grid_trades"] += 1

            elif order_type == "sell":
                # Sell order filled - update position and stats
                quantity_decimal = Decimal(str(quantity))
                self.current_position -= quantity_decimal
                profit = (price - self.average_entry_price) * quantity_decimal
                self.profit_taken += profit

                # Place new sell order at higher level
                new_sell_price = price * (1 + Decimal(str(self.grid_spacing)))
                sell_order = await self.exchange.create_limit_sell_order(
                    self.symbol, quantity, float(new_sell_price)
                )

                self.active_grids[sell_order["id"]] = {
                    "type": "sell",
                    "price": new_sell_price,
                    "quantity": quantity,
                    "level": f"grid_sell_higher_{grid_order['level']}",
                    "timestamp": datetime.now(),
                }

                # Place new buy order to maintain grid
                buy_price = price * (1 - Decimal(str(self.grid_spacing * 2)))
                buy_quantity = (quantity * price) / buy_price
                buy_quantity = self._round_quantity(buy_quantity)

                if buy_quantity > 0:
                    buy_order = await self.exchange.create_limit_buy_order(
                        self.symbol, buy_quantity, float(buy_price)
                    )

                    self.active_grids[buy_order["id"]] = {
                        "type": "buy",
                        "price": buy_price,
                        "quantity": buy_quantity,
                        "level": "grid_rebuy",
                        "timestamp": datetime.now(),
                    }

                logger.info(
                    f"Grid sell filled: {quantity} {self.base_asset} at ${price}, Profit: ${profit}"
                )
                self.stats["grid_trades"] += 1
                self.stats["profitable_trades"] += 1 if profit > 0 else 0
                self.stats["total_profit"] += profit

            # Remove filled order from active grids
            del self.active_grids[order_id]

            # Update total trades
            self.stats["total_trades"] += 1
            self.stats["win_rate"] = (
                self.stats["profitable_trades"] / self.stats["total_trades"]
            ) * 100

        except Exception as e:
            logger.error(f"Error processing filled order {order_id}: {e}")

    async def run_strategy(self):
        """Main strategy execution loop."""
        logger.info("Starting Grid DCA Strategy execution")

        while True:
            try:
                # Get current market data
                ticker = await self.exchange.fetch_ticker(self.symbol)
                current_price = Decimal(str(ticker["last"]))

                # Check for filled orders
                await self._check_filled_orders()

                # Check DCA opportunity
                if await self.check_dca_opportunity(current_price):
                    await self.execute_dca(current_price)

                # Check stop loss
                await self._check_stop_loss(current_price)

                # Log strategy status
                if (
                    self.stats["total_trades"] > 0
                    and self.stats["total_trades"] % 10 == 0
                ):
                    await self._log_strategy_status(current_price)

                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in strategy execution: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _check_filled_orders(self):
        """Check for filled orders and process them."""
        try:
            # Get open orders
            open_orders = await self.exchange.fetch_open_orders(self.symbol)
            open_order_ids = {order["id"] for order in open_orders}

            # Find filled orders
            filled_order_ids = set(self.active_grids.keys()) - open_order_ids

            for order_id in filled_order_ids:
                # Get order details
                order = await self.exchange.fetch_order(order_id, self.symbol)
                await self.process_filled_order(order_id, order)

        except Exception as e:
            logger.error(f"Error checking filled orders: {e}")

    async def _check_stop_loss(self, current_price: Decimal):
        """Check and execute stop loss if necessary."""
        if self.current_position == 0 or self.average_entry_price == 0:
            return

        loss_percentage = (
            self.average_entry_price - current_price
        ) / self.average_entry_price

        if loss_percentage >= self.stop_loss_percentage:
            try:
                # Execute emergency sell
                quantity = self._round_quantity(self.current_position)

                if quantity > 0:
                    order = await self.exchange.create_market_sell_order(
                        self.symbol, quantity
                    )

                    loss = (current_price - self.average_entry_price) * quantity

                    logger.warning(
                        f"STOP LOSS TRIGGERED: Sold {quantity} {self.base_asset} at ${current_price}"
                    )
                    logger.warning(f"Loss: ${loss}")

                    # Reset position
                    self.current_position = Decimal("0")
                    self.average_entry_price = Decimal("0")

                    # Cancel all active orders
                    for order_id in list(self.active_grids.keys()):
                        try:
                            await self.exchange.cancel_order(order_id, self.symbol)
                            del self.active_grids[order_id]
                        except:
                            pass

                    # Restart strategy after stop loss
                    await asyncio.sleep(300)  # Wait 5 minutes
                    await self.initialize()

            except Exception as e:
                logger.error(f"Error executing stop loss: {e}")

    async def _log_strategy_status(self, current_price: Decimal):
        """Log current strategy status."""
        total_value = self.current_position * current_price + self.profit_taken
        total_return = (
            ((total_value - self.total_invested) / self.total_invested) * 100
            if self.total_invested > 0
            else 0
        )

        logger.info("=" * 50)
        logger.info("GRID DCA STRATEGY STATUS")
        logger.info(f"Current Price: ${current_price}")
        logger.info(f"Position: {self.current_position} {self.base_asset}")
        logger.info(f"Average Entry: ${self.average_entry_price}")
        logger.info(f"Total Invested: ${self.total_invested}")
        logger.info(f"Current Value: ${total_value}")
        logger.info(f"Total Return: {total_return:.2f}%")
        logger.info(f"Profit Taken: ${self.profit_taken}")
        logger.info(f"Active Grids: {len(self.active_grids)}")
        logger.info(f"DCA Levels: {len(self.dca_levels)}")
        logger.info(f"Total Trades: {self.stats['total_trades']}")
        logger.info(f"Win Rate: {self.stats['win_rate']:.1f}%")
        logger.info("=" * 50)

    def _round_quantity(self, quantity: Decimal) -> float:
        """Round quantity to exchange precision."""
        # Most exchanges use 6-8 decimal places for crypto
        return float(quantity.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN))

    def get_strategy_stats(self) -> Dict:
        """Get current strategy statistics."""
        return {
            "name": "Grid Trading + DCA",
            "symbol": self.symbol,
            "current_position": float(self.current_position),
            "average_entry_price": float(self.average_entry_price),
            "total_invested": float(self.total_invested),
            "profit_taken": float(self.profit_taken),
            "active_grids": len(self.active_grids),
            "dca_levels": len(self.dca_levels),
            "stats": {
                "total_trades": self.stats["total_trades"],
                "profitable_trades": self.stats["profitable_trades"],
                "total_profit": float(self.stats["total_profit"]),
                "grid_trades": self.stats["grid_trades"],
                "dca_trades": self.stats["dca_trades"],
                "win_rate": self.stats["win_rate"],
            },
        }

    # Abstract method implementations
    @property
    def name(self) -> str:
        """Return the strategy name."""
        return "Grid DCA Strategy"

    @property
    def description(self) -> str:
        """Return the strategy description."""
        return "Grid Trading + DCA strategy that places buy/sell orders at predetermined price levels and averages down during dips"

    @property
    def required_indicators(self) -> List[str]:
        """Return list of required technical indicators."""
        return ["sma", "rsi", "volume"]  # Basic indicators for market analysis

    async def generate_signals(self, market_data) -> List:
        """
        Generate trading signals based on market data.

        For Grid DCA, signals are generated based on grid levels and DCA triggers.
        """
        signals = []

        if market_data is None or len(market_data) == 0:
            return signals

        try:
            current_price = float(market_data.iloc[-1]["close"])

            # Check if we need to trigger DCA
            if self.should_trigger_dca(current_price):
                signals.append(
                    {
                        "action": "dca_buy",
                        "price": current_price,
                        "timestamp": datetime.now(),
                    }
                )

            # Check grid levels for buy/sell signals
            grid_signals = self.check_grid_signals(current_price)
            signals.extend(grid_signals)

        except Exception as e:
            logger.error(f"Error generating signals: {e}")

        return signals

    def should_trigger_dca(self, current_price: float) -> bool:
        """Check if DCA should be triggered."""
        if not self.dca_enabled or len(self.dca_levels) >= self.max_dca_levels:
            return False

        if self.average_entry_price > 0:
            price_drop = (
                self.average_entry_price - current_price
            ) / self.average_entry_price
            return price_drop >= self.dca_percentage

        return False

    def check_grid_signals(self, current_price: float) -> List:
        """Check for grid-based trading signals."""
        signals = []
        # Implementation would check grid levels and generate appropriate signals
        return signals


# Strategy Configuration Template
GRID_DCA_CONFIG = {
    "symbol": "BTC/USDT",
    "grid_size": 10,  # Number of grid levels
    "grid_spacing": 0.02,  # 2% spacing between levels
    "initial_investment": 1000,  # Initial investment amount
    "max_investment": 5000,  # Maximum total investment
    "dca_enabled": True,  # Enable DCA
    "dca_percentage": 0.05,  # 5% drop triggers DCA
    "dca_multiplier": 1.5,  # Increase position by 50% each DCA
    "max_dca_levels": 5,  # Maximum DCA levels
    "take_profit_percentage": 0.03,  # 3% profit target
    "partial_profit_levels": [0.02, 0.04, 0.06],  # Partial profit levels
    "max_position_size": 0.1,  # 10% of portfolio max
    "stop_loss_percentage": 0.15,  # 15% stop loss
}
