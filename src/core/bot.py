"""
Main Trading Bot class that orchestrates all components.
This is the central coordinator for data, strategies, execution, and risk management.
"""

import asyncio
import logging
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .config import Config
from .exceptions import TradingBotError, ConfigurationError
from ..data.data_manager import DataManager
from ..data.websocket_client import WebSocketClient
from ..strategies.base_strategy import BaseStrategy
from ..strategies.ma_crossover import MovingAverageCrossover
from ..strategies.rsi_strategy import RSIStrategy
from ..strategies.strategy_manager import StrategyManager
from ..execution.order_manager import OrderManager
from ..execution.portfolio_manager import PortfolioManager
from ..risk.risk_manager import RiskManager
from ..notifications.notification_manager import NotificationManager
from ..backtesting.backtest_engine import BacktestEngine
from ..utils.logger import get_logger


@dataclass
class BotStatus:
    """Trading bot status information."""

    is_running: bool = False
    start_time: Optional[datetime] = None
    uptime: Optional[timedelta] = None
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    current_balance: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    max_drawdown: float = 0.0
    last_error: Optional[str] = None


class TradingBot:
    """
    Main trading bot class that coordinates all components.

    The bot manages:
    - Configuration and initialization
    - Data feeds and WebSocket connections
    - Strategy execution
    - Order management and portfolio tracking
    - Risk management
    - Notifications and logging
    """

    def __init__(self, config: Config):
        """
        Initialize the trading bot with configuration.

        Args:
            config: Configuration object with all bot settings
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.status = BotStatus()

        # Core components
        self.data_manager: Optional[DataManager] = None
        self.websocket_client: Optional[WebSocketClient] = None
        self.strategy: Optional[BaseStrategy] = None
        self.strategy_manager: Optional[StrategyManager] = None
        self.order_manager: Optional[OrderManager] = None
        self.portfolio_manager: Optional[PortfolioManager] = None
        self.risk_manager: Optional[RiskManager] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.backtest_engine: Optional[BacktestEngine] = None

        # Control flags
        self._shutdown_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all bot components."""
        try:
            self.logger.info("Initializing trading bot components...")

            # Initialize data manager
            self.data_manager = DataManager(self.config)

            # Initialize WebSocket client for real-time data
            if self.config.trading.mode in ["live", "paper"]:
                self.websocket_client = WebSocketClient(self.config)

            # Initialize strategy
            self.strategy = self._create_strategy()

            # Initialize strategy manager for Grid DCA and other advanced strategies
            # Get the primary exchange for the strategy manager
            primary_exchange = None
            if self.data_manager and self.data_manager.exchanges:
                # Get the configured exchange name
                exchange_name = self.config.trading.exchange
                if exchange_name in self.data_manager.exchanges:
                    primary_exchange = self.data_manager.exchanges[exchange_name]
                elif self.data_manager.exchanges:
                    # Fallback to first available exchange
                    primary_exchange = next(iter(self.data_manager.exchanges.values()))

            self.strategy_manager = StrategyManager(
                primary_exchange,
                self.data_manager.db_manager if self.data_manager else None,
            )

            # Initialize order manager
            self.order_manager = OrderManager(self.config)

            # Initialize portfolio manager
            self.portfolio_manager = PortfolioManager(self.config)

            # Initialize risk manager
            self.risk_manager = RiskManager(self.config)

            # Initialize notification manager
            self.notification_manager = NotificationManager(self.config)

            # Initialize backtest engine if needed
            if self.config.trading.mode == "backtest":
                self.backtest_engine = BacktestEngine(self.config)

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise ConfigurationError(f"Component initialization failed: {e}")

    def _create_strategy(self) -> BaseStrategy:
        """Create and initialize the trading strategy."""
        strategy_name = self.config.trading.strategy

        strategy_map = {
            "ma_crossover": MovingAverageCrossover,
            "rsi_strategy": RSIStrategy,
            "grid_dca": "strategy_manager",  # Special case for strategy manager
            # Add more strategies as they are implemented
        }

        if strategy_name not in strategy_map:
            raise ConfigurationError(f"Unknown strategy: {strategy_name}")

        strategy_class = strategy_map[strategy_name]
        strategy_config = getattr(self.config.strategies, strategy_name)

        return strategy_class(strategy_config, self.config)

    async def start(self):
        """Start the trading bot."""
        try:
            self.logger.info("Starting trading bot...")
            self.status.is_running = True
            self.status.start_time = datetime.now()

            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Send startup notification
            await self.notification_manager.send_notification(
                "Trading Bot Started",
                f"Bot started in {self.config.trading.mode} mode with {self.config.trading.strategy} strategy",
            )

            # Start all tasks
            await self._start_tasks()

            # Main bot loop
            await self._main_loop()

        except Exception as e:
            self.logger.error(f"Error starting bot: {e}", exc_info=True)
            self.status.last_error = str(e)
            await self.notification_manager.send_error_notification(
                "Bot Startup Error", f"Failed to start bot: {e}"
            )
            raise

    async def stop(self):
        """Stop the trading bot gracefully."""
        self.logger.info("Stopping trading bot...")
        self.status.is_running = False

        # Signal shutdown
        self._shutdown_event.set()

        # Cancel all running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close connections
        if self.websocket_client:
            await self.websocket_client.close()

        if self.order_manager:
            await self.order_manager.close()

        # Send shutdown notification
        await self.notification_manager.send_notification(
            "Trading Bot Stopped", "Bot has been stopped gracefully"
        )

        self.logger.info("Trading bot stopped successfully")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _start_tasks(self):
        """Start all background tasks."""
        self.logger.info("Starting background tasks...")

        # Initialize and start strategy manager if using Grid DCA
        if self.config.trading.strategy == "grid_dca" and self.strategy_manager:
            await self.strategy_manager.initialize()
            self._tasks.append(
                asyncio.create_task(self.strategy_manager.start_strategies())
            )

        # Data collection task
        if self.websocket_client:
            self._tasks.append(asyncio.create_task(self.websocket_client.start()))

        # Strategy execution task
        self._tasks.append(asyncio.create_task(self._strategy_task()))

        # Portfolio monitoring task
        self._tasks.append(asyncio.create_task(self._portfolio_monitoring_task()))

        # Risk monitoring task
        self._tasks.append(asyncio.create_task(self._risk_monitoring_task()))

        # Order management task
        self._tasks.append(asyncio.create_task(self._order_management_task()))

        # Health check task
        self._tasks.append(asyncio.create_task(self._health_check_task()))

        self.logger.info(f"Started {len(self._tasks)} background tasks")

    async def _main_loop(self):
        """Main bot event loop."""
        self.logger.info("Entering main bot loop...")

        try:
            while not self._shutdown_event.is_set():
                # Update bot status
                self._update_status()

                # Wait for shutdown signal or timeout
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(), timeout=60.0  # Check every minute
                    )
                    break
                except asyncio.TimeoutError:
                    # Continue loop
                    pass

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
            raise

    async def _strategy_task(self):
        """Background task for strategy execution."""
        self.logger.info("Starting strategy execution task...")

        while not self._shutdown_event.is_set():
            try:
                # Get latest market data
                market_data = await self.data_manager.get_latest_data(
                    self.config.trading.symbol, self.config.trading.timeframe
                )

                if market_data is not None:
                    # Generate trading signals
                    signals = await self.strategy.generate_signals(market_data)

                    # Process signals
                    for signal in signals:
                        await self._process_signal(signal)

                # Wait before next execution
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in strategy task: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer on error

    async def _process_signal(self, signal: Dict[str, Any]):
        """Process a trading signal from the strategy."""
        try:
            self.logger.info(f"Processing signal: {signal}")

            # Validate signal with risk manager
            if not await self.risk_manager.validate_signal(signal):
                self.logger.warning(f"Signal rejected by risk manager: {signal}")
                return

            # Calculate position size
            position_size = await self.risk_manager.calculate_position_size(
                signal, self.portfolio_manager.get_portfolio_value()
            )

            if position_size <= 0:
                self.logger.warning(f"Position size too small for signal: {signal}")
                return

            # Create and submit order
            order = await self.order_manager.create_order(
                symbol=signal["symbol"],
                side=signal["side"],
                amount=position_size,
                order_type=signal.get("order_type", "market"),
                price=signal.get("price"),
                stop_loss=signal.get("stop_loss"),
                take_profit=signal.get("take_profit"),
            )

            if order:
                self.status.total_trades += 1
                await self.notification_manager.send_trade_notification(
                    "Trade Signal",
                    f"Executed {signal['side']} order for {signal['symbol']}: {order}",
                )

        except Exception as e:
            self.logger.error(f"Error processing signal: {e}", exc_info=True)
            self.status.failed_trades += 1

    async def _portfolio_monitoring_task(self):
        """Background task for portfolio monitoring."""
        self.logger.info("Starting portfolio monitoring task...")

        while not self._shutdown_event.is_set():
            try:
                # Update portfolio
                await self.portfolio_manager.update_portfolio()

                # Update status
                portfolio = self.portfolio_manager.get_portfolio()
                self.status.current_balance = portfolio.get("total_value", 0.0)
                self.status.unrealized_pnl = portfolio.get("unrealized_pnl", 0.0)
                self.status.realized_pnl = portfolio.get("realized_pnl", 0.0)

                # Wait before next update
                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in portfolio monitoring: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _risk_monitoring_task(self):
        """Background task for risk monitoring."""
        self.logger.info("Starting risk monitoring task...")

        while not self._shutdown_event.is_set():
            try:
                # Check risk limits
                risk_status = await self.risk_manager.check_risk_limits()

                if risk_status.get("max_drawdown_exceeded"):
                    self.logger.warning("Maximum drawdown exceeded!")
                    await self.notification_manager.send_risk_notification(
                        "Risk Alert",
                        "Maximum drawdown exceeded. Consider stopping trading.",
                    )

                if risk_status.get("daily_loss_exceeded"):
                    self.logger.warning("Daily loss limit exceeded!")
                    # Optionally stop trading for the day

                # Update max drawdown
                self.status.max_drawdown = risk_status.get("current_drawdown", 0.0)

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in risk monitoring: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _order_management_task(self):
        """Background task for order management."""
        self.logger.info("Starting order management task...")

        while not self._shutdown_event.is_set():
            try:
                # Update order statuses
                await self.order_manager.update_orders()

                # Process filled orders
                filled_orders = await self.order_manager.get_filled_orders()
                for order in filled_orders:
                    await self._process_filled_order(order)

                # Wait before next update
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in order management: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _process_filled_order(self, order: Dict[str, Any]):
        """Process a filled order."""
        try:
            self.logger.info(f"Processing filled order: {order}")

            # Update portfolio
            await self.portfolio_manager.process_trade(order)

            # Update strategy
            await self.strategy.on_order_filled(order)

            # Send notification
            await self.notification_manager.send_trade_notification(
                "Order Filled",
                f"Order filled: {order['side']} {order['amount']} {order['symbol']} at {order['price']}",
            )

            self.status.successful_trades += 1

        except Exception as e:
            self.logger.error(f"Error processing filled order: {e}", exc_info=True)

    async def _health_check_task(self):
        """Background task for system health checks."""
        self.logger.info("Starting health check task...")

        while not self._shutdown_event.is_set():
            try:
                # Check WebSocket connection
                if self.websocket_client and not self.websocket_client.is_connected():
                    self.logger.warning(
                        "WebSocket disconnected, attempting reconnection..."
                    )
                    await self.websocket_client.reconnect()

                # Check exchange connectivity
                if not await self.order_manager.check_connectivity():
                    self.logger.warning("Exchange connectivity issues detected")

                # Memory and performance checks could be added here

                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in health check: {e}", exc_info=True)
                await asyncio.sleep(60)

    def _update_status(self):
        """Update bot status information."""
        if self.status.start_time:
            self.status.uptime = datetime.now() - self.status.start_time

    async def run_backtest(self):
        """Run backtesting mode."""
        if not self.backtest_engine:
            raise TradingBotError("Backtest engine not initialized")

        self.logger.info("Starting backtest...")

        try:
            # Run the backtest
            results = await self.backtest_engine.run_backtest(
                strategy=self.strategy,
                symbol=self.config.trading.symbol,
                timeframe=self.config.trading.timeframe,
            )

            # Generate and save report
            report = await self.backtest_engine.generate_report(results)

            self.logger.info("Backtest completed successfully")
            print("\n" + "=" * 50)
            print("BACKTEST RESULTS")
            print("=" * 50)
            print(report)

            return results

        except Exception as e:
            self.logger.error(f"Backtest failed: {e}", exc_info=True)
            raise

    def get_status(self) -> BotStatus:
        """Get current bot status."""
        self._update_status()
        return self.status

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if not self.portfolio_manager:
            return {}

        portfolio = self.portfolio_manager.get_portfolio()

        return {
            "total_trades": self.status.total_trades,
            "successful_trades": self.status.successful_trades,
            "failed_trades": self.status.failed_trades,
            "success_rate": (
                self.status.successful_trades / self.status.total_trades
                if self.status.total_trades > 0
                else 0
            ),
            "current_balance": self.status.current_balance,
            "unrealized_pnl": self.status.unrealized_pnl,
            "realized_pnl": self.status.realized_pnl,
            "max_drawdown": self.status.max_drawdown,
            "uptime": str(self.status.uptime) if self.status.uptime else "0:00:00",
        }
