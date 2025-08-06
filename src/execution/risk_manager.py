"""
Risk Manager for implementing comprehensive risk management and position sizing.
Provides real-time risk monitoring and automated risk controls.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.config import Config
from ..core.exceptions import RiskError, RiskViolationError
from ..utils.logger import get_logger
from ..utils.helpers import safe_float, calculate_percentage_change
from .portfolio_manager import PortfolioManager, Position, PositionSide
from .order_manager import Order, OrderManager


class RiskLevel(Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAlert:
    """Risk alert object."""

    id: str
    level: RiskLevel
    type: str
    message: str
    timestamp: datetime
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "level": self.level.value,
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
        }


@dataclass
class RiskLimits:
    """Risk limits configuration."""

    max_portfolio_risk: float  # Maximum portfolio risk %
    max_position_size: float  # Maximum position size %
    max_daily_loss: float  # Maximum daily loss %
    max_drawdown: float  # Maximum drawdown %
    risk_per_trade: float  # Risk per trade %
    max_correlation: float  # Maximum position correlation
    max_leverage: float  # Maximum leverage ratio
    var_limit: float  # Value at Risk limit

    @classmethod
    def from_config(cls, config: Config) -> "RiskLimits":
        """Create risk limits from configuration."""
        risk_config = config.risk
        return cls(
            max_portfolio_risk=getattr(risk_config, "max_portfolio_risk", 20.0),
            max_position_size=getattr(risk_config, "max_position_size", 10.0),
            max_daily_loss=getattr(risk_config, "max_daily_loss", 5.0),
            max_drawdown=getattr(risk_config, "max_drawdown", 15.0),
            risk_per_trade=getattr(risk_config, "risk_per_trade", 1.0),
            max_correlation=getattr(risk_config, "max_correlation", 0.8),
            max_leverage=getattr(risk_config, "max_leverage", 3.0),
            var_limit=getattr(risk_config, "var_limit", 10.0),
        )


class RiskManager:
    """
    Risk manager for comprehensive risk monitoring and control.
    """

    def __init__(self, config: Config, portfolio_manager: PortfolioManager):
        """
        Initialize risk manager.

        Args:
            config: Configuration object
            portfolio_manager: Portfolio manager instance
        """
        self.config = config
        self.portfolio_manager = portfolio_manager
        self.logger = get_logger(__name__)

        # Risk configuration
        self.risk_limits = RiskLimits.from_config(config)
        self.emergency_stop = False

        # Risk monitoring
        self.active_alerts: List[RiskAlert] = []
        self.risk_events: List[Dict[str, Any]] = []

        # Position sizing
        self.position_sizing_method = getattr(
            config.risk, "position_sizing_method", "fixed_risk"
        )
        self.volatility_lookback = getattr(config.risk, "volatility_lookback", 20)

        # Risk metrics
        self.current_drawdown = 0.0
        self.daily_pnl = 0.0
        self.portfolio_var = 0.0
        self.portfolio_beta = 0.0

        # Correlation tracking
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        self.price_history: Dict[str, List[float]] = {}

        # Stop loss tracking
        self.stop_losses: Dict[str, float] = {}  # symbol -> stop loss price
        self.trailing_stops: Dict[str, Dict[str, Any]] = (
            {}
        )  # symbol -> trailing stop data

    async def check_pre_trade_risk(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        stop_loss: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Check risk before placing a trade.

        Args:
            symbol: Trading symbol
            side: Trade side
            amount: Trade amount
            price: Trade price
            stop_loss: Stop loss price

        Returns:
            Tuple of (approved, reason)
        """
        try:
            # Check emergency stop
            if self.emergency_stop:
                return False, "Emergency stop activated"

            # Check portfolio risk limits
            approval, reason = await self._check_portfolio_limits(
                symbol, side, amount, price
            )
            if not approval:
                return False, reason

            # Check position size limits
            approval, reason = await self._check_position_limits(
                symbol, side, amount, price
            )
            if not approval:
                return False, reason

            # Check correlation limits
            approval, reason = await self._check_correlation_limits(
                symbol, amount, price
            )
            if not approval:
                return False, reason

            # Check risk per trade
            approval, reason = await self._check_trade_risk(
                symbol, amount, price, stop_loss
            )
            if not approval:
                return False, reason

            # Check leverage limits
            approval, reason = await self._check_leverage_limits(amount, price)
            if not approval:
                return False, reason

            self.logger.info(f"Pre-trade risk check passed for {symbol}")
            return True, "Risk check passed"

        except Exception as e:
            self.logger.error(f"Error in pre-trade risk check: {e}")
            return False, f"Risk check error: {e}"

    async def _check_portfolio_limits(
        self, symbol: str, side: str, amount: float, price: float
    ) -> Tuple[bool, str]:
        """Check portfolio-level risk limits."""
        try:
            # Check daily loss limit
            performance = self.portfolio_manager.get_portfolio_performance()

            if performance.get("daily_loss", 0) >= self.risk_limits.max_daily_loss:
                return (
                    False,
                    f"Daily loss limit exceeded: {performance.get('daily_loss', 0):.2f}%",
                )

            # Check maximum drawdown
            if performance.get("max_drawdown", 0) >= self.risk_limits.max_drawdown:
                return (
                    False,
                    f"Maximum drawdown exceeded: {performance.get('max_drawdown', 0):.2f}%",
                )

            # Check portfolio risk (simplified - would use VaR in production)
            total_position_value = sum(
                pos.market_value()
                for pos in self.portfolio_manager.get_positions().values()
            )

            portfolio_value = self.portfolio_manager.get_total_balance()
            if portfolio_value > 0:
                portfolio_risk = (total_position_value / portfolio_value) * 100
                if portfolio_risk >= self.risk_limits.max_portfolio_risk:
                    return (
                        False,
                        f"Portfolio risk limit exceeded: {portfolio_risk:.2f}%",
                    )

            return True, "Portfolio limits OK"

        except Exception as e:
            self.logger.error(f"Error checking portfolio limits: {e}")
            return False, f"Portfolio check error: {e}"

    async def _check_position_limits(
        self, symbol: str, side: str, amount: float, price: float
    ) -> Tuple[bool, str]:
        """Check position-level risk limits."""
        try:
            position_value = amount * price
            portfolio_value = self.portfolio_manager.get_total_balance()

            if portfolio_value > 0:
                position_size_pct = (position_value / portfolio_value) * 100

                # Check new position size
                if position_size_pct > self.risk_limits.max_position_size:
                    return (
                        False,
                        f"Position size limit exceeded: {position_size_pct:.2f}%",
                    )

                # Check total position size (including existing position)
                existing_position = self.portfolio_manager.get_position(symbol)
                if existing_position and not existing_position.is_flat():
                    total_value = existing_position.market_value() + position_value
                    total_size_pct = (total_value / portfolio_value) * 100

                    if total_size_pct > self.risk_limits.max_position_size:
                        return (
                            False,
                            f"Total position size limit exceeded: {total_size_pct:.2f}%",
                        )

            return True, "Position limits OK"

        except Exception as e:
            self.logger.error(f"Error checking position limits: {e}")
            return False, f"Position check error: {e}"

    async def _check_correlation_limits(
        self, symbol: str, amount: float, price: float
    ) -> Tuple[bool, str]:
        """Check correlation limits between positions."""
        try:
            # Get existing positions
            positions = self.portfolio_manager.get_positions()

            if not positions:
                return True, "No existing positions"

            # Check correlation with existing positions
            for existing_symbol, position in positions.items():
                if existing_symbol == symbol:
                    continue

                correlation = self._get_correlation(symbol, existing_symbol)

                if abs(correlation) > self.risk_limits.max_correlation:
                    return (
                        False,
                        f"High correlation with {existing_symbol}: {correlation:.2f}",
                    )

            return True, "Correlation limits OK"

        except Exception as e:
            self.logger.error(f"Error checking correlation limits: {e}")
            return True, "Correlation check skipped due to error"

    async def _check_trade_risk(
        self, symbol: str, amount: float, price: float, stop_loss: Optional[float]
    ) -> Tuple[bool, str]:
        """Check risk per trade limits."""
        try:
            portfolio_value = self.portfolio_manager.get_total_balance()

            if stop_loss and portfolio_value > 0:
                # Calculate risk based on stop loss
                risk_per_unit = abs(price - stop_loss)
                total_risk = risk_per_unit * amount
                risk_percentage = (total_risk / portfolio_value) * 100

                if risk_percentage > self.risk_limits.risk_per_trade:
                    return False, f"Trade risk exceeds limit: {risk_percentage:.2f}%"

            return True, "Trade risk OK"

        except Exception as e:
            self.logger.error(f"Error checking trade risk: {e}")
            return True, "Trade risk check skipped due to error"

    async def _check_leverage_limits(
        self, amount: float, price: float
    ) -> Tuple[bool, str]:
        """Check leverage limits."""
        try:
            position_value = amount * price
            portfolio_value = self.portfolio_manager.get_total_balance()

            # Calculate total position value including new position
            total_position_value = (
                sum(
                    pos.market_value()
                    for pos in self.portfolio_manager.get_positions().values()
                )
                + position_value
            )

            if portfolio_value > 0:
                leverage = total_position_value / portfolio_value

                if leverage > self.risk_limits.max_leverage:
                    return False, f"Leverage limit exceeded: {leverage:.2f}x"

            return True, "Leverage limits OK"

        except Exception as e:
            self.logger.error(f"Error checking leverage limits: {e}")
            return True, "Leverage check skipped due to error"

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        confidence: float = 1.0,
    ) -> float:
        """
        Calculate optimal position size based on risk management method.

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss_price: Stop loss price
            confidence: Signal confidence (0-1)

        Returns:
            Calculated position size
        """
        try:
            portfolio_value = self.portfolio_manager.get_total_balance()

            if portfolio_value <= 0:
                return 0.0

            if self.position_sizing_method == "fixed_risk":
                return self._calculate_fixed_risk_size(
                    symbol, entry_price, stop_loss_price, confidence, portfolio_value
                )
            elif self.position_sizing_method == "volatility":
                return self._calculate_volatility_size(
                    symbol, entry_price, confidence, portfolio_value
                )
            elif self.position_sizing_method == "kelly":
                return self._calculate_kelly_size(
                    symbol, entry_price, stop_loss_price, confidence, portfolio_value
                )
            else:
                return self._calculate_fixed_risk_size(
                    symbol, entry_price, stop_loss_price, confidence, portfolio_value
                )

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0

    def _calculate_fixed_risk_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: Optional[float],
        confidence: float,
        portfolio_value: float,
    ) -> float:
        """Calculate position size using fixed risk method."""
        try:
            if not stop_loss_price or stop_loss_price == entry_price:
                # Use maximum position size if no stop loss
                max_position_value = portfolio_value * (
                    self.risk_limits.max_position_size / 100
                )
                return max_position_value / entry_price

            # Calculate position size based on risk per trade
            risk_amount = (
                portfolio_value * (self.risk_limits.risk_per_trade / 100) * confidence
            )
            risk_per_unit = abs(entry_price - stop_loss_price)

            if risk_per_unit > 0:
                return risk_amount / risk_per_unit

            return 0.0

        except Exception as e:
            self.logger.error(f"Error in fixed risk calculation: {e}")
            return 0.0

    def _calculate_volatility_size(
        self, symbol: str, entry_price: float, confidence: float, portfolio_value: float
    ) -> float:
        """Calculate position size based on volatility (ATR-based)."""
        try:
            # Get recent price history for volatility calculation
            if (
                symbol not in self.price_history
                or len(self.price_history[symbol]) < self.volatility_lookback
            ):
                # Fallback to fixed risk if no history
                max_position_value = portfolio_value * (
                    self.risk_limits.max_position_size / 100
                )
                return max_position_value / entry_price

            prices = self.price_history[symbol][-self.volatility_lookback :]

            # Calculate Average True Range (simplified)
            volatility = self._calculate_atr(prices)

            if volatility > 0:
                # Risk amount based on volatility
                base_risk = portfolio_value * (self.risk_limits.risk_per_trade / 100)
                volatility_adjusted_risk = base_risk * confidence / volatility

                # Position size
                return min(
                    volatility_adjusted_risk / entry_price,
                    portfolio_value
                    * (self.risk_limits.max_position_size / 100)
                    / entry_price,
                )

            return 0.0

        except Exception as e:
            self.logger.error(f"Error in volatility calculation: {e}")
            return 0.0

    def _calculate_kelly_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: Optional[float],
        confidence: float,
        portfolio_value: float,
    ) -> float:
        """Calculate position size using Kelly Criterion (simplified)."""
        try:
            # This is a simplified Kelly calculation
            # In practice, you'd need historical win/loss data

            # Estimate win probability and average win/loss
            win_probability = 0.5 + (confidence * 0.2)  # 50-70% based on confidence
            average_win = 0.02  # 2% average win
            average_loss = 0.01  # 1% average loss

            # Kelly fraction
            kelly_fraction = (win_probability / average_loss) - (
                (1 - win_probability) / average_win
            )

            # Apply safety factor
            kelly_fraction = max(0, kelly_fraction * 0.25)  # Use 25% of Kelly

            # Cap at maximum position size
            max_fraction = self.risk_limits.max_position_size / 100
            kelly_fraction = min(kelly_fraction, max_fraction)

            return (portfolio_value * kelly_fraction) / entry_price

        except Exception as e:
            self.logger.error(f"Error in Kelly calculation: {e}")
            return 0.0

    def _calculate_atr(self, prices: List[float], period: int = 14) -> float:
        """Calculate Average True Range (simplified)."""
        try:
            if len(prices) < period + 1:
                return 0.0

            true_ranges = []
            for i in range(1, len(prices)):
                high_low = abs(prices[i] - prices[i - 1])
                true_ranges.append(high_low)

            if true_ranges:
                return sum(true_ranges[-period:]) / min(len(true_ranges), period)

            return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return 0.0

    def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols."""
        try:
            if (
                symbol1 in self.correlation_matrix
                and symbol2 in self.correlation_matrix[symbol1]
            ):
                return self.correlation_matrix[symbol1][symbol2]

            # Calculate correlation if both symbols have price history
            if (
                symbol1 in self.price_history
                and symbol2 in self.price_history
                and len(self.price_history[symbol1]) > 10
                and len(self.price_history[symbol2]) > 10
            ):

                prices1 = self.price_history[symbol1][-20:]
                prices2 = self.price_history[symbol2][-20:]

                # Simple correlation calculation
                correlation = self._calculate_correlation(prices1, prices2)

                # Cache correlation
                if symbol1 not in self.correlation_matrix:
                    self.correlation_matrix[symbol1] = {}
                if symbol2 not in self.correlation_matrix:
                    self.correlation_matrix[symbol2] = {}

                self.correlation_matrix[symbol1][symbol2] = correlation
                self.correlation_matrix[symbol2][symbol1] = correlation

                return correlation

            return 0.0  # No correlation if no data

        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return 0.0

    def _calculate_correlation(
        self, prices1: List[float], prices2: List[float]
    ) -> float:
        """Calculate correlation between two price series."""
        try:
            if len(prices1) != len(prices2) or len(prices1) < 2:
                return 0.0

            # Calculate returns
            returns1 = [
                (prices1[i] - prices1[i - 1]) / prices1[i - 1]
                for i in range(1, len(prices1))
            ]
            returns2 = [
                (prices2[i] - prices2[i - 1]) / prices2[i - 1]
                for i in range(1, len(prices2))
            ]

            if not returns1 or not returns2:
                return 0.0

            # Calculate correlation
            mean1 = sum(returns1) / len(returns1)
            mean2 = sum(returns2) / len(returns2)

            numerator = sum(
                (r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2)
            )

            sum_sq1 = sum((r1 - mean1) ** 2 for r1 in returns1)
            sum_sq2 = sum((r2 - mean2) ** 2 for r2 in returns2)

            denominator = (sum_sq1 * sum_sq2) ** 0.5

            if denominator == 0:
                return 0.0

            return numerator / denominator

        except Exception as e:
            self.logger.error(f"Error in correlation calculation: {e}")
            return 0.0

    async def monitor_positions(self, market_data: Dict[str, Dict[str, float]]):
        """
        Monitor existing positions for risk violations.

        Args:
            market_data: Current market data
        """
        try:
            positions = self.portfolio_manager.get_positions()

            for symbol, position in positions.items():
                if position.is_flat():
                    continue

                current_price = market_data.get(symbol, {}).get(
                    "price", position.market_price
                )

                # Update price history
                if symbol not in self.price_history:
                    self.price_history[symbol] = []

                self.price_history[symbol].append(current_price)

                # Keep only recent history
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol] = self.price_history[symbol][-100:]

                # Check stop losses
                await self._check_stop_losses(symbol, current_price, position)

                # Check trailing stops
                await self._update_trailing_stops(symbol, current_price, position)

                # Check position risk
                await self._check_position_risk(symbol, current_price, position)

            # Update portfolio-level risk metrics
            await self._update_portfolio_risk_metrics()

        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")

    async def _check_stop_losses(
        self, symbol: str, current_price: float, position: Position
    ):
        """Check and trigger stop losses."""
        try:
            if symbol not in self.stop_losses:
                return

            stop_loss_price = self.stop_losses[symbol]
            should_trigger = False

            if position.side == PositionSide.LONG and current_price <= stop_loss_price:
                should_trigger = True
            elif (
                position.side == PositionSide.SHORT and current_price >= stop_loss_price
            ):
                should_trigger = True

            if should_trigger:
                await self._trigger_stop_loss(symbol, position)

        except Exception as e:
            self.logger.error(f"Error checking stop loss for {symbol}: {e}")

    async def _update_trailing_stops(
        self, symbol: str, current_price: float, position: Position
    ):
        """Update trailing stop losses."""
        try:
            if symbol not in self.trailing_stops:
                return

            trailing_data = self.trailing_stops[symbol]
            trailing_distance = trailing_data.get("distance", 0.02)  # 2% default

            if position.side == PositionSide.LONG:
                # Update trailing stop for long position
                new_stop = current_price * (1 - trailing_distance)
                if (
                    "stop_price" not in trailing_data
                    or new_stop > trailing_data["stop_price"]
                ):
                    trailing_data["stop_price"] = new_stop
                    trailing_data["updated_at"] = datetime.now()

                # Check if trailing stop triggered
                if current_price <= trailing_data["stop_price"]:
                    await self._trigger_trailing_stop(symbol, position)

            elif position.side == PositionSide.SHORT:
                # Update trailing stop for short position
                new_stop = current_price * (1 + trailing_distance)
                if (
                    "stop_price" not in trailing_data
                    or new_stop < trailing_data["stop_price"]
                ):
                    trailing_data["stop_price"] = new_stop
                    trailing_data["updated_at"] = datetime.now()

                # Check if trailing stop triggered
                if current_price >= trailing_data["stop_price"]:
                    await self._trigger_trailing_stop(symbol, position)

        except Exception as e:
            self.logger.error(f"Error updating trailing stop for {symbol}: {e}")

    async def _check_position_risk(
        self, symbol: str, current_price: float, position: Position
    ):
        """Check individual position risk."""
        try:
            # Check position size
            position_value = position.market_value()
            portfolio_value = self.portfolio_manager.get_total_balance()

            if portfolio_value > 0:
                position_size_pct = (position_value / portfolio_value) * 100

                if position_size_pct > self.risk_limits.max_position_size:
                    await self._create_risk_alert(
                        RiskLevel.HIGH,
                        "position_size",
                        f"Position {symbol} exceeds size limit: {position_size_pct:.2f}%",
                    )

            # Check position P&L
            pnl_pct = position.pnl_percentage()

            if pnl_pct < -10:  # 10% loss threshold
                await self._create_risk_alert(
                    RiskLevel.MEDIUM,
                    "position_loss",
                    f"Position {symbol} has significant loss: {pnl_pct:.2f}%",
                )

        except Exception as e:
            self.logger.error(f"Error checking position risk for {symbol}: {e}")

    async def _update_portfolio_risk_metrics(self):
        """Update portfolio-level risk metrics."""
        try:
            performance = self.portfolio_manager.get_portfolio_performance()

            # Update drawdown
            self.current_drawdown = performance.get("max_drawdown", 0)

            # Check critical risk levels
            if self.current_drawdown >= self.risk_limits.max_drawdown:
                await self._create_risk_alert(
                    RiskLevel.CRITICAL,
                    "max_drawdown",
                    f"Maximum drawdown reached: {self.current_drawdown:.2f}%",
                )

                # Consider emergency stop
                await self._consider_emergency_stop()

            # Update daily P&L
            self.daily_pnl = performance.get("daily_loss", 0)

            if self.daily_pnl >= self.risk_limits.max_daily_loss:
                await self._create_risk_alert(
                    RiskLevel.HIGH,
                    "daily_loss",
                    f"Daily loss limit reached: {self.daily_pnl:.2f}%",
                )

        except Exception as e:
            self.logger.error(f"Error updating portfolio risk metrics: {e}")

    async def _trigger_stop_loss(self, symbol: str, position: Position):
        """Trigger stop loss for a position."""
        try:
            self.logger.warning(f"Stop loss triggered for {symbol}")

            # Create risk alert
            await self._create_risk_alert(
                RiskLevel.MEDIUM, "stop_loss", f"Stop loss triggered for {symbol}"
            )

            # Remove stop loss
            if symbol in self.stop_losses:
                del self.stop_losses[symbol]

            # Note: Actual order placement would be handled by order manager
            # This is just risk monitoring

        except Exception as e:
            self.logger.error(f"Error triggering stop loss for {symbol}: {e}")

    async def _trigger_trailing_stop(self, symbol: str, position: Position):
        """Trigger trailing stop for a position."""
        try:
            self.logger.warning(f"Trailing stop triggered for {symbol}")

            # Create risk alert
            await self._create_risk_alert(
                RiskLevel.MEDIUM,
                "trailing_stop",
                f"Trailing stop triggered for {symbol}",
            )

            # Remove trailing stop
            if symbol in self.trailing_stops:
                del self.trailing_stops[symbol]

        except Exception as e:
            self.logger.error(f"Error triggering trailing stop for {symbol}: {e}")

    async def _create_risk_alert(self, level: RiskLevel, alert_type: str, message: str):
        """Create a risk alert."""
        try:
            alert = RiskAlert(
                id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                level=level,
                type=alert_type,
                message=message,
                timestamp=datetime.now(),
            )

            self.active_alerts.append(alert)

            # Log alert
            if level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                self.logger.error(f"Risk Alert [{level.value.upper()}]: {message}")
            else:
                self.logger.warning(f"Risk Alert [{level.value.upper()}]: {message}")

            # Keep only recent alerts
            if len(self.active_alerts) > 100:
                self.active_alerts = self.active_alerts[-100:]

        except Exception as e:
            self.logger.error(f"Error creating risk alert: {e}")

    async def _consider_emergency_stop(self):
        """Consider activating emergency stop."""
        try:
            # Check if emergency stop should be activated
            critical_alerts = [
                a
                for a in self.active_alerts
                if a.level == RiskLevel.CRITICAL and not a.resolved
            ]

            if len(critical_alerts) >= 2:  # Multiple critical alerts
                self.emergency_stop = True
                self.logger.critical(
                    "EMERGENCY STOP ACTIVATED - Multiple critical risk violations"
                )

                await self._create_risk_alert(
                    RiskLevel.CRITICAL,
                    "emergency_stop",
                    "Emergency stop activated due to multiple critical risk violations",
                )

        except Exception as e:
            self.logger.error(f"Error considering emergency stop: {e}")

    def set_stop_loss(self, symbol: str, stop_price: float):
        """Set stop loss for a symbol."""
        self.stop_losses[symbol] = stop_price
        self.logger.info(f"Stop loss set for {symbol} at {stop_price}")

    def set_trailing_stop(self, symbol: str, distance: float):
        """Set trailing stop for a symbol."""
        self.trailing_stops[symbol] = {
            "distance": distance,
            "created_at": datetime.now(),
        }
        self.logger.info(
            f"Trailing stop set for {symbol} with {distance*100:.1f}% distance"
        )

    def remove_stop_loss(self, symbol: str):
        """Remove stop loss for a symbol."""
        if symbol in self.stop_losses:
            del self.stop_losses[symbol]
            self.logger.info(f"Stop loss removed for {symbol}")

    def remove_trailing_stop(self, symbol: str):
        """Remove trailing stop for a symbol."""
        if symbol in self.trailing_stops:
            del self.trailing_stops[symbol]
            self.logger.info(f"Trailing stop removed for {symbol}")

    def activate_emergency_stop(self):
        """Manually activate emergency stop."""
        self.emergency_stop = True
        self.logger.critical("EMERGENCY STOP MANUALLY ACTIVATED")

    def deactivate_emergency_stop(self):
        """Deactivate emergency stop."""
        self.emergency_stop = False
        self.logger.info("Emergency stop deactivated")

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive risk summary.

        Returns:
            Dictionary with risk metrics and alerts
        """
        try:
            active_alerts = [
                alert.to_dict() for alert in self.active_alerts if not alert.resolved
            ]

            return {
                "emergency_stop": self.emergency_stop,
                "current_drawdown": self.current_drawdown,
                "daily_pnl": self.daily_pnl,
                "portfolio_var": self.portfolio_var,
                "risk_limits": {
                    "max_portfolio_risk": self.risk_limits.max_portfolio_risk,
                    "max_position_size": self.risk_limits.max_position_size,
                    "max_daily_loss": self.risk_limits.max_daily_loss,
                    "max_drawdown": self.risk_limits.max_drawdown,
                    "risk_per_trade": self.risk_limits.risk_per_trade,
                },
                "active_alerts": active_alerts,
                "stop_losses": dict(self.stop_losses),
                "trailing_stops": {
                    k: v.get("distance", 0) for k, v in self.trailing_stops.items()
                },
                "position_count": len(self.portfolio_manager.get_positions()),
                "last_updated": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error generating risk summary: {e}")
            return {}

    def resolve_alert(self, alert_id: str):
        """Resolve a risk alert."""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                self.logger.info(f"Risk alert resolved: {alert_id}")
                break

    async def close(self):
        """Close risk manager."""
        try:
            # Clear all stops
            self.stop_losses.clear()
            self.trailing_stops.clear()

            self.logger.info("Risk manager closed")

        except Exception as e:
            self.logger.error(f"Error closing risk manager: {e}")
