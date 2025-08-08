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
        self.trading_pair = "DOGEUSDT"  # Default pair for small balances

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        print("✅ Real Strategy Manager initialized")

    def add_strategy(self, strategy_name, strategy_instance):
        """Add a strategy to the manager"""
        self.strategies[strategy_name] = strategy_instance
        print(f"✅ Strategy '{strategy_name}' added to manager")

    def start_trading(self):
        """Start real trading"""
        if self.is_running:
            print("⚠️ Trading is already running")
            return

        self.is_running = True
        print("🚀 Starting real trading...")

        try:
            # Get current balance
            balance = self.exchange.get_balance()

            # Choose trading pair based on balance
            if balance >= 50:
                self.trading_pair = "BTCUSDT"
                print(f"💰 Large balance detected (${balance:.2f}), using BTC/USDT")
            else:
                self.trading_pair = "DOGEUSDT"
                print(f"💡 Small balance detected (${balance:.2f}), using DOGE/USDT")

            # Start all strategies
            for name, strategy in self.strategies.items():
                print(f"🎯 Starting strategy: {name}")
                strategy.set_trading_pair(self.trading_pair)
                strategy.start()

        except Exception as e:
            print(f"❌ Error starting trading: {e}")
            self.is_running = False

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

    def get_status(self):
        """Get current trading status"""
        return {
            "is_running": self.is_running,
            "status": "active" if self.is_running else "stopped",
            "trading_pair": self.trading_pair,
            "balance": self.exchange.get_balance(),
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
