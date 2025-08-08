"""
Micro Balance Grid DCA Strategy

Optimized strategy for small balances ($1-$10 USDT)
Focuses on:
- High frequency, small profit trades
- Conservative risk management
- Realistic profit targets
- Efficient use of small capital
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


class MicroBalanceGridDCA(BaseStrategy):
    """
    Specialized Grid DCA Strategy for Micro Balances

    This strategy is optimized for accounts with $1-$10 USDT:
    - Uses smaller, more frequent trades
    - Tighter grid spacing for better entry/exit points
    - Conservative DCA to preserve capital
    - Realistic profit targets (1-2% per trade)
    """

    def __init__(self, strategy_config: Dict[str, Any], config: Config):
        super().__init__(strategy_config, config)

        self.symbol = strategy_config.get("symbol", "BTC/USDT")
        self.base_asset = self.symbol.split("/")[0]
        self.quote_asset = self.symbol.split("/")[1]

        # Micro Balance Optimized Configuration
        self.total_balance = Decimal(str(strategy_config.get("total_balance", 2.16)))
        self.usable_balance = self.total_balance * Decimal("0.9")  # Use 90% of balance

        # Grid Configuration (Optimized for micro balance)
        self.grid_levels = strategy_config.get("grid_levels", 3)  # Only 3 levels
        self.grid_spacing = Decimal(
            str(strategy_config.get("grid_spacing", 0.008))
        )  # 0.8%
        self.order_size = self.usable_balance / self.grid_levels  # Split balance evenly

        # Ensure minimum order size compliance (Binance minimum ~$1)
        self.min_order_size = Decimal("0.50")  # $0.50 minimum
        if self.order_size < self.min_order_size:
            self.grid_levels = max(1, int(self.usable_balance / self.min_order_size))
            self.order_size = self.usable_balance / self.grid_levels

        # DCA Configuration (Very Conservative)
        self.dca_enabled = strategy_config.get("dca_enabled", True)
        self.dca_trigger = Decimal(
            str(strategy_config.get("dca_percentage", 0.02))
        )  # 2%
        self.dca_multiplier = Decimal(
            str(strategy_config.get("dca_multiplier", 1.1))
        )  # 10%
        self.max_dca_levels = strategy_config.get("max_dca_levels", 1)  # Only 1 DCA

        # Profit Taking (Realistic Targets)
        self.profit_target = Decimal(
            str(strategy_config.get("take_profit_percentage", 0.015))
        )  # 1.5%
        self.quick_profit = Decimal(
            str(strategy_config.get("quick_profit", 0.008))
        )  # 0.8%

        # Risk Management (Conservative)
        self.stop_loss = Decimal(
            str(strategy_config.get("stop_loss_percentage", 0.05))
        )  # 5%
        self.max_loss_per_day = Decimal(
            str(strategy_config.get("max_daily_loss", 0.15))
        )  # $0.15

        # State Tracking
        self.active_orders = {}
        self.current_position = Decimal("0")
        self.average_entry_price = Decimal("0")
        self.daily_pnl = Decimal("0")
        self.total_trades = 0
        self.profitable_trades = 0

        logger.info(f"Micro Balance Grid DCA initialized:")
        logger.info(f"  Total Balance: ${self.total_balance}")
        logger.info(f"  Usable Balance: ${self.usable_balance}")
        logger.info(f"  Grid Levels: {self.grid_levels}")
        logger.info(f"  Order Size: ${self.order_size}")
        logger.info(f"  Grid Spacing: {self.grid_spacing * 100}%")

    async def initialize(self) -> bool:
        """Initialize the strategy."""
        try:
            logger.info("Initializing Micro Balance Grid DCA Strategy...")

            # Get current market price
            ticker = await self.data_manager.get_ticker(self.symbol)
            if not ticker:
                logger.error(f"Failed to get ticker for {self.symbol}")
                return False

            self.current_price = Decimal(str(ticker["last"]))
            logger.info(f"Current {self.symbol} price: ${self.current_price}")

            # Calculate grid levels
            await self._setup_initial_grid()

            self.is_initialized = True
            logger.info("Micro Balance Grid DCA Strategy initialized successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize strategy: {e}")
            return False

    async def _setup_initial_grid(self):
        """Setup the initial grid of buy orders."""
        try:
            grid_levels = []

            # Calculate buy levels below current price
            for i in range(self.grid_levels):
                level_distance = (i + 1) * self.grid_spacing
                buy_price = self.current_price * (1 - level_distance)

                grid_levels.append(
                    {
                        "level": i + 1,
                        "price": buy_price,
                        "size": self.order_size,
                        "type": "buy",
                        "filled": False,
                    }
                )

            self.grid_levels_data = grid_levels

            logger.info(f"Grid setup complete:")
            for level in grid_levels:
                logger.info(
                    f"  Level {level['level']}: Buy ${level['size']:.2f} at ${level['price']:.2f}"
                )

        except Exception as e:
            logger.error(f"Failed to setup grid: {e}")

    async def execute_strategy(
        self, market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute the micro balance strategy."""
        try:
            if not self.is_initialized:
                await self.initialize()

            signals = []
            current_price = Decimal(str(market_data.get("price", 0)))

            if current_price <= 0:
                return signals

            self.current_price = current_price

            # Check for grid buy opportunities
            buy_signals = await self._check_buy_opportunities(current_price)
            signals.extend(buy_signals)

            # Check for sell opportunities
            sell_signals = await self._check_sell_opportunities(current_price)
            signals.extend(sell_signals)

            # Check for DCA opportunities
            if self.dca_enabled:
                dca_signals = await self._check_dca_opportunities(current_price)
                signals.extend(dca_signals)

            return signals

        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            return []

    async def _check_buy_opportunities(
        self, current_price: Decimal
    ) -> List[Dict[str, Any]]:
        """Check for buy opportunities in the grid."""
        signals = []

        try:
            for level in self.grid_levels_data:
                if not level["filled"] and current_price <= level["price"]:
                    # Price hit our buy level
                    signal = {
                        "action": "buy",
                        "symbol": self.symbol,
                        "amount": float(level["size"]),
                        "price": float(level["price"]),
                        "type": "limit",
                        "reason": f'Grid buy level {level["level"]} triggered',
                        "level": level["level"],
                    }
                    signals.append(signal)
                    level["filled"] = True

                    logger.info(
                        f"🟢 BUY signal: ${level['size']:.2f} at ${level['price']:.2f}"
                    )

        except Exception as e:
            logger.error(f"Error checking buy opportunities: {e}")

        return signals

    async def _check_sell_opportunities(
        self, current_price: Decimal
    ) -> List[Dict[str, Any]]:
        """Check for sell opportunities."""
        signals = []

        try:
            if self.current_position > 0:
                # Calculate profit percentage
                profit_pct = (
                    current_price - self.average_entry_price
                ) / self.average_entry_price

                # Quick profit taking (0.8% gain)
                if profit_pct >= self.quick_profit:
                    sell_amount = self.current_position * Decimal("0.5")  # Sell half
                    signal = {
                        "action": "sell",
                        "symbol": self.symbol,
                        "amount": float(sell_amount),
                        "price": float(current_price),
                        "type": "market",
                        "reason": f"Quick profit at {profit_pct*100:.2f}%",
                    }
                    signals.append(signal)
                    logger.info(
                        f"🟡 SELL signal: Quick profit ${sell_amount:.4f} BTC at {profit_pct*100:.2f}%"
                    )

                # Full profit target (1.5% gain)
                elif profit_pct >= self.profit_target:
                    signal = {
                        "action": "sell",
                        "symbol": self.symbol,
                        "amount": float(self.current_position),
                        "price": float(current_price),
                        "type": "market",
                        "reason": f"Profit target reached at {profit_pct*100:.2f}%",
                    }
                    signals.append(signal)
                    logger.info(
                        f"🟢 SELL signal: Full position ${self.current_position:.4f} BTC at {profit_pct*100:.2f}%"
                    )

                # Stop loss (5% loss)
                elif profit_pct <= -self.stop_loss:
                    signal = {
                        "action": "sell",
                        "symbol": self.symbol,
                        "amount": float(self.current_position),
                        "price": float(current_price),
                        "type": "market",
                        "reason": f"Stop loss at {profit_pct*100:.2f}%",
                    }
                    signals.append(signal)
                    logger.warning(
                        f"🔴 STOP LOSS: Selling ${self.current_position:.4f} BTC at {profit_pct*100:.2f}%"
                    )

        except Exception as e:
            logger.error(f"Error checking sell opportunities: {e}")

        return signals

    async def _check_dca_opportunities(
        self, current_price: Decimal
    ) -> List[Dict[str, Any]]:
        """Check for DCA opportunities."""
        signals = []

        try:
            if self.current_position > 0 and len(self.dca_levels) < self.max_dca_levels:
                # Check if price dropped enough to trigger DCA
                price_drop = (
                    self.average_entry_price - current_price
                ) / self.average_entry_price

                if price_drop >= self.dca_trigger:
                    dca_amount = self.order_size * self.dca_multiplier

                    # Make sure we have enough balance
                    if dca_amount <= (self.total_balance - self.get_invested_amount()):
                        signal = {
                            "action": "buy",
                            "symbol": self.symbol,
                            "amount": float(dca_amount),
                            "price": float(current_price),
                            "type": "market",
                            "reason": f"DCA triggered at {price_drop*100:.2f}% drop",
                        }
                        signals.append(signal)
                        self.dca_levels.append(current_price)
                        logger.info(
                            f"📈 DCA signal: ${dca_amount:.2f} at ${current_price:.2f}"
                        )

        except Exception as e:
            logger.error(f"Error checking DCA opportunities: {e}")

        return signals

    def get_invested_amount(self) -> Decimal:
        """Calculate total amount currently invested."""
        return self.current_position * self.average_entry_price

    async def update_position(self, trade_data: Dict[str, Any]):
        """Update position after a trade."""
        try:
            action = trade_data.get("action")
            amount = Decimal(str(trade_data.get("amount", 0)))
            price = Decimal(str(trade_data.get("price", 0)))

            if action == "buy":
                # Update average entry price
                total_cost = (self.current_position * self.average_entry_price) + (
                    amount * price
                )
                self.current_position += amount
                self.average_entry_price = (
                    total_cost / self.current_position
                    if self.current_position > 0
                    else price
                )

            elif action == "sell":
                self.current_position -= amount
                if self.current_position <= 0:
                    self.current_position = Decimal("0")
                    self.average_entry_price = Decimal("0")

            self.total_trades += 1
            logger.info(
                f"Position updated: {self.current_position:.6f} BTC @ ${self.average_entry_price:.2f}"
            )

        except Exception as e:
            logger.error(f"Error updating position: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current strategy status."""
        return {
            "strategy": "Micro Balance Grid DCA",
            "symbol": self.symbol,
            "is_active": self.is_initialized,
            "current_position": float(self.current_position),
            "average_entry_price": float(self.average_entry_price),
            "total_balance": float(self.total_balance),
            "usable_balance": float(self.usable_balance),
            "grid_levels": self.grid_levels,
            "order_size": float(self.order_size),
            "total_trades": self.total_trades,
            "daily_pnl": float(self.daily_pnl),
            "grid_spacing": float(self.grid_spacing * 100),  # As percentage
            "profit_target": float(self.profit_target * 100),  # As percentage
            "stop_loss": float(self.stop_loss * 100),  # As percentage
        }
