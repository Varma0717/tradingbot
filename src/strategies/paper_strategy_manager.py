import time
import logging
from datetime import datetime, timedelta
from ..exchanges.paper_binance import PaperBinanceExchange


class PaperStrategyManager:
    def __init__(self):
        """Initialize paper trading strategy manager"""
        self.exchange = PaperBinanceExchange()
        self.is_running = False
        self.strategies = {}
        self.trading_pair = "DOGEUSDT"  # Default pair for testing

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        print("✅ Paper Strategy Manager initialized")

    def add_strategy(self, strategy_name, strategy_instance):
        """Add a strategy to the manager"""
        self.strategies[strategy_name] = strategy_instance
        print(f"✅ Strategy '{strategy_name}' added to paper manager")

    def start_trading(self):
        """Start paper trading"""
        if self.is_running:
            print("⚠️ Paper trading is already running")
            return

        self.is_running = True
        print("🚀 Starting paper trading...")

        try:
            # Get current paper balance
            balance = self.exchange.get_balance()

            # Choose trading pair based on balance (for testing)
            if balance >= 50:
                self.trading_pair = "BTCUSDT"
                print(f"💰 Paper balance (${balance:.2f}), testing with BTC/USDT")
            else:
                self.trading_pair = "DOGEUSDT"
                print(f"💡 Paper balance (${balance:.2f}), testing with DOGE/USDT")

            # Start all strategies in paper mode
            for name, strategy in self.strategies.items():
                print(f"🎯 Starting paper strategy: {name}")
                strategy.set_trading_pair(self.trading_pair)
                strategy.start()

        except Exception as e:
            print(f"❌ Error starting paper trading: {e}")
            self.is_running = False

    def stop_trading(self):
        """Stop paper trading"""
        if not self.is_running:
            print("⚠️ Paper trading is not running")
            return

        self.is_running = False
        print("🛑 Stopping paper trading...")

        try:
            # Stop all strategies
            for name, strategy in self.strategies.items():
                print(f"⏹️ Stopping paper strategy: {name}")
                strategy.stop()

        except Exception as e:
            print(f"❌ Error stopping paper trading: {e}")

    def get_status(self):
        """Get current paper trading status"""
        return {
            "is_running": self.is_running,
            "status": "active" if self.is_running else "stopped",
            "trading_pair": self.trading_pair,
            "balance": self.exchange.get_balance(),
            "strategies": list(self.strategies.keys()),
            "mode": "paper",
        }

    def get_trades(self):
        """Get all paper trades from strategies"""
        all_trades = []
        for strategy in self.strategies.values():
            if hasattr(strategy, "get_trades"):
                all_trades.extend(strategy.get_trades())
        return all_trades

    def get_active_orders(self):
        """Get all active paper orders from strategies"""
        all_orders = []
        for strategy in self.strategies.values():
            if hasattr(strategy, "get_active_orders"):
                all_orders.extend(strategy.get_active_orders())
        return all_orders

    def get_balance(self):
        """Get current paper trading balance"""
        return self.exchange.get_balance()

    def reset_paper_balance(self, new_balance=1000):
        """Reset paper trading balance for testing"""
        if hasattr(self.exchange, "reset_balance"):
            self.exchange.reset_balance(new_balance)
            print(f"💰 Paper balance reset to ${new_balance}")
        else:
            print("⚠️ Paper exchange doesn't support balance reset")
