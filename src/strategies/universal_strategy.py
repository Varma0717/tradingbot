"""
Universal Grid DCA Strategy for Paper Trading
Implements a grid trading strategy with DCA (Dollar Cost Averaging)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

from .base_strategy import BaseStrategy, TradeSignal
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
        strategy_config: Optional[Dict[str, Any]] = None,
        config=None,
        **kwargs,
    ):
        # Create a default config if none provided
        if strategy_config is None:
            strategy_config = {
                "symbol": symbol,
                "grid_levels": grid_levels,
                "grid_spacing": grid_spacing,
                "order_size": order_size,
            }

        # Import Config class if config not provided
        if config is None:
            from ..core.config import Config

            config = Config()

        super().__init__(strategy_config, config)

        self.symbol = symbol
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

        # Strategy state
        self.is_active = False

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

    async def start(self):
        """Start the strategy"""
        if self.is_active:
            self.logger.warning(
                f"Strategy {self.name} is already active, skipping start"
            )
            return

        self.is_active = True
        self.logger.info(f"Started {self.name} for {self.symbol}")

        # Initialize grid with a default price if no current price available
        if self.grid_center_price is None:
            # Use a default BTC price for simulation
            default_price = 43000.0 if self.symbol == "BTCUSDT" else 1.0
            await self._update_grid(default_price)

    async def stop(self):
        """Stop the strategy"""
        self.is_active = False
        await self.cancel_all_grid_orders()
        self.logger.info(f"Stopped {self.name} for {self.symbol}")

    @property
    def name(self) -> str:
        """Get strategy name"""
        return "Universal Grid DCA Strategy"

    @property
    def description(self) -> str:
        """Get strategy description"""
        return (
            "A grid trading strategy with Dollar Cost Averaging (DCA) that places "
            "buy and sell orders at predetermined price levels forming a grid around "
            "the current market price. Automatically manages order placement and replacement."
        )

    @property
    def required_indicators(self) -> List[str]:
        """Get required technical indicators"""
        return []  # Grid strategy doesn't require specific indicators

    async def generate_signals(self, market_data: pd.DataFrame) -> List[TradeSignal]:
        """Generate trading signals based on market data"""
        signals = []

        if market_data.empty:
            return signals

        try:
            current_price = float(market_data.iloc[-1]["close"])

            # Generate signals based on grid logic
            if self._should_update_grid(current_price):
                # Signal to update grid - this is more of an internal operation
                # but we can generate signals for monitoring
                signals.append(
                    TradeSignal(
                        symbol=self.symbol,
                        side="buy",  # Placeholder - actual grid management is in process_market_data
                        strength=0.5,
                        price=current_price,
                        reason="Grid update needed",
                        metadata={
                            "grid_center": self.grid_center_price,
                            "current_price": current_price,
                        },
                    )
                )
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")

        return signals

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
        # Base state information
        base_state = {
            "symbol": self.symbol,
            "is_active": getattr(self, "is_active", False),
            "timestamp": datetime.now().isoformat(),
        }

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

    def __init__(self, exchange=None, db_manager=None, initial_balance: float = 1000.0):
        # Handle both new signature (exchange, db_manager) and old signature (initial_balance)
        if isinstance(exchange, (int, float)) and db_manager is None:
            # Old signature: StrategyManager(initial_balance)
            initial_balance = exchange
            exchange = None
            db_manager = None

        self.exchange = exchange
        self.db_manager = db_manager
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.strategies: Dict[str, BaseStrategy] = {}
        self.is_running = False

        self.logger = logging.getLogger(__name__)

        # Initialize paper trading simulator for paper mode
        self.paper_simulator = None
        try:
            from ..simulation.paper_trading_simulator import PaperTradingSimulator

            self.paper_simulator = PaperTradingSimulator(self)
            self.logger.info("Paper trading simulator initialized")
        except Exception as e:
            self.logger.warning(f"Could not initialize paper trading simulator: {e}")

        # Create optimized default strategy
        try:
            self.default_strategy = UniversalGridDCAStrategy(
                symbol="BTCUSDT",  # Default symbol
                grid_levels=8,  # More levels for better coverage
                grid_spacing=0.015,  # Tighter spacing (1.5%) for more frequent trades
                order_size=min(
                    175.0, initial_balance * 0.12
                ),  # 12% of balance per order, max $175
            )
            self.add_strategy("default_grid_dca", self.default_strategy)
        except Exception as e:
            self.logger.error(f"Error creating default strategy: {e}")

    async def initialize(self):
        """Initialize the strategy manager asynchronously"""
        try:
            for strategy in self.strategies.values():
                if hasattr(strategy, "initialize"):
                    await strategy.initialize()
            self.logger.info("Strategy manager initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing strategy manager: {e}")
            raise

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

        # Start paper trading simulator if available
        if self.paper_simulator:
            self.paper_simulator.start_simulation()

        for name, strategy in self.strategies.items():
            try:
                if hasattr(strategy, "start"):
                    await strategy.start()
                else:
                    # Fallback: set strategy as active
                    strategy.is_active = True
                self.logger.info(f"Started strategy: {name}")
            except Exception as e:
                self.logger.error(f"Error starting strategy {name}: {e}")

    async def stop_all(self):
        """Stop all managed strategies"""
        self.is_running = False

        # Stop paper trading simulator if available
        if self.paper_simulator:
            self.paper_simulator.stop_simulation()

        for name, strategy in self.strategies.items():
            try:
                if hasattr(strategy, "stop"):
                    await strategy.stop()
                else:
                    # Fallback: set strategy as inactive
                    strategy.is_active = False
                self.logger.info(f"Stopped strategy: {name}")
            except Exception as e:
                self.logger.error(f"Error stopping strategy {name}: {e}")

    def get_total_balance(self) -> float:
        """Get total balance across all strategies"""
        return self.current_balance

    def get_trades(self) -> List[Dict]:
        """Get trades from paper trading simulator"""
        if self.paper_simulator and hasattr(self.paper_simulator, "mock_trades"):
            return self.paper_simulator.mock_trades
        return []

    def get_active_orders(self) -> List[Dict]:
        """Get active orders from paper trading simulator"""
        if self.paper_simulator and hasattr(self.paper_simulator, "mock_orders"):
            return self.paper_simulator.mock_orders
        return []

    def get_status(self) -> Dict[str, Any]:
        """Get status of all strategies"""
        return {
            "is_running": self.is_running,
            "status": "active" if self.is_running else "stopped",
            "total_balance": self.current_balance,
            "balance": self.current_balance,
            "initial_balance": self.initial_balance,
            "profit_loss": self.current_balance - self.initial_balance,
            "strategies": {
                name: strategy.get_strategy_state()
                for name, strategy in self.strategies.items()
            },
        }

    def start_trading(self) -> bool:
        """Start trading (synchronous wrapper)"""
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a task if we're already in an event loop
                asyncio.create_task(self.start_all())
            else:
                # Run the coroutine if no loop is running
                loop.run_until_complete(self.start_all())
            return True
        except Exception as e:
            self.logger.error(f"Error starting trading: {e}")
            return False

    def stop_trading(self) -> bool:
        """Stop trading (synchronous wrapper)"""
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a task if we're already in an event loop
                asyncio.create_task(self.stop_all())
            else:
                # Run the coroutine if no loop is running
                loop.run_until_complete(self.stop_all())
            return True
        except Exception as e:
            self.logger.error(f"Error stopping trading: {e}")
            return False

    def get_trades(self) -> List[Dict[str, Any]]:
        """Get all trades from all strategies"""
        # Return simulated trades if paper trading simulator is available
        if self.paper_simulator:
            return self.paper_simulator.get_trades()

        # Fallback to strategy trade history
        all_trades = []
        for strategy in self.strategies.values():
            if hasattr(strategy, "trade_history"):
                all_trades.extend(strategy.trade_history)
        return all_trades

    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active orders from all strategies"""
        # Return simulated orders if paper trading simulator is available
        if self.paper_simulator:
            return self.paper_simulator.get_orders()

        # Fallback to strategy active orders
        all_orders = []
        for strategy in self.strategies.values():
            if hasattr(strategy, "active_grid_orders"):
                for order_id, order_data in strategy.active_grid_orders.items():
                    all_orders.append(
                        {
                            "id": order_id,
                            "strategy": strategy.symbol,
                            "type": order_data.get("side", "unknown"),
                            "amount": order_data.get("amount", 0),
                            "price": order_data.get("price", 0),
                            "created": order_data.get(
                                "created_at", datetime.now().isoformat()
                            ),
                        }
                    )
        return all_orders

    def update_simulation(self):
        """Update simulation state (for paper trading)"""
        if self.paper_simulator:
            self.paper_simulator.update_simulation()
