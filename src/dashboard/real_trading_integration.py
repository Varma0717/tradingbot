import threading
import time
from ..strategies.real_strategy_manager import RealStrategyManager
from ..strategies.real_universal_strategy import RealUniversalGridDCAStrategy


class RealTradingIntegration:
    def __init__(self):
        """Initialize real trading integration"""
        self.strategy_manager = None
        self.universal_strategy = None
        self.is_initialized = False

        print("🔧 Real Trading Integration initialized")

    def initialize(self):
        """Initialize real trading components"""
        try:
            if self.is_initialized:
                print("⚠️ Real trading already initialized")
                return True

            print("🚀 Initializing real trading system...")

            # Initialize strategy manager
            self.strategy_manager = RealStrategyManager()

            # Initialize universal strategy
            self.universal_strategy = RealUniversalGridDCAStrategy()

            # Add strategy to manager
            self.strategy_manager.add_strategy(
                "Universal_Grid_DCA", self.universal_strategy
            )

            self.is_initialized = True
            print("✅ Real trading system initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize real trading: {e}")
            return False

    def start_trading(self):
        """Start real trading"""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return False

            self.strategy_manager.start_trading()
            return True

        except Exception as e:
            print(f"❌ Error starting real trading: {e}")
            return False

    def stop_trading(self):
        """Stop real trading"""
        try:
            if not self.is_initialized:
                print("⚠️ Real trading not initialized")
                return False

            self.strategy_manager.stop_trading()
            return True

        except Exception as e:
            print(f"❌ Error stopping real trading: {e}")
            return False

    def get_status(self):
        """Get real trading status"""
        try:
            if not self.is_initialized or not self.strategy_manager:
                return {
                    "initialized": False,
                    "trading": False,
                    "balance": 0.0,
                    "trading_pair": "N/A",
                }

            status = self.strategy_manager.get_status()
            return {
                "initialized": self.is_initialized,
                "trading": status["is_running"],
                "balance": status["balance"],
                "trading_pair": status["trading_pair"],
            }

        except Exception as e:
            print(f"❌ Error getting real trading status: {e}")
            return {
                "initialized": False,
                "trading": False,
                "balance": 0.0,
                "trading_pair": "N/A",
                "error": str(e),
            }

    def get_live_balance(self):
        """Get live balance from Binance"""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return 0.0

            return self.strategy_manager.exchange.get_balance()

        except Exception as e:
            print(f"❌ Error getting live balance: {e}")
            return 0.0

    def change_trading_pair(self, new_pair):
        """Change trading pair"""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return False

            return self.strategy_manager.change_trading_pair(new_pair)

        except Exception as e:
            print(f"❌ Error changing trading pair: {e}")
            return False

    async def get_real_trading_status(self):
        """Get comprehensive real trading status"""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return {
                        "available": False,
                        "mode": "unavailable",
                        "is_initialized": False,
                        "is_running": False,
                        "balance": 0.0,
                        "trading_pair": "DOGEUSDT",
                        "error": "Not initialized",
                    }

            status = self.strategy_manager.get_status()
            balance = status.get("balance", 0.0)

            return {
                "available": True,
                "mode": "real",
                "is_initialized": self.is_initialized,
                "is_running": status.get("is_running", False),
                "balance": balance,
                "trading_pair": status.get("trading_pair", "DOGEUSDT"),
                "strategies": status.get("strategies", []),
                "account": {"usdt_balance": balance, "total_balance": balance},
                "strategy": {
                    "name": "Universal_Grid_DCA",
                    "status": (
                        "running" if status.get("is_running", False) else "stopped"
                    ),
                    "trading_pair": status.get("trading_pair", "DOGEUSDT"),
                },
            }

        except Exception as e:
            print(f"❌ Error getting real trading status: {e}")
            return {
                "available": False,
                "mode": "error",
                "is_initialized": False,
                "is_running": False,
                "balance": 0.0,
                "trading_pair": "DOGEUSDT",
                "error": str(e),
            }

    def get_real_trades(self):
        """Get real trading history"""
        try:
            # This would return actual trade history from Binance
            # For now, return empty list
            return []
        except Exception as e:
            print(f"❌ Error getting real trades: {e}")
            return []

    def get_real_orders(self):
        """Get real open orders"""
        try:
            if not self.is_initialized:
                return []
            # This would return actual open orders from Binance
            # For now, return empty list
            return []
        except Exception as e:
            print(f"❌ Error getting real orders: {e}")
            return []


# Global instance
real_trading = RealTradingIntegration()
real_trading_integrator = real_trading  # Alias for dashboard compatibility
