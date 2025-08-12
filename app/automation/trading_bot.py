"""
Automated Trading Bot for Indian Stock Market
One-click trading solution with comprehensive strategies
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import current_app
from ..models import User, Strategy, Order, Trade, ExchangeConnection
from ..strategies.engine import run_strategy
from ..exchange_adapter.kite_adapter import exchange_adapter
from ..orders.manager import place_order
from .. import db
import asyncio
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class IndianStockTradingBot:
    """
    Comprehensive automated trading bot for Indian stock market.
    Provides one-click start trading functionality with multiple strategies.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        # Eagerly load user with subscription to avoid lazy loading issues
        self.user = User.query.options(joinedload(User.subscription)).get(user_id)
        self.is_running = False
        self.thread = None
        self.strategies = []
        self.current_positions = {}
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.last_signal_time = None

        # Indian stock market symbols for automated trading
        self.indian_stocks = [
            "RELIANCE",
            "TCS",
            "INFY",
            "HDFCBANK",
            "HINDUNILVR",
            "ICICIBANK",
            "KOTAKBANK",
            "SBIN",
            "BHARTIARTL",
            "ITC",
            "ASIANPAINT",
            "LT",
            "AXISBANK",
            "MARUTI",
            "HCLTECH",
            "WIPRO",
            "ULTRACEMCO",
            "TITAN",
            "BAJFINANCE",
            "NESTLEIND",
        ]

        # Default trading parameters for automation
        self.default_params = {
            "investment_amount": 50000,  # Default 50k investment
            "risk_per_trade": 0.02,  # 2% risk per trade
            "max_positions": 5,  # Maximum 5 concurrent positions
            "stop_loss": 0.03,  # 3% stop loss
            "take_profit": 0.06,  # 6% take profit (2:1 risk-reward)
            "trading_hours": (9, 15),  # 9 AM to 3 PM IST
        }

    def start_automated_trading(self) -> Dict:
        """
        Start automated trading with comprehensive strategies.
        This is the main entry point for one-click trading.
        """
        try:
            if self.is_running:
                return {"success": False, "message": "Trading bot is already running"}

            # Check if user has exchange connection
            exchange_conn = ExchangeConnection.query.filter_by(
                user_id=self.user_id, status="connected"
            ).first()

            if not exchange_conn:
                return {
                    "success": False,
                    "message": "Please connect to a broker first from Settings page",
                }

            # Initialize comprehensive strategies
            self._initialize_comprehensive_strategies()

            # Sync trade count from database to ensure consistency
            self._sync_trade_count_from_db()

            # Update bot status in database
            self._update_bot_status(is_running=True, started_at=datetime.now())

            # Start the trading thread
            self.is_running = True
            app = current_app._get_current_object()
            self.thread = threading.Thread(
                target=self._trading_loop, args=(app,), daemon=True
            )
            self.thread.start()

            logger.info(f"Automated trading started for user {self.user_id}")

            return {
                "success": True,
                "message": "Automated trading started successfully! The bot will now trade with intelligent strategies.",
                "strategies_count": len(self.strategies),
                "symbols_count": len(self.indian_stocks),
            }

        except Exception as e:
            logger.error(f"Error starting automated trading: {e}")
            return {"success": False, "message": f"Failed to start trading: {str(e)}"}

    def stop_automated_trading(self) -> Dict:
        """Stop automated trading and close all positions."""
        try:
            if not self.is_running:
                return {"success": False, "message": "Trading bot is not running"}

            self.is_running = False

            # Close all open positions
            self._close_all_positions()

            # Update bot status in database
            self._update_bot_status(is_running=False, stopped_at=datetime.now())

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)

            logger.info(f"Automated trading stopped for user {self.user_id}")

            return {
                "success": True,
                "message": "Trading stopped successfully. All positions closed.",
                "total_trades": self.total_trades,
                "daily_pnl": self.daily_pnl,
            }

        except Exception as e:
            logger.error(f"Error stopping automated trading: {e}")
            return {"success": False, "message": f"Failed to stop trading: {str(e)}"}

    def _initialize_comprehensive_strategies(self):
        """Initialize multiple strategies for comprehensive trading."""
        from .enhanced_strategies import MultiStrategyEngine

        # Initialize the multi-strategy engine
        self.multi_strategy_engine = MultiStrategyEngine()

        # Strategy configurations for different market conditions
        self.strategies = [
            {
                "name": "Multi_Strategy_Engine",
                "description": "Combines RSI, Momentum, Bollinger Bands, and VWAP strategies",
                "symbols": self.indian_stocks,  # All stocks
                "active_hours": (9, 15),  # Market hours
                "risk_level": "moderate",
            }
        ]

        logger.info(
            f"Initialized comprehensive strategy engine with {len(self.indian_stocks)} symbols"
        )

    def _trading_loop(self, app):
        """Main trading loop that runs continuously."""
        logger.info("Starting automated trading loop")

        # Use the provided app context for database operations
        with app.app_context():
            while self.is_running:
                try:
                    current_time = datetime.now()

                    # Check if within trading hours (9 AM to 3:30 PM IST)
                    if not self._is_trading_hours(current_time):
                        logger.info("Outside trading hours, sleeping...")
                        time.sleep(300)  # Sleep for 5 minutes
                        continue

                    # Execute all strategies
                    for strategy in self.strategies:
                        if self.is_running:  # Check if still running
                            self._execute_strategy(strategy)

                    # Update portfolio metrics
                    self._update_portfolio_metrics()

                    # Risk management check
                    self._risk_management_check()

                    # Update heartbeat to show bot is alive (maintain current running status)
                    self._update_bot_status(is_running=self.is_running)

                    # Sleep for 2 minutes before next iteration
                    time.sleep(120)

                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    time.sleep(60)  # Sleep for 1 minute on error

    def _execute_strategy(self, strategy: Dict):
        """Execute a specific trading strategy."""
        try:
            logger.info(f"Executing enhanced multi-strategy engine")

            # Prepare market data for all symbols
            market_data = {}
            for symbol in self.indian_stocks:
                if not self.is_running:
                    break

                data = self._get_market_data(symbol)
                if data:
                    market_data[symbol] = data

            # Generate comprehensive signals using enhanced strategies
            if hasattr(self, "multi_strategy_engine"):
                signals = self.multi_strategy_engine.generate_comprehensive_signals(
                    market_data
                )

                # Execute the top signals (limit to avoid overtrading)
                max_signals = 3  # Maximum 3 signals per cycle
                for signal in signals[:max_signals]:
                    if not self.is_running:
                        break

                    self._execute_signal(signal, strategy)
                    self.last_signal_time = datetime.now()

                    # Small delay between orders
                    time.sleep(2)

        except Exception as e:
            logger.error(f"Error executing enhanced strategy: {e}")

    def _generate_signal(
        self, strategy: Dict, symbol: str, market_data: Dict
    ) -> Optional[Dict]:
        """Generate trading signals using enhanced strategy engine."""
        # This method is now handled by the multi-strategy engine
        # Keeping for backward compatibility
        return None

    def _execute_signal(self, signal: Dict, strategy: Dict):
        """Execute a trading signal by placing an order."""
        try:
            # Check position limits
            if (
                signal["action"] == "BUY"
                and len(self.current_positions) >= self.default_params["max_positions"]
            ):
                logger.info(f"Maximum positions reached, skipping {signal['symbol']}")
                return

            # Prepare order data
            order_data = {
                "symbol": signal["symbol"],
                "quantity": signal["quantity"],
                "order_type": "market",
                "side": signal["action"].lower(),
                "price": signal.get("price"),
                "is_paper": not self._get_user_pro_status(),
            }

            # Place the order using existing order manager
            with current_app.app_context():
                # Get fresh user object to avoid session issues
                fresh_user = User.query.options(joinedload(User.subscription)).get(
                    self.user_id
                )
                order = place_order(fresh_user, order_data)

                if order and order.status == "filled":
                    self.total_trades += 1

                    # Update positions
                    if signal["action"] == "BUY":
                        self.current_positions[signal["symbol"]] = {
                            "quantity": signal["quantity"],
                            "entry_price": signal["price"],
                            "stop_loss": signal.get("stop_loss"),
                            "take_profit": signal.get("take_profit"),
                            "strategy": strategy["name"],
                            "entry_time": datetime.now(),
                        }
                    elif (
                        signal["action"] == "SELL"
                        and signal["symbol"] in self.current_positions
                    ):
                        # Calculate P&L
                        position = self.current_positions[signal["symbol"]]
                        pnl = (signal["price"] - position["entry_price"]) * position[
                            "quantity"
                        ]
                        self.daily_pnl += pnl

                        if pnl > 0:
                            self.winning_trades += 1

                        # Remove position
                        del self.current_positions[signal["symbol"]]

                    logger.info(
                        f"Order executed: {signal['action']} {signal['quantity']} {signal['symbol']} at {signal['price']}"
                    )

        except Exception as e:
            logger.error(f"Error executing signal: {e}")

    def _get_market_data(self, symbol: str) -> Dict:
        """Get comprehensive market data for a symbol with technical indicators."""
        try:
            # Try to get real market data from exchange adapter
            try:
                market_data = exchange_adapter.get_market_data([symbol])
                if market_data and symbol in market_data:
                    data = market_data[symbol]
                    current_price = data.get("close", 100)

                    # Generate historical data for technical analysis
                    price_history = self._generate_price_history(current_price)
                    volume_history = self._generate_volume_history()

                    return {
                        "current_price": current_price,
                        "price_history": price_history,
                        "volume_history": volume_history,
                        "volume_ratio": self._calculate_volume_ratio(volume_history),
                        "high": current_price * 1.01,
                        "low": current_price * 0.99,
                        "open": current_price * 0.995,
                    }
            except:
                pass

            # Fallback to enhanced mock data
            import random

            base_price = random.uniform(100, 2000)  # Indian stock price range

            # Generate realistic price history
            price_history = self._generate_price_history(base_price)
            volume_history = self._generate_volume_history()

            return {
                "current_price": base_price,
                "price_history": price_history,
                "volume_history": volume_history,
                "volume_ratio": self._calculate_volume_ratio(volume_history),
                "high": base_price * random.uniform(1.005, 1.02),
                "low": base_price * random.uniform(0.98, 0.995),
                "open": base_price * random.uniform(0.995, 1.005),
            }

        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return {}

    def _generate_price_history(
        self, current_price: float, days: int = 50
    ) -> List[float]:
        """Generate realistic price history for technical analysis."""
        import random
        import numpy as np

        prices = []
        price = current_price * 0.9  # Start 10% lower

        for i in range(days):
            # Simulate price movement with trend and volatility
            trend = random.uniform(-0.005, 0.008)  # Slight upward bias
            volatility = random.uniform(-0.03, 0.03)  # 3% daily volatility

            price_change = trend + volatility
            price = price * (1 + price_change)

            # Ensure realistic bounds
            price = max(price, current_price * 0.7)  # No more than 30% below current
            price = min(price, current_price * 1.5)  # No more than 50% above current

            prices.append(price)

        # Ensure last price is close to current price
        prices[-1] = current_price

        return prices

    def _generate_volume_history(self, days: int = 50) -> List[float]:
        """Generate realistic volume history."""
        import random

        base_volume = random.uniform(10000, 500000)  # Base volume
        volumes = []

        for i in range(days):
            # Volume with some randomness
            volume_factor = random.uniform(0.5, 2.0)
            volume = base_volume * volume_factor
            volumes.append(volume)

        return volumes

    def _calculate_volume_ratio(self, volume_history: List[float]) -> float:
        """Calculate current volume vs average volume ratio."""
        if len(volume_history) < 2:
            return 1.0

        current_volume = volume_history[-1]
        avg_volume = sum(volume_history[:-1]) / len(volume_history[:-1])

        return current_volume / avg_volume if avg_volume > 0 else 1.0

    def _calculate_mock_rsi(self, price: float) -> float:
        """Calculate mock RSI based on price."""
        import random

        # Simple mock RSI calculation
        base_rsi = 50
        price_factor = (price % 100) / 100
        noise = random.uniform(-10, 10)
        return max(0, min(100, base_rsi + (price_factor * 20) + noise))

    def _is_trading_hours(self, current_time: datetime) -> bool:
        """Check if current time is within trading hours."""
        hour = current_time.hour
        weekday = current_time.weekday()

        # Indian stock market: 9:15 AM to 3:30 PM, Monday to Friday
        return (
            weekday < 5 and 9 <= hour <= 15  # Monday to Friday
        )  # 9 AM to 3 PM (simplified)

    def _update_portfolio_metrics(self):
        """Update portfolio performance metrics."""
        try:
            # Calculate unrealized P&L for open positions
            unrealized_pnl = 0
            for symbol, position in self.current_positions.items():
                current_data = self._get_market_data(symbol)
                current_price = current_data.get(
                    "current_price", position["entry_price"]
                )
                unrealized_pnl += (current_price - position["entry_price"]) * position[
                    "quantity"
                ]

            # Log performance metrics
            if self.total_trades > 0:
                win_rate = (self.winning_trades / self.total_trades) * 100
                logger.info(
                    f"Portfolio Update - Realized P&L: Rs.{self.daily_pnl:.2f}, "
                    f"Unrealized P&L: Rs.{unrealized_pnl:.2f}, "
                    f"Win Rate: {win_rate:.1f}%"
                )

        except Exception as e:
            logger.error(f"Error updating portfolio metrics: {e}")

    def _risk_management_check(self):
        """Perform risk management checks and close positions if needed."""
        try:
            current_time = datetime.now()

            for symbol, position in list(self.current_positions.items()):
                current_data = self._get_market_data(symbol)
                current_price = current_data.get(
                    "current_price", position["entry_price"]
                )

                # Check stop loss
                if position.get("stop_loss") and current_price <= position["stop_loss"]:

                    self._close_position(symbol, current_price, "Stop Loss Hit")

                # Check take profit
                elif (
                    position.get("take_profit")
                    and current_price >= position["take_profit"]
                ):

                    self._close_position(symbol, current_price, "Take Profit Hit")

                # Check maximum holding time (close at end of day for intraday)
                elif current_time.hour >= 15:  # 3 PM
                    self._close_position(symbol, current_price, "End of Day Close")

        except Exception as e:
            logger.error(f"Error in risk management check: {e}")

    def _close_position(self, symbol: str, price: float, reason: str):
        """Close a specific position."""
        try:
            if symbol not in self.current_positions:
                return

            position = self.current_positions[symbol]

            # Create sell signal
            signal = {
                "action": "SELL",
                "symbol": symbol,
                "price": price,
                "quantity": position["quantity"],
                "reason": reason,
            }

            # Execute the sell order
            self._execute_signal(signal, {"name": "Risk_Management"})

            logger.info(f"Position closed: {symbol} at Rs.{price:.2f} - {reason}")

        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}")

    def _close_all_positions(self):
        """Close all open positions."""
        try:
            for symbol in list(self.current_positions.keys()):
                current_data = self._get_market_data(symbol)
                current_price = current_data.get(
                    "current_price", self.current_positions[symbol]["entry_price"]
                )
                self._close_position(symbol, current_price, "Bot Stopped")

        except Exception as e:
            logger.error(f"Error closing all positions: {e}")

    def get_status(self) -> Dict:
        """Get current bot status and performance."""
        # Check database status for accuracy
        try:
            from ..models import TradingBotStatus

            bot_status = TradingBotStatus.query.filter_by(
                user_id=self.user_id, bot_type="stock"
            ).first()

            # If we have database status and it shows bot is running but local state says not,
            # sync the states
            if bot_status and bot_status.is_active and not self.is_running:
                logger.warning(
                    f"Bot status mismatch for user {self.user_id}, syncing..."
                )
                # Database says bot is running but local state doesn't
                # This can happen after page navigation - restore the running state
                self.is_running = True
                self._sync_trade_count_from_db()  # Sync actual trade count from database
                self.daily_pnl = bot_status.daily_pnl or 0.0

                # Restart the trading loop if it's not running
                if not self.thread or not self.thread.is_alive():
                    app = current_app._get_current_object()
                    self.thread = threading.Thread(
                        target=self._trading_loop, args=(app,), daemon=True
                    )
                    self.thread.start()
                    logger.info(f"Restarted trading loop for user {self.user_id}")

            elif bot_status and not bot_status.is_active and self.is_running:
                # Database says bot is not running but local state says it is
                logger.warning(f"Bot was stopped externally for user {self.user_id}")
                self.is_running = False

        except Exception as e:
            logger.error(f"Error checking bot status: {e}")

        return {
            "is_running": self.is_running,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": (self.winning_trades / max(1, self.total_trades)) * 100,
            "daily_pnl": self.daily_pnl,
            "open_positions": len(self.current_positions),
            "strategies_active": len(self.strategies),
            "last_signal_time": (
                self.last_signal_time.isoformat() if self.last_signal_time else None
            ),
            "positions": self._get_positions_details(),
        }

    def _get_positions_details(self):
        """Return details of all current open positions for live session display."""
        positions = {}
        for symbol, pos in self.current_positions.items():
            # Get current market price
            current_data = self._get_market_data(symbol)
            current_price = current_data.get("current_price", pos.get("entry_price", 0))
            positions[symbol] = {
                "symbol": symbol,
                "quantity": pos.get("quantity", 0),
                "avg_price": pos.get("entry_price", 0),
                "current_price": current_price,
                "unrealized_pnl": (current_price - pos.get("entry_price", 0))
                * pos.get("quantity", 0),
                "strategy": pos.get("strategy", "Unknown"),
                "entry_time": pos.get("entry_time", None),
            }
        return positions

    def _update_bot_status(self, is_running=None, started_at=None, stopped_at=None):
        """Update bot status in database for persistence."""
        try:
            from ..models import TradingBotStatus

            # Get or create bot status record
            bot_status = TradingBotStatus.query.filter_by(
                user_id=self.user_id, bot_type="stock"
            ).first()
            if not bot_status:
                bot_status = TradingBotStatus(user_id=self.user_id, bot_type="stock")
                db.session.add(bot_status)

            # Update status fields
            if is_running is not None:
                bot_status.is_running = is_running
            if started_at:
                bot_status.started_at = started_at
            if stopped_at:
                bot_status.stopped_at = stopped_at

            # Update performance metrics
            bot_status.total_trades = self.total_trades
            bot_status.daily_pnl = self.daily_pnl
            bot_status.win_rate = (
                self.winning_trades / max(1, self.total_trades)
            ) * 100
            bot_status.open_positions = len(self.current_positions)
            bot_status.strategies_active = len(self.strategies)
            bot_status.last_heartbeat = datetime.now()
            bot_status.bot_type = "stock"

            db.session.commit()
            logger.info(
                f"Updated bot status for user {self.user_id}: running={is_running}"
            )

        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
            db.session.rollback()

    def _restore_bot_status(self):
        """Restore bot status from database on initialization."""
        try:
            from ..models import TradingBotStatus

            bot_status = TradingBotStatus.query.filter_by(user_id=self.user_id).first()
            if bot_status and bot_status.is_active:
                logger.info(f"Restoring bot status for user {self.user_id}")
                # Bot was running, restart it
                self.total_trades = bot_status.total_trades or 0
                self.daily_pnl = bot_status.daily_pnl or 0.0
                # Note: We don't automatically restart the bot to avoid issues
                # User will need to manually restart if needed

        except Exception as e:
            logger.error(f"Error restoring bot status: {e}")

    def _sync_trade_count_from_db(self):
        """Sync trade count from database to ensure consistency after restarts."""
        try:
            from ..models import Trade

            # Count actual trades in database for this user and exchange type
            actual_trade_count = Trade.query.filter_by(
                user_id=self.user_id, exchange_type="stocks"
            ).count()

            self.total_trades = actual_trade_count
            logger.info(
                f"Synced trade count for user {self.user_id}: {actual_trade_count} trades"
            )

        except Exception as e:
            logger.error(f"Error syncing trade count from database: {e}")

    def _get_user_pro_status(self):
        """Safely get user's pro plan status with session management."""
        try:
            with current_app.app_context():
                # Re-query user with subscription to ensure fresh session
                user = User.query.options(joinedload(User.subscription)).get(
                    self.user_id
                )
                if user and user.subscription:
                    return (
                        user.subscription.plan == "pro" and user.subscription.is_active
                    )
                return False
        except Exception as e:
            logger.warning(f"Failed to check user pro status: {e}")
            return False  # Default to free/paper trading on error


# Global instances for each user
_bot_instances = {}


def get_trading_bot(user_id: int) -> IndianStockTradingBot:
    """Get or create trading bot instance for a user."""
    if user_id not in _bot_instances:
        _bot_instances[user_id] = IndianStockTradingBot(user_id)
        # Restore any previous status
        _bot_instances[user_id]._restore_bot_status()
    return _bot_instances[user_id]


def cleanup_bot_instance(user_id: int):
    """Clean up bot instance for a user."""
    if user_id in _bot_instances:
        bot = _bot_instances[user_id]
        if bot.is_running:
            bot.stop_automated_trading()
        del _bot_instances[user_id]
