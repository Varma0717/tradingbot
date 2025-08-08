import time
import logging
from datetime import datetime, timedelta
from ..exchanges.real_binance import RealBinanceExchange


class RealStrategyManager:
    def __init__(self):
        """Initialize real trading strategy manager"""
        self.exchange = RealBinanceExchange()
        self.is_running = False
        self.strategies = {}
        self.trading_pair = "BTCUSDT"  # Default pair (will be overridden by settings)

        # Default configurable settings
        self.settings = {
            "trading_pair": "BTCUSDT",  # Default trading pair
            "order_size": 2.0,  # Default $2 per order
            "grid_levels": 3,  # Conservative default
            "max_open_orders": 5,
            "grid_spacing": 0.02,  # 2%
            "auto_restart": False,
        }

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Auto-create default strategy
        self._create_default_strategy()

        print("✅ Real Strategy Manager initialized")

    def _create_default_strategy(self):
        """Create and add default real trading strategy"""
        try:
            from .real_universal_strategy import RealUniversalGridDCAStrategy

            # Create default strategy (no parameters needed)
            default_strategy = RealUniversalGridDCAStrategy()

            # Apply current settings to strategy
            default_strategy.order_size_usd = self.settings.get("order_size", 10.0)
            default_strategy.grid_levels = self.settings.get("grid_levels", 5)
            default_strategy.grid_spacing = self.settings.get("grid_spacing", 0.02)

            # Set trading pair from settings
            trading_pair = self.settings.get("trading_pair", "BTCUSDT")
            default_strategy.trading_pair = trading_pair
            self.trading_pair = trading_pair  # Set manager's trading pair too
            print(f"📊 Strategy trading pair set to: {trading_pair}")

            print(
                f"📊 Strategy configured: ${self.settings.get('order_size', 10.0)}/order, {self.settings.get('grid_levels', 5)} levels, {self.settings.get('grid_spacing', 0.02)*100:.1f}% spacing"
            )

            # Add to strategies
            self.add_strategy("default_real_grid", default_strategy)

        except Exception as e:
            print(f"❌ Error creating default strategy: {e}")
            self.logger.error(f"Error creating default strategy: {e}")

    def update_settings(self, new_settings):
        """Update trading settings and recreate strategies"""
        try:
            print(f"🔧 Updating settings: {new_settings}")

            # Update settings
            for key, value in new_settings.items():
                # Handle trading_pair separately since it's not in self.settings initially
                if key == "trading_pair":
                    self.trading_pair = value
                    self.settings[key] = value
                    print(f"✅ Updated {key}: {value}")
                elif key in self.settings or key in [
                    "take_profit",
                    "stop_loss",
                    "enable_notifications",
                    "paper_balance",
                    "real_investment",
                    "max_daily_loss",
                ]:
                    # Convert to appropriate types
                    if key in [
                        "order_size",
                        "take_profit",
                        "stop_loss",
                        "grid_spacing",
                    ]:
                        self.settings[key] = float(value)
                    elif key in [
                        "grid_levels",
                        "max_open_orders",
                        "paper_balance",
                        "real_investment",
                        "max_daily_loss",
                    ]:
                        self.settings[key] = int(value)
                    elif key in ["auto_restart", "enable_notifications"]:
                        self.settings[key] = bool(value)
                    else:
                        self.settings[key] = value

                    print(f"✅ Updated {key}: {self.settings[key]}")

            # If trading is running, restart with new settings
            was_running = self.is_running
            if was_running:
                print("🔄 Restarting trading with new settings...")
                self.stop_trading()
                time.sleep(1)

                # Recreate strategy with new settings
                self._recreate_strategies()

                # Restart trading
                return self.start_trading()
            else:
                # Just recreate strategies for next start
                self._recreate_strategies()
                return True

        except Exception as e:
            print(f"❌ Error updating settings: {e}")
            self.logger.error(f"Error updating settings: {e}")
            return False

    def _recreate_strategies(self):
        """Recreate strategies with current settings"""
        try:
            # Clear existing strategies
            self.strategies.clear()

            # Recreate with new settings
            self._create_default_strategy()

        except Exception as e:
            print(f"❌ Error recreating strategies: {e}")

    def get_settings(self):
        """Get current settings"""
        return self.settings.copy()

    def add_strategy(self, strategy_name, strategy_instance):
        """Add a strategy to the manager"""
        self.strategies[strategy_name] = strategy_instance
        print(f"✅ Strategy '{strategy_name}' added to manager")

    def start_trading(self):
        """Start real trading"""
        if self.is_running:
            print("⚠️ Trading is already running")
            return True

        print(f"🚀 Starting real trading with {len(self.strategies)} strategies...")

        if not self.strategies:
            print("❌ No strategies available to start")
            return False

        self.is_running = True

        try:
            # Get current balance
            balance = self.exchange.get_balance()

            # Use the trading pair from settings (user's choice)
            if "trading_pair" in self.settings:
                self.trading_pair = self.settings["trading_pair"]
                print(f"� Using trading pair from settings: {self.trading_pair}")
            else:
                # Fallback to default if no setting
                self.trading_pair = "BTCUSDT"
                print(f"� Using default trading pair: {self.trading_pair}")

            print(f"💰 Current balance: ${balance:.2f}")

            # Start all strategies
            started_count = 0
            for name, strategy in self.strategies.items():
                try:
                    print(f"🎯 Starting strategy: {name}")
                    strategy.set_trading_pair(self.trading_pair)
                    strategy.start()
                    started_count += 1
                    print(f"✅ Strategy '{name}' started successfully")
                except Exception as e:
                    print(f"❌ Error starting strategy '{name}': {e}")

            if started_count > 0:
                print(
                    f"🎉 Successfully started {started_count}/{len(self.strategies)} strategies"
                )
                return True
            else:
                print("❌ Failed to start any strategies")
                self.is_running = False
                return False

        except Exception as e:
            print(f"❌ Error starting trading: {e}")
            self.is_running = False
            return False

    def stop_trading(self):
        """Stop real trading"""
        if not self.is_running:
            print("⚠️ Trading is not running")
            return

        self.is_running = False
        print("🛑 Stopping real trading...")

        try:
            # Stop all strategies
            for name, strategy in self.strategies.items():
                print(f"⏹️ Stopping strategy: {name}")
                strategy.stop()

        except Exception as e:
            print(f"❌ Error stopping trading: {e}")

    def restart_trading(self):
        """Restart trading with fresh setup"""
        print("🔄 Restarting trading...")

        # Stop current trading
        self.stop_trading()

        # Wait a moment
        time.sleep(2)

        # Start fresh
        return self.start_trading()

    def get_balance(self):
        """Get current balance (cached to reduce API calls)"""
        try:
            return self.exchange.get_balance()
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return 0.0

    def get_status(self):
        """Get current trading status"""
        return {
            "is_running": self.is_running,
            "status": "active" if self.is_running else "stopped",
            "trading_pair": self.trading_pair,
            "balance": self.get_balance(),
            "strategies": list(self.strategies.keys()),
        }

    def get_trades(self):
        """Get all trades from strategies"""
        all_trades = []
        for strategy in self.strategies.values():
            if hasattr(strategy, "get_trades"):
                all_trades.extend(strategy.get_trades())
        return all_trades

    def get_active_orders(self):
        """Get all active orders from strategies"""
        all_orders = []
        for strategy in self.strategies.values():
            if hasattr(strategy, "get_active_orders"):
                all_orders.extend(strategy.get_active_orders())
        return all_orders

    def change_trading_pair(self, new_pair):
        """Change the trading pair"""
        try:
            # Validate the pair exists on Binance
            price = self.exchange.get_current_price(new_pair)
            if price > 0:
                old_pair = self.trading_pair
                self.trading_pair = new_pair

                # Update all strategies
                for strategy in self.strategies.values():
                    strategy.set_trading_pair(new_pair)

                print(f"✅ Trading pair changed from {old_pair} to {new_pair}")
                return True
            else:
                print(f"❌ Invalid trading pair: {new_pair}")
                return False

        except Exception as e:
            print(f"❌ Error changing trading pair: {e}")
            return False

    def get_real_trades(self):
        """Get real trading trades (alias for get_trades)"""
        return self.get_trades()

    def get_real_orders(self):
        """Get real trading orders (alias for get_active_orders)"""
        return self.get_active_orders()

    def get_analytics(self):
        """Get comprehensive trading analytics"""
        try:
            all_analytics = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "total_volume": 0.0,
                "average_profit_per_trade": 0.0,
                "active_orders_count": len(self.get_active_orders()),
            }

            # Aggregate analytics from all strategies
            for strategy in self.strategies.values():
                if hasattr(strategy, "get_analytics"):
                    strategy_analytics = strategy.get_analytics()
                    all_analytics["total_trades"] += strategy_analytics.get(
                        "total_trades", 0
                    )
                    all_analytics["winning_trades"] += strategy_analytics.get(
                        "winning_trades", 0
                    )
                    all_analytics["losing_trades"] += strategy_analytics.get(
                        "losing_trades", 0
                    )
                    all_analytics["total_profit"] += strategy_analytics.get(
                        "total_profit", 0.0
                    )
                    all_analytics["total_volume"] += strategy_analytics.get(
                        "total_volume", 0.0
                    )

            # Calculate overall win rate
            if all_analytics["total_trades"] > 0:
                all_analytics["win_rate"] = round(
                    (all_analytics["winning_trades"] / all_analytics["total_trades"])
                    * 100,
                    2,
                )
                all_analytics["average_profit_per_trade"] = round(
                    all_analytics["total_profit"] / all_analytics["total_trades"], 4
                )

            return all_analytics
        except Exception as e:
            self.logger.error(f"Error getting analytics: {e}")
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "total_volume": 0.0,
                "average_profit_per_trade": 0.0,
                "active_orders_count": 0,
            }
