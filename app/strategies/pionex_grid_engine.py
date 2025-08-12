"""
Pionex-Inspired Grid Trading Bot
Advanced Grid Strategy for Consistent Profits
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GridOrder:
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    price: float
    quantity: float
    grid_level: int
    status: str = "PENDING"  # 'PENDING', 'FILLED', 'CANCELLED'
    fill_time: Optional[datetime] = None


@dataclass
class GridBot:
    symbol: str
    lower_price: float
    upper_price: float
    grid_count: int
    investment_amount: float
    profit_per_grid: float = 0.01  # 1% profit per grid

    # Calculated fields
    grid_spacing: float = field(init=False)
    quantity_per_grid: float = field(init=False)
    grid_levels: List[float] = field(default_factory=list, init=False)
    buy_orders: Dict[int, GridOrder] = field(default_factory=dict, init=False)
    sell_orders: Dict[int, GridOrder] = field(default_factory=dict, init=False)

    # Statistics
    total_profit: float = 0.0
    completed_cycles: int = 0
    is_active: bool = False

    def __post_init__(self):
        self.grid_spacing = (self.upper_price - self.lower_price) / (
            self.grid_count - 1
        )
        self.quantity_per_grid = self.investment_amount / self.grid_count
        self.grid_levels = [
            self.lower_price + i * self.grid_spacing for i in range(self.grid_count)
        ]


class PionexGridEngine:
    """
    Pionex-inspired Grid Trading Engine
    Implements sophisticated grid trading with automatic rebalancing
    """

    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        self.grid_bots: Dict[str, GridBot] = {}
        self.is_running = False
        self.order_counter = 0

        # Performance tracking
        self.total_profit = 0.0
        self.total_fees_paid = 0.0
        self.active_grids = 0

        # Risk management
        self.max_capital_per_grid = 0.2  # 20% max capital per grid bot
        self.min_profit_threshold = 0.005  # 0.5% minimum profit per trade

    async def create_grid_bot(
        self,
        symbol: str,
        price_range_pct: float = 0.3,  # 30% price range
        grid_count: int = 20,
        investment_pct: float = 0.1,  # 10% of available capital
    ) -> GridBot:
        """
        Create a new grid bot for a symbol
        """
        try:
            # Get current market price
            current_price = await self.get_current_price(symbol)

            # Calculate price range
            range_amount = current_price * price_range_pct / 2
            lower_price = current_price - range_amount
            upper_price = current_price + range_amount

            # Calculate investment amount
            investment_amount = min(
                self.available_capital * investment_pct,
                self.available_capital * self.max_capital_per_grid,
            )

            # Create grid bot
            grid_bot = GridBot(
                symbol=symbol,
                lower_price=lower_price,
                upper_price=upper_price,
                grid_count=grid_count,
                investment_amount=investment_amount,
            )

            # Setup initial grid orders
            await self.setup_grid_orders(grid_bot, current_price)

            # Store grid bot
            self.grid_bots[symbol] = grid_bot
            self.available_capital -= investment_amount
            self.active_grids += 1

            logger.info(f"🔥 Grid Bot Created: {symbol}")
            logger.info(f"   Price Range: ${lower_price:.2f} - ${upper_price:.2f}")
            logger.info(f"   Grid Count: {grid_count}")
            logger.info(f"   Investment: ${investment_amount:.2f}")
            logger.info(f"   Expected Daily Return: 2-5%")

            return grid_bot

        except Exception as e:
            logger.error(f"❌ Failed to create grid bot for {symbol}: {e}")
            raise

    async def setup_grid_orders(self, grid_bot: GridBot, current_price: float):
        """
        Setup initial buy and sell orders for the grid
        """
        try:
            grid_bot.is_active = True

            # Place buy orders below current price
            for i, price in enumerate(grid_bot.grid_levels):
                if price < current_price:
                    # Create buy order
                    order = GridOrder(
                        order_id=self.generate_order_id(),
                        symbol=grid_bot.symbol,
                        side="BUY",
                        price=price,
                        quantity=grid_bot.quantity_per_grid / price,
                        grid_level=i,
                    )
                    grid_bot.buy_orders[i] = order
                    await self.place_grid_order(order)

                elif price > current_price:
                    # Create sell order (for existing positions)
                    order = GridOrder(
                        order_id=self.generate_order_id(),
                        symbol=grid_bot.symbol,
                        side="SELL",
                        price=price,
                        quantity=grid_bot.quantity_per_grid / price,
                        grid_level=i,
                    )
                    grid_bot.sell_orders[i] = order
                    # Note: Sell orders placed only if we have inventory

            logger.info(f"✅ Grid orders setup complete for {grid_bot.symbol}")

        except Exception as e:
            logger.error(f"❌ Grid setup failed for {grid_bot.symbol}: {e}")

    async def start_grid_trading(self, symbols: List[str]):
        """
        Start grid trading for multiple symbols
        """
        self.is_running = True
        logger.info("🚀 Starting Pionex-style Grid Trading Engine")

        # Create grid bots for each symbol
        for symbol in symbols:
            try:
                await self.create_grid_bot(symbol)
                await asyncio.sleep(1)  # Prevent rate limiting
            except Exception as e:
                logger.error(f"❌ Failed to create grid for {symbol}: {e}")

        # Start monitoring loop
        await self.run_grid_monitoring()

    async def run_grid_monitoring(self):
        """
        Main monitoring loop for all grid bots
        """
        logger.info("👀 Grid monitoring started")

        while self.is_running:
            try:
                # Monitor each grid bot
                for symbol, grid_bot in self.grid_bots.items():
                    if grid_bot.is_active:
                        await self.monitor_grid_bot(grid_bot)

                # Update performance statistics
                await self.update_performance_stats()

                # Check for rebalancing opportunities
                await self.check_rebalancing_opportunities()

                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"❌ Grid monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on errors

    async def monitor_grid_bot(self, grid_bot: GridBot):
        """
        Monitor and manage a single grid bot
        """
        try:
            current_price = await self.get_current_price(grid_bot.symbol)

            # Check for filled buy orders
            filled_buys = await self.check_filled_orders(
                grid_bot.buy_orders, current_price
            )

            # Check for filled sell orders
            filled_sells = await self.check_filled_orders(
                grid_bot.sell_orders, current_price
            )

            # Process filled orders
            for order in filled_buys + filled_sells:
                await self.process_filled_order(grid_bot, order, current_price)

            # Rebalance grid if price moved significantly
            await self.rebalance_grid_if_needed(grid_bot, current_price)

        except Exception as e:
            logger.error(f"❌ Grid monitoring error for {grid_bot.symbol}: {e}")

    async def check_filled_orders(
        self, orders: Dict[int, GridOrder], current_price: float
    ) -> List[GridOrder]:
        """
        Check which orders have been filled based on current price
        """
        filled_orders = []

        for level, order in orders.items():
            if order.status == "PENDING":
                # Simulate order execution based on price
                if (order.side == "BUY" and current_price <= order.price) or (
                    order.side == "SELL" and current_price >= order.price
                ):

                    order.status = "FILLED"
                    order.fill_time = datetime.now()
                    filled_orders.append(order)

                    logger.info(
                        f"✅ Order Filled: {order.side} {order.quantity:.4f} {order.symbol} at ${order.price:.2f}"
                    )

        return filled_orders

    async def process_filled_order(
        self, grid_bot: GridBot, order: GridOrder, current_price: float
    ):
        """
        Process a filled order and create the corresponding counter-order
        """
        try:
            if order.side == "BUY":
                # Buy order filled - create sell order at higher price
                sell_price = order.price * (1 + grid_bot.profit_per_grid)

                sell_order = GridOrder(
                    order_id=self.generate_order_id(),
                    symbol=grid_bot.symbol,
                    side="SELL",
                    price=sell_price,
                    quantity=order.quantity,
                    grid_level=order.grid_level,
                )

                grid_bot.sell_orders[order.grid_level] = sell_order
                await self.place_grid_order(sell_order)

                logger.info(
                    f"📈 Buy→Sell: {grid_bot.symbol} ${order.price:.2f}→${sell_price:.2f}"
                )

            elif order.side == "SELL":
                # Sell order filled - calculate profit and create new buy order
                corresponding_buy = None
                for buy_order in grid_bot.buy_orders.values():
                    if (
                        buy_order.grid_level == order.grid_level
                        and buy_order.status == "FILLED"
                    ):
                        corresponding_buy = buy_order
                        break

                if corresponding_buy:
                    # Calculate profit
                    profit = (order.price - corresponding_buy.price) * order.quantity
                    grid_bot.total_profit += profit
                    grid_bot.completed_cycles += 1
                    self.total_profit += profit

                    logger.info(f"💰 Grid Profit: ${profit:.2f} from {grid_bot.symbol}")

                    # Create new buy order at the same level
                    new_buy_order = GridOrder(
                        order_id=self.generate_order_id(),
                        symbol=grid_bot.symbol,
                        side="BUY",
                        price=corresponding_buy.price,
                        quantity=corresponding_buy.quantity,
                        grid_level=order.grid_level,
                    )

                    grid_bot.buy_orders[order.grid_level] = new_buy_order
                    await self.place_grid_order(new_buy_order)

                    logger.info(
                        f"🔄 Cycle Complete: {grid_bot.symbol} - Total Cycles: {grid_bot.completed_cycles}"
                    )

        except Exception as e:
            logger.error(f"❌ Order processing error: {e}")

    async def rebalance_grid_if_needed(self, grid_bot: GridBot, current_price: float):
        """
        Rebalance grid if price moves outside the range
        """
        try:
            if (
                current_price < grid_bot.lower_price
                or current_price > grid_bot.upper_price
            ):
                logger.info(
                    f"🔄 Rebalancing grid for {grid_bot.symbol} - Price: ${current_price:.2f}"
                )

                # Cancel existing orders
                await self.cancel_all_orders(grid_bot)

                # Recalculate price range
                range_amount = current_price * 0.15  # 15% range
                grid_bot.lower_price = current_price - range_amount
                grid_bot.upper_price = current_price + range_amount
                grid_bot.grid_spacing = (
                    grid_bot.upper_price - grid_bot.lower_price
                ) / (grid_bot.grid_count - 1)
                grid_bot.grid_levels = [
                    grid_bot.lower_price + i * grid_bot.grid_spacing
                    for i in range(grid_bot.grid_count)
                ]

                # Setup new grid orders
                await self.setup_grid_orders(grid_bot, current_price)

                logger.info(f"✅ Grid rebalanced for {grid_bot.symbol}")

        except Exception as e:
            logger.error(f"❌ Grid rebalancing error for {grid_bot.symbol}: {e}")

    async def check_rebalancing_opportunities(self):
        """
        Check for opportunities to optimize existing grids
        """
        try:
            for symbol, grid_bot in self.grid_bots.items():
                # Check if grid is making enough profit
                if grid_bot.completed_cycles > 0:
                    avg_profit_per_cycle = (
                        grid_bot.total_profit / grid_bot.completed_cycles
                    )
                    expected_min_profit = (
                        grid_bot.investment_amount * 0.001
                    )  # 0.1% minimum

                    if avg_profit_per_cycle < expected_min_profit:
                        logger.info(f"⚡ Optimizing low-performing grid: {symbol}")
                        await self.optimize_grid_parameters(grid_bot)

        except Exception as e:
            logger.error(f"❌ Rebalancing check error: {e}")

    async def optimize_grid_parameters(self, grid_bot: GridBot):
        """
        Optimize grid parameters for better performance
        """
        try:
            # Analyze recent volatility
            volatility = await self.calculate_volatility(grid_bot.symbol)

            # Adjust grid spacing based on volatility
            if volatility > 0.03:  # High volatility
                grid_bot.grid_count = min(30, grid_bot.grid_count + 5)
                grid_bot.profit_per_grid = 0.005  # 0.5% profit per grid
            else:  # Low volatility
                grid_bot.grid_count = max(10, grid_bot.grid_count - 5)
                grid_bot.profit_per_grid = 0.015  # 1.5% profit per grid

            # Recalculate grid
            current_price = await self.get_current_price(grid_bot.symbol)
            await self.cancel_all_orders(grid_bot)
            await self.setup_grid_orders(grid_bot, current_price)

            logger.info(f"✅ Grid optimized for {grid_bot.symbol}")

        except Exception as e:
            logger.error(f"❌ Grid optimization error: {e}")

    async def get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            return float(data["Close"].iloc[-1])
        except Exception as e:
            logger.error(f"❌ Price fetch error for {symbol}: {e}")
            return 0.0

    async def calculate_volatility(self, symbol: str) -> float:
        """Calculate recent volatility"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="7d")
            returns = data["Close"].pct_change().dropna()
            return float(returns.std())
        except Exception as e:
            logger.error(f"❌ Volatility calculation error: {e}")
            return 0.02

    async def place_grid_order(self, order: GridOrder):
        """Place grid order (integration point for real broker)"""
        # This would integrate with actual broker API
        logger.debug(
            f"📝 Grid Order: {order.side} {order.quantity:.4f} {order.symbol} at ${order.price:.2f}"
        )

    async def cancel_all_orders(self, grid_bot: GridBot):
        """Cancel all pending orders for a grid bot"""
        try:
            for order in list(grid_bot.buy_orders.values()) + list(
                grid_bot.sell_orders.values()
            ):
                if order.status == "PENDING":
                    order.status = "CANCELLED"

            grid_bot.buy_orders.clear()
            grid_bot.sell_orders.clear()

        except Exception as e:
            logger.error(f"❌ Order cancellation error: {e}")

    def generate_order_id(self) -> str:
        """Generate unique order ID"""
        self.order_counter += 1
        return f"GRID_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.order_counter}"

    async def update_performance_stats(self):
        """Update overall performance statistics"""
        try:
            total_investment = sum(
                bot.investment_amount for bot in self.grid_bots.values()
            )
            total_profit = sum(bot.total_profit for bot in self.grid_bots.values())

            if total_investment > 0:
                roi_pct = (total_profit / total_investment) * 100

                # Log performance every 10 minutes
                if datetime.now().minute % 10 == 0:
                    logger.info(f"📊 Performance Update:")
                    logger.info(f"   Total Investment: ${total_investment:.2f}")
                    logger.info(f"   Total Profit: ${total_profit:.2f}")
                    logger.info(f"   ROI: {roi_pct:.2f}%")
                    logger.info(f"   Active Grids: {len(self.grid_bots)}")

        except Exception as e:
            logger.error(f"❌ Performance update error: {e}")

    def get_grid_statistics(self) -> Dict:
        """Get comprehensive grid trading statistics"""
        total_investment = sum(bot.investment_amount for bot in self.grid_bots.values())
        total_profit = sum(bot.total_profit for bot in self.grid_bots.values())
        total_cycles = sum(bot.completed_cycles for bot in self.grid_bots.values())

        return {
            "total_investment": total_investment,
            "total_profit": total_profit,
            "roi_percentage": (total_profit / max(total_investment, 1)) * 100,
            "active_grids": len(self.grid_bots),
            "total_cycles": total_cycles,
            "average_profit_per_cycle": total_profit / max(total_cycles, 1),
            "daily_profit_target": total_investment * 0.03,  # 3% daily target
            "grid_bots": {
                symbol: {
                    "profit": bot.total_profit,
                    "cycles": bot.completed_cycles,
                    "investment": bot.investment_amount,
                    "roi": (bot.total_profit / bot.investment_amount) * 100,
                }
                for symbol, bot in self.grid_bots.items()
            },
        }

    def stop_all_grids(self):
        """Stop all grid trading"""
        self.is_running = False
        for grid_bot in self.grid_bots.values():
            grid_bot.is_active = False
        logger.info("🛑 All grid trading stopped")


# Example usage
async def main():
    """Example of how to use the Pionex-style grid engine"""
    engine = PionexGridEngine(initial_capital=10000)

    # Popular trading pairs
    symbols = ["AAPL", "TSLA", "MSFT", "NVDA", "BTC-USD", "ETH-USD"]

    # Start grid trading
    await engine.start_grid_trading(symbols)


if __name__ == "__main__":
    asyncio.run(main())
