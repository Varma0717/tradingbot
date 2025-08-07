"""
Risk Manager
Handles position sizing, stop losses, and risk limits.
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta

from ..core.exceptions import RiskViolationError, RiskError
from ..utils.logger import get_logger


class RiskManager:
    """
    Manages trading risk through position sizing, stop losses, and exposure limits.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the risk manager.

        Args:
            config: Risk management configuration
        """
        self.logger = get_logger(__name__)
        self.config = config.get("risk_management", {})

        # Risk parameters
        self.max_position_size = self.config.get(
            "max_position_size", 0.1
        )  # 10% of portfolio
        self.max_daily_loss = self.config.get(
            "max_daily_loss", 0.05
        )  # 5% daily loss limit
        self.max_drawdown = self.config.get("max_drawdown", 0.15)  # 15% max drawdown
        self.max_open_positions = self.config.get("max_open_positions", 5)
        self.max_risk_per_trade = self.config.get(
            "max_risk_per_trade", 0.02
        )  # 2% per trade

        # Stop loss settings
        self.default_stop_loss = self.config.get("default_stop_loss", 0.05)  # 5%
        self.trailing_stop = self.config.get("trailing_stop", False)
        self.trailing_stop_distance = self.config.get(
            "trailing_stop_distance", 0.03
        )  # 3%

        # Risk tracking
        self.daily_pnl = 0.0
        self.start_of_day_balance = 0.0
        self.peak_balance = 0.0
        self.current_positions = []
        self.open_positions = {}  # Dictionary to track open positions
        self.risk_violations = []

        self.logger.info("Risk Manager initialized")

    def validate_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        portfolio_value: float,
    ) -> Dict[str, Any]:
        """
        Validate if a trade meets risk management criteria.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Trade quantity
            price: Trade price
            portfolio_value: Current portfolio value

        Returns:
            Dict with validation result and details
        """
        try:
            validation_result = {
                "valid": True,
                "reasons": [],
                "warnings": [],
                "suggested_quantity": quantity,
            }

            trade_value = quantity * price
            position_size_ratio = (
                trade_value / portfolio_value if portfolio_value > 0 else 0
            )

            # Check maximum position size
            if position_size_ratio > self.max_position_size:
                suggested_quantity = (portfolio_value * self.max_position_size) / price
                validation_result.update(
                    {
                        "valid": False,
                        "reasons": [
                            f"Position size {position_size_ratio:.2%} exceeds maximum {self.max_position_size:.2%}"
                        ],
                        "suggested_quantity": suggested_quantity,
                    }
                )

            # Check maximum open positions
            if len(self.current_positions) >= self.max_open_positions and side == "buy":
                validation_result.update(
                    {
                        "valid": False,
                        "reasons": validation_result["reasons"]
                        + [
                            f"Maximum open positions ({self.max_open_positions}) reached"
                        ],
                    }
                )

            # Check daily loss limit
            if self.start_of_day_balance > 0:
                current_loss = (
                    self.start_of_day_balance - portfolio_value
                ) / self.start_of_day_balance
                if current_loss > self.max_daily_loss:
                    validation_result.update(
                        {
                            "valid": False,
                            "reasons": validation_result["reasons"]
                            + [f"Daily loss limit {self.max_daily_loss:.2%} exceeded"],
                        }
                    )

            # Check maximum drawdown
            if self.peak_balance > 0:
                current_drawdown = (
                    self.peak_balance - portfolio_value
                ) / self.peak_balance
                if current_drawdown > self.max_drawdown:
                    validation_result.update(
                        {
                            "valid": False,
                            "reasons": validation_result["reasons"]
                            + [f"Maximum drawdown {self.max_drawdown:.2%} exceeded"],
                        }
                    )

            # Risk per trade check
            if side == "buy":
                risk_amount = trade_value * self.default_stop_loss
                risk_ratio = risk_amount / portfolio_value if portfolio_value > 0 else 0

                if risk_ratio > self.max_risk_per_trade:
                    validation_result["warnings"].append(
                        f"Trade risk {risk_ratio:.2%} exceeds recommended {self.max_risk_per_trade:.2%}"
                    )

            self.logger.debug(f"Trade validation for {symbol}: {validation_result}")
            return validation_result

        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            raise RiskError(f"Trade validation failed: {e}")

    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        portfolio_value: float,
        risk_amount: Optional[float] = None,
    ) -> float:
        """
        Calculate optimal position size based on risk parameters.

        Args:
            symbol: Trading symbol
            price: Current price
            portfolio_value: Current portfolio value
            risk_amount: Specific risk amount (optional)

        Returns:
            Calculated position size
        """
        try:
            if risk_amount is None:
                risk_amount = portfolio_value * self.max_risk_per_trade

            # Calculate position size based on stop loss
            stop_loss_distance = price * self.default_stop_loss
            position_size = risk_amount / stop_loss_distance

            # Ensure position doesn't exceed maximum position size
            max_position_value = portfolio_value * self.max_position_size
            max_quantity = max_position_value / price

            position_size = min(position_size, max_quantity)

            self.logger.debug(f"Calculated position size for {symbol}: {position_size}")
            return position_size

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            raise RiskError(f"Position size calculation failed: {e}")

    def calculate_stop_loss(self, symbol: str, side: str, entry_price: float) -> float:
        """
        Calculate stop loss price for a position.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            entry_price: Entry price

        Returns:
            Stop loss price
        """
        try:
            if side.lower() == "buy":
                stop_loss = entry_price * (1 - self.default_stop_loss)
            else:  # sell
                stop_loss = entry_price * (1 + self.default_stop_loss)

            self.logger.debug(f"Calculated stop loss for {symbol} {side}: {stop_loss}")
            return stop_loss

        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {e}")
            raise RiskError(f"Stop loss calculation failed: {e}")

    def update_portfolio_metrics(self, portfolio_value: float):
        """
        Update portfolio metrics for risk tracking.

        Args:
            portfolio_value: Current portfolio value
        """
        try:
            # Update peak balance
            if portfolio_value > self.peak_balance:
                self.peak_balance = portfolio_value

            # Set start of day balance if not set
            if self.start_of_day_balance == 0:
                self.start_of_day_balance = portfolio_value

            # Check if new day (simplified check)
            now = datetime.now()
            if now.hour == 0 and now.minute < 5:  # Reset at midnight
                self.start_of_day_balance = portfolio_value
                self.daily_pnl = 0.0

            # Calculate daily P&L
            self.daily_pnl = portfolio_value - self.start_of_day_balance

            self.logger.debug(
                f"Updated portfolio metrics: value={portfolio_value}, daily_pnl={self.daily_pnl}"
            )

        except Exception as e:
            self.logger.error(f"Error updating portfolio metrics: {e}")

    def add_position(self, position: Dict[str, Any]):
        """
        Add a position to risk tracking.

        Args:
            position: Position information
        """
        try:
            self.current_positions.append(position)
            self.logger.debug(f"Added position to risk tracking: {position}")

        except Exception as e:
            self.logger.error(f"Error adding position: {e}")

    def remove_position(self, symbol: str):
        """
        Remove a position from risk tracking.

        Args:
            symbol: Trading symbol to remove
        """
        try:
            self.current_positions = [
                p for p in self.current_positions if p.get("symbol") != symbol
            ]
            self.logger.debug(f"Removed position from risk tracking: {symbol}")

        except Exception as e:
            self.logger.error(f"Error removing position: {e}")

    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics.

        Returns:
            Dict with risk metrics
        """
        try:
            current_drawdown = 0.0
            if self.peak_balance > 0 and self.start_of_day_balance > 0:
                current_value = self.start_of_day_balance + self.daily_pnl
                current_drawdown = (
                    self.peak_balance - current_value
                ) / self.peak_balance

            daily_return = 0.0
            if self.start_of_day_balance > 0:
                daily_return = self.daily_pnl / self.start_of_day_balance

            metrics = {
                "daily_pnl": self.daily_pnl,
                "daily_return": daily_return,
                "current_drawdown": current_drawdown,
                "max_drawdown_limit": self.max_drawdown,
                "daily_loss_limit": self.max_daily_loss,
                "open_positions": len(self.current_positions),
                "max_positions": self.max_open_positions,
                "risk_violations": len(self.risk_violations),
            }

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return {}

    def check_emergency_stop(self, portfolio_value: float) -> bool:
        """
        Check if emergency stop conditions are met.

        Args:
            portfolio_value: Current portfolio value

        Returns:
            True if emergency stop should be triggered
        """
        try:
            # Check daily loss limit
            if self.start_of_day_balance > 0:
                daily_loss = (
                    self.start_of_day_balance - portfolio_value
                ) / self.start_of_day_balance
                if daily_loss > self.max_daily_loss:
                    self.logger.warning(
                        f"Emergency stop: Daily loss {daily_loss:.2%} exceeds limit {self.max_daily_loss:.2%}"
                    )
                    return True

            # Check maximum drawdown
            if self.peak_balance > 0:
                drawdown = (self.peak_balance - portfolio_value) / self.peak_balance
                if drawdown > self.max_drawdown:
                    self.logger.warning(
                        f"Emergency stop: Drawdown {drawdown:.2%} exceeds limit {self.max_drawdown:.2%}"
                    )
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking emergency stop: {e}")
            return False

    def reset_daily_metrics(self):
        """Reset daily risk metrics."""
        try:
            self.daily_pnl = 0.0
            self.start_of_day_balance = 0.0
            self.risk_violations.clear()
            self.logger.info("Daily risk metrics reset")

        except Exception as e:
            self.logger.error(f"Error resetting daily metrics: {e}")

    async def check_risk_limits(self) -> Dict[str, Any]:
        """
        Check all risk limits and return risk status.
        This method is called by the bot's risk monitoring tasks.

        Returns:
            Dict containing risk status information
        """
        try:
            risk_status = {
                "status": "ok",
                "violations": [],
                "metrics": self.get_risk_metrics(),
                "emergency_stop": False,
            }

            # Check daily loss limit
            if self.daily_pnl < -abs(self.config.get("max_daily_loss", 1000)):
                risk_status["violations"].append("Daily loss limit exceeded")
                risk_status["status"] = "warning"

            # Check drawdown limit
            current_drawdown = self.get_risk_metrics().get("max_drawdown", 0)
            max_allowed_drawdown = self.config.get("max_drawdown_percent", 10)
            if current_drawdown > max_allowed_drawdown:
                risk_status["violations"].append(
                    f"Drawdown limit exceeded: {current_drawdown:.2f}%"
                )
                risk_status["status"] = "critical"

            # Check portfolio exposure
            total_exposure = sum(
                abs(pos.get("size", 0)) for pos in self.open_positions.values()
            )
            max_exposure = self.config.get("max_portfolio_exposure", 100000)
            if total_exposure > max_exposure:
                risk_status["violations"].append("Portfolio exposure limit exceeded")
                risk_status["status"] = "warning"

            # Log risk check results
            if risk_status["violations"]:
                self.logger.warning(
                    f"Risk violations detected: {risk_status['violations']}"
                )
            else:
                self.logger.debug("Risk limits check passed")

            return risk_status

        except Exception as e:
            self.logger.error(f"Error checking risk limits: {e}")
            return {
                "status": "error",
                "violations": [f"Risk check error: {str(e)}"],
                "metrics": {},
                "emergency_stop": False,
            }
