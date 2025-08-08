"""
Universal Grid DCA Strategy for Paper Trading
Implements a grid trading strategy with DCA (Dollar Cost Averaging)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .base_strategy import BaseStrategy
from ..data.data_manager import DataManager
from ..execution.order_manager import OrderManager
from ..risk.risk_manager import RiskManager


class UniversalGridDCAStrategy(BaseStrategy):
    """
    Universal Grid DCA (Dollar Cost Averaging) Strategy

    This strategy places buy and sell orders at predetermined price levels
    forming a "grid" around the current market price. When orders are filled,
    new orders are placed to maintain the grid structure.
    """

    def __init__(
        self,
        symbol: str,
        grid_levels: int = 5,
        grid_spacing: float = 0.02,  # 2% spacing between levels
        order_size: float = 100.0,  # Base order size in quote currency
        **kwargs,
    ):
        super().__init__(symbol, **kwargs)

        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing
        self.order_size = order_size

        # Grid tracking
        self.active_grid_orders: Dict[str, Dict] = {}
        self.grid_center_price: Optional[float] = None
        self.last_grid_update: Optional[datetime] = None

        # Performance tracking
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0

        self.logger = logging.getLogger(f"{__name__}.{symbol}")

    async def initialize(self):
        """Initialize the strategy"""
        await super().initialize()
        self.logger.info(f"Initializing Universal Grid DCA Strategy for {self.symbol}")
        self.logger.info(
            f"Grid levels: {self.grid_levels}, Spacing: {self.grid_spacing:.1%}"
        )

    async def cleanup(self):
        """Clean up strategy resources"""
        await self.cancel_all_grid_orders()
        await super().cleanup()

    async def process_market_data(self, data: Dict[str, Any]):
        """Process incoming market data"""
        if not self.is_active:
            return

        try:
            current_price = float(data.get("price", 0))
            if current_price <= 0:
                return

            # Update grid if needed
            if self._should_update_grid(current_price):
                await self._update_grid(current_price)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")

    def _should_update_grid(self, current_price: float) -> bool:
        """Determine if grid needs updating"""
        if self.grid_center_price is None:
            return True

        # Update if price moved significantly from grid center
        price_deviation = (
            abs(current_price - self.grid_center_price) / self.grid_center_price
        )
        return price_deviation > self.grid_spacing * 2

    async def _update_grid(self, current_price: float):
        """Update the trading grid"""
        try:
            # Cancel existing grid orders
            await self.cancel_all_grid_orders()

            # Set new grid center
            self.grid_center_price = current_price
            self.last_grid_update = datetime.now()

            # Create new grid orders
            await self._create_grid_orders(current_price)

            self.logger.info(f"Grid updated with center price: ${current_price:.4f}")

        except Exception as e:
            self.logger.error(f"Error updating grid: {e}")

    async def _create_grid_orders(self, center_price: float):
        """Create buy and sell orders for the grid"""
        orders_to_place = []

        # Create buy orders below center price
        for level in range(1, self.grid_levels + 1):
            buy_price = center_price * (1 - self.grid_spacing * level)
            quantity = self.order_size / buy_price

            orders_to_place.append(
                {
                    "side": "buy",
                    "price": buy_price,
                    "quantity": quantity,
                    "level": -level,  # Negative for buy levels
                }
            )

        # Create sell orders above center price
        for level in range(1, self.grid_levels + 1):
            sell_price = center_price * (1 + self.grid_spacing * level)
            quantity = self.order_size / center_price  # Base quantity on center price

            orders_to_place.append(
                {
                    "side": "sell",
                    "price": sell_price,
                    "quantity": quantity,
                    "level": level,  # Positive for sell levels
                }
            )

        # Place all orders
        for order_info in orders_to_place:
            try:
                order_id = await self._place_grid_order(order_info)
                if order_id:
                    self.active_grid_orders[order_id] = order_info

            except Exception as e:
                self.logger.error(f"Error placing grid order: {e}")

    async def _place_grid_order(self, order_info: Dict) -> Optional[str]:
        """Place a single grid order"""
        try:
            # This would integrate with the order manager
            # For now, return a mock order ID
            order_id = f"grid_{order_info['side']}_{order_info['level']}_{datetime.now().timestamp()}"

            self.logger.debug(
                f"Placed {order_info['side']} order: "
                f"{order_info['quantity']:.4f} @ ${order_info['price']:.4f} "
                f"(Level: {order_info['level']})"
            )

            return order_id

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None

    async def cancel_all_grid_orders(self):
        """Cancel all active grid orders"""
        for order_id in list(self.active_grid_orders.keys()):
            try:
                # This would integrate with order manager to cancel
                self.logger.debug(f"Cancelled grid order: {order_id}")
                del self.active_grid_orders[order_id]

            except Exception as e:
                self.logger.error(f"Error cancelling order {order_id}: {e}")

    async def on_order_filled(self, order_id: str, fill_data: Dict[str, Any]):
        """Handle order fill events"""
        if order_id not in self.active_grid_orders:
            return

        try:
            order_info = self.active_grid_orders.pop(order_id)
            fill_price = float(fill_data.get("price", 0))
            fill_quantity = float(fill_data.get("quantity", 0))

            self.total_trades += 1

            # Log the fill
            self.logger.info(
                f"Grid order filled: {order_info['side']} "
                f"{fill_quantity:.4f} @ ${fill_price:.4f} "
                f"(Level: {order_info['level']})"
            )

            # Place replacement order on opposite side
            await self._place_replacement_order(order_info, fill_price)

        except Exception as e:
            self.logger.error(f"Error handling order fill: {e}")

    async def _place_replacement_order(self, filled_order: Dict, fill_price: float):
        """Place a replacement order after one is filled"""
        try:
            if filled_order["side"] == "buy":
                # Buy order filled, place sell order above
                new_price = fill_price * (1 + self.grid_spacing)
                new_side = "sell"
                new_level = abs(filled_order["level"])
            else:
                # Sell order filled, place buy order below
                new_price = fill_price * (1 - self.grid_spacing)
                new_side = "buy"
                new_level = -abs(filled_order["level"])

            new_order_info = {
                "side": new_side,
                "price": new_price,
                "quantity": filled_order["quantity"],
                "level": new_level,
            }

            order_id = await self._place_grid_order(new_order_info)
            if order_id:
                self.active_grid_orders[order_id] = new_order_info

        except Exception as e:
            self.logger.error(f"Error placing replacement order: {e}")

    def get_strategy_state(self) -> Dict[str, Any]:
        """Get current strategy state"""
        base_state = super().get_strategy_state()

        grid_state = {
            "grid_center_price": self.grid_center_price,
            "active_orders": len(self.active_grid_orders),
            "grid_levels": self.grid_levels,
            "grid_spacing": self.grid_spacing,
            "total_trades": self.total_trades,
            "profitable_trades": self.profitable_trades,
            "win_rate": self.profitable_trades / max(1, self.total_trades),
            "total_profit": self.total_profit,
            "last_grid_update": (
                self.last_grid_update.isoformat() if self.last_grid_update else None
            ),
        }

        return {**base_state, **grid_state}


class StrategyManager:
    """
    Strategy Manager for coordinating multiple strategies
    """

    def __init__(self, initial_balance: float = 1000.0):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.strategies: Dict[str, BaseStrategy] = {}
        self.is_running = False

        self.logger = logging.getLogger(__name__)

    def add_strategy(self, name: str, strategy: BaseStrategy):
        """Add a strategy to the manager"""
        self.strategies[name] = strategy
        self.logger.info(f"Added strategy: {name}")

    def remove_strategy(self, name: str):
        """Remove a strategy from the manager"""
        if name in self.strategies:
            del self.strategies[name]
            self.logger.info(f"Removed strategy: {name}")

    async def start_all(self):
        """Start all managed strategies"""
        self.is_running = True
        for name, strategy in self.strategies.items():
            try:
                await strategy.start()
                self.logger.info(f"Started strategy: {name}")
            except Exception as e:
                self.logger.error(f"Error starting strategy {name}: {e}")

    async def stop_all(self):
        """Stop all managed strategies"""
        self.is_running = False
        for name, strategy in self.strategies.items():
            try:
                await strategy.stop()
                self.logger.info(f"Stopped strategy: {name}")
            except Exception as e:
                self.logger.error(f"Error stopping strategy {name}: {e}")

    def get_total_balance(self) -> float:
        """Get total balance across all strategies"""
        return self.current_balance

    def get_status(self) -> Dict[str, Any]:
        """Get status of all strategies"""
        return {
            "is_running": self.is_running,
            "total_balance": self.current_balance,
            "initial_balance": self.initial_balance,
            "profit_loss": self.current_balance - self.initial_balance,
            "strategies": {
                name: strategy.get_strategy_state()
                for name, strategy in self.strategies.items()
            },
        }
