"""
Trading Mode Manager - Centralized mode switching and management
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    PAPER = "paper"
    REAL = "real"


class TradingModeManager:
    """
    Centralized trading mode management.
    Ensures proper separation between paper and real trading.
    """

    def __init__(self):
        self._current_mode = TradingMode.PAPER  # Always start in paper mode for safety
        self._mode_file = "data/trading_mode.json"
        self._paper_strategy_manager = None
        self._real_strategy_manager = None
        self._paper_balance = 10000.0  # Default paper trading balance

        # Load saved mode
        self._load_mode()

        logger.info(
            f"Trading Mode Manager initialized in {self._current_mode.value} mode"
        )

    def _load_mode(self):
        """Load trading mode from file"""
        try:
            if os.path.exists(self._mode_file):
                with open(self._mode_file, "r") as f:
                    data = json.load(f)
                    mode_str = data.get("mode", "paper")
                    self._current_mode = TradingMode(mode_str)
                    self._paper_balance = data.get("paper_balance", 10000.0)
                    logger.info(f"Loaded trading mode: {self._current_mode.value}")
        except Exception as e:
            logger.warning(f"Could not load trading mode: {e}")
            self._current_mode = TradingMode.PAPER

    def _save_mode(self):
        """Save trading mode to file"""
        try:
            os.makedirs(os.path.dirname(self._mode_file), exist_ok=True)
            data = {
                "mode": self._current_mode.value,
                "paper_balance": self._paper_balance,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self._mode_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved trading mode: {self._current_mode.value}")
        except Exception as e:
            logger.error(f"Could not save trading mode: {e}")

    @property
    def current_mode(self) -> TradingMode:
        """Get current trading mode"""
        return self._current_mode

    @property
    def is_paper_trading(self) -> bool:
        """Check if currently in paper trading mode"""
        return self._current_mode == TradingMode.PAPER

    @property
    def is_real_trading(self) -> bool:
        """Check if currently in real trading mode"""
        return self._current_mode == TradingMode.REAL

    def switch_to_paper(self) -> bool:
        """Switch to paper trading mode"""
        try:
            if self._current_mode == TradingMode.PAPER:
                logger.info("Already in paper trading mode")
                return True

            # Stop real trading if active
            if self._real_strategy_manager and hasattr(
                self._real_strategy_manager, "stop_trading"
            ):
                self._real_strategy_manager.stop_trading()

            self._current_mode = TradingMode.PAPER
            self._save_mode()

            logger.info("✅ Switched to PAPER trading mode")
            return True

        except Exception as e:
            logger.error(f"Failed to switch to paper trading: {e}")
            return False

    def switch_to_real(self) -> bool:
        """Switch to real trading mode"""
        try:
            # Safety checks
            api_key = os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_SECRET_KEY")

            if not api_key or not api_secret:
                logger.error(
                    "Cannot switch to real trading: Missing Binance API credentials"
                )
                return False

            if self._current_mode == TradingMode.REAL:
                logger.info("Already in real trading mode")
                return True

            # Stop paper trading if active
            if self._paper_strategy_manager and hasattr(
                self._paper_strategy_manager, "stop_trading"
            ):
                self._paper_strategy_manager.stop_trading()

            self._current_mode = TradingMode.REAL
            self._save_mode()

            logger.warning("⚠️ Switched to REAL trading mode - REAL MONEY AT RISK!")
            return True

        except Exception as e:
            logger.error(f"Failed to switch to real trading: {e}")
            return False

    def get_active_strategy_manager(self):
        """Get the active strategy manager based on current mode"""
        if self._current_mode == TradingMode.PAPER:
            return self._get_paper_strategy_manager()
        else:
            return self._get_real_strategy_manager()

    def _get_paper_strategy_manager(self):
        """Get or create paper strategy manager"""
        if self._paper_strategy_manager is None:
            try:
                from ..strategies.strategy_manager import StrategyManager

                self._paper_strategy_manager = StrategyManager()
                logger.info("Paper strategy manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize paper strategy manager: {e}")
        return self._paper_strategy_manager

    def _get_real_strategy_manager(self):
        """Get or create real strategy manager"""
        if self._real_strategy_manager is None:
            try:
                from ..strategies.real_strategy_manager import RealStrategyManager

                self._real_strategy_manager = RealStrategyManager()
                logger.info("Real strategy manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize real strategy manager: {e}")
        return self._real_strategy_manager

    def get_balance(self) -> float:
        """Get balance based on current trading mode"""
        try:
            if self._current_mode == TradingMode.PAPER:
                return self._paper_balance
            else:
                # Get real balance from real strategy manager
                manager = self._get_real_strategy_manager()
                if manager and hasattr(manager, "get_balance"):
                    return manager.get_balance()
                elif manager and hasattr(manager, "exchange") and manager.exchange:
                    # Fallback to direct exchange balance
                    balance_info = manager.exchange.get_balance()
                    return balance_info
                return 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            # Return paper balance as fallback
            return (
                self._paper_balance if self._current_mode == TradingMode.PAPER else 0.0
            )

    def update_paper_balance(self, amount: float):
        """Update paper trading balance"""
        if self._current_mode == TradingMode.PAPER:
            self._paper_balance = amount
            self._save_mode()

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive trading mode status"""
        manager = self.get_active_strategy_manager()

        return {
            "mode": self._current_mode.value,
            "is_paper_trading": self.is_paper_trading,
            "is_real_trading": self.is_real_trading,
            "balance": self.get_balance(),
            "paper_balance": self._paper_balance,
            "manager_status": (
                manager.get_status()
                if manager and hasattr(manager, "get_status")
                else {}
            ),
            "api_configured": bool(
                os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_SECRET_KEY")
            ),
        }


# Global instance
trading_mode_manager = TradingModeManager()
