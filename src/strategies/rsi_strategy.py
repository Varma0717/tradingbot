"""
RSI (Relative Strength Index) Trading Strategy.

This strategy generates trading signals based on RSI overbought/oversold conditions
with additional filters for trend and volume confirmation.
"""

from typing import Dict, List, Any, Optional
import pandas as pd

from .base_strategy import BaseStrategy, TradeSignal
from ..utils.indicators import TechnicalIndicators


class RSIStrategy(BaseStrategy):
    """
    RSI trading strategy implementation.

    Strategy Logic:
    - BUY when RSI is oversold (< oversold_threshold) and shows bullish divergence
    - SELL when RSI is overbought (> overbought_threshold) and shows bearish divergence
    - Additional filters: volume, trend, momentum confirmation
    """

    def __init__(self, strategy_config: Dict[str, Any], config):
        """
        Initialize RSI strategy.

        Args:
            strategy_config: Strategy configuration
            config: Global configuration
        """
        # Set default parameters
        default_config = {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70,
            "rsi_ma_period": 9,
            "min_rsi_divergence": 5,
            "volume_filter": True,
            "trend_filter": True,
            "divergence_filter": True,
            "min_volume_ratio": 0.8,  # Minimum volume vs average
            "confirmation_periods": 2,  # Periods to wait for confirmation
            "stop_loss_pct": 0.025,  # 2.5% stop loss
            "take_profit_pct": 0.075,  # 7.5% take profit
            "min_signal_interval": 1800,  # 30 minutes between signals
        }

        # Update with provided config
        default_config.update(strategy_config)

        super().__init__(default_config, config)

        # Strategy state
        self.rsi_history = []
        self.price_history = []
        self.last_rsi = None
        self.pending_signals = []
        self.divergence_points = []

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "RSI Strategy"

    @property
    def description(self) -> str:
        """Return strategy description."""
        return (
            f"RSI strategy with {self.strategy_config['rsi_period']}-period RSI, "
            f"oversold < {self.strategy_config['oversold']}, "
            f"overbought > {self.strategy_config['overbought']}"
        )

    @property
    def required_indicators(self) -> List[str]:
        """Return required indicators."""
        return ["rsi", "sma", "volume", "atr", "macd"]

    def get_min_data_points(self) -> int:
        """Get minimum data points needed."""
        return max(self.strategy_config["rsi_period"] * 3, 50)

    async def generate_signals(self, market_data: pd.DataFrame) -> List[TradeSignal]:
        """
        Generate trading signals based on RSI analysis.

        Args:
            market_data: DataFrame with OHLCV data

        Returns:
            List of trade signals
        """
        signals = []

        try:
            # Validate data
            if not self.validate_data(market_data):
                return signals

            # Calculate indicators
            df = self.calculate_indicators(market_data)

            if len(df) < self.get_min_data_points():
                self.logger.warning(
                    f"Insufficient data for RSI strategy: {len(df)} candles"
                )
                return signals

            # Update RSI and price history
            self._update_history(df)

            # Get current RSI
            current_rsi = df["rsi"].iloc[-1]
            current_price = df["close"].iloc[-1]

            if pd.isna(current_rsi):
                return signals

            # Check for RSI signals
            buy_signal = self._check_buy_conditions(df, current_rsi, current_price)
            sell_signal = self._check_sell_conditions(df, current_rsi, current_price)

            if buy_signal:
                signals.append(buy_signal)

            if sell_signal:
                signals.append(sell_signal)

            # Update strategy state
            self.last_rsi = current_rsi

        except Exception as e:
            self.logger.error(f"Error generating RSI signals: {e}")

        return signals

    def _update_history(self, df: pd.DataFrame):
        """
        Update RSI and price history for divergence analysis.

        Args:
            df: DataFrame with indicators
        """
        try:
            max_history = 100  # Keep last 100 periods

            current_rsi = df["rsi"].iloc[-1]
            current_price = df["close"].iloc[-1]

            if not pd.isna(current_rsi):
                self.rsi_history.append(current_rsi)
                self.price_history.append(current_price)

                # Trim history
                if len(self.rsi_history) > max_history:
                    self.rsi_history = self.rsi_history[-max_history:]
                    self.price_history = self.price_history[-max_history:]

        except Exception as e:
            self.logger.error(f"Error updating history: {e}")

    def _check_buy_conditions(
        self, df: pd.DataFrame, current_rsi: float, current_price: float
    ) -> Optional[TradeSignal]:
        """
        Check conditions for buy signal.

        Args:
            df: DataFrame with indicators
            current_rsi: Current RSI value
            current_price: Current price

        Returns:
            TradeSignal if conditions met, None otherwise
        """
        try:
            oversold_threshold = self.strategy_config["oversold"]
            symbol = self.config.trading.symbol

            # Basic RSI oversold condition
            if current_rsi > oversold_threshold:
                return None

            # Additional validations
            if not self._validate_buy_signal(df, current_rsi, current_price):
                return None

            # Calculate signal strength
            signal_strength = self._calculate_buy_strength(
                df, current_rsi, current_price
            )

            # Check for bullish divergence
            divergence_strength = 0.0
            if self.strategy_config.get("divergence_filter", True):
                divergence_strength = self._check_bullish_divergence()

            # Combine base strength with divergence
            total_strength = min(1.0, signal_strength + divergence_strength * 0.3)

            reason = f"RSI Oversold: {current_rsi:.2f} < {oversold_threshold}"
            if divergence_strength > 0:
                reason += f" + Bullish Divergence"

            return self.create_signal(
                symbol=symbol,
                side="buy",
                strength=total_strength,
                price=current_price,
                reason=reason,
                metadata={
                    "rsi": current_rsi,
                    "rsi_threshold": oversold_threshold,
                    "divergence_strength": divergence_strength,
                    "signal_type": "rsi_oversold",
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking buy conditions: {e}")
            return None

    def _check_sell_conditions(
        self, df: pd.DataFrame, current_rsi: float, current_price: float
    ) -> Optional[TradeSignal]:
        """
        Check conditions for sell signal.

        Args:
            df: DataFrame with indicators
            current_rsi: Current RSI value
            current_price: Current price

        Returns:
            TradeSignal if conditions met, None otherwise
        """
        try:
            overbought_threshold = self.strategy_config["overbought"]
            symbol = self.config.trading.symbol

            # Basic RSI overbought condition
            if current_rsi < overbought_threshold:
                return None

            # Only sell if we have positions
            if self.position_count <= 0:
                return None

            # Additional validations
            if not self._validate_sell_signal(df, current_rsi, current_price):
                return None

            # Calculate signal strength
            signal_strength = self._calculate_sell_strength(
                df, current_rsi, current_price
            )

            # Check for bearish divergence
            divergence_strength = 0.0
            if self.strategy_config.get("divergence_filter", True):
                divergence_strength = self._check_bearish_divergence()

            # Combine base strength with divergence
            total_strength = min(1.0, signal_strength + divergence_strength * 0.3)

            reason = f"RSI Overbought: {current_rsi:.2f} > {overbought_threshold}"
            if divergence_strength > 0:
                reason += f" + Bearish Divergence"

            return self.create_signal(
                symbol=symbol,
                side="sell",
                strength=total_strength,
                price=current_price,
                reason=reason,
                metadata={
                    "rsi": current_rsi,
                    "rsi_threshold": overbought_threshold,
                    "divergence_strength": divergence_strength,
                    "signal_type": "rsi_overbought",
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking sell conditions: {e}")
            return None

    def _validate_buy_signal(
        self, df: pd.DataFrame, current_rsi: float, current_price: float
    ) -> bool:
        """
        Validate buy signal with additional filters.

        Args:
            df: DataFrame with indicators
            current_rsi: Current RSI value
            current_price: Current price

        Returns:
            True if signal is valid
        """
        try:
            # Volume filter
            if self.strategy_config.get("volume_filter", True):
                if not self._check_volume_confirmation(df, "buy"):
                    self.logger.debug("Buy signal rejected: volume filter")
                    return False

            # Trend filter
            if self.strategy_config.get("trend_filter", True):
                if not self._check_trend_alignment(df, "buy"):
                    self.logger.debug("Buy signal rejected: trend filter")
                    return False

            # RSI momentum filter (RSI should be recovering)
            if not self._check_rsi_momentum(df, "buy"):
                self.logger.debug("Buy signal rejected: RSI momentum")
                return False

            # MACD confirmation
            if not self._check_macd_confirmation(df, "buy"):
                self.logger.debug("Buy signal rejected: MACD confirmation")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating buy signal: {e}")
            return False

    def _validate_sell_signal(
        self, df: pd.DataFrame, current_rsi: float, current_price: float
    ) -> bool:
        """
        Validate sell signal with additional filters.

        Args:
            df: DataFrame with indicators
            current_rsi: Current RSI value
            current_price: Current price

        Returns:
            True if signal is valid
        """
        try:
            # Volume filter
            if self.strategy_config.get("volume_filter", True):
                if not self._check_volume_confirmation(df, "sell"):
                    self.logger.debug("Sell signal rejected: volume filter")
                    return False

            # Trend filter
            if self.strategy_config.get("trend_filter", True):
                if not self._check_trend_alignment(df, "sell"):
                    self.logger.debug("Sell signal rejected: trend filter")
                    return False

            # RSI momentum filter (RSI should be declining)
            if not self._check_rsi_momentum(df, "sell"):
                self.logger.debug("Sell signal rejected: RSI momentum")
                return False

            # MACD confirmation
            if not self._check_macd_confirmation(df, "sell"):
                self.logger.debug("Sell signal rejected: MACD confirmation")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating sell signal: {e}")
            return False

    def _check_volume_confirmation(self, df: pd.DataFrame, side: str) -> bool:
        """
        Check volume confirmation for signal.

        Args:
            df: DataFrame with indicators
            side: Trade side

        Returns:
            True if volume confirms signal
        """
        try:
            if "volume_sma" not in df.columns:
                return True  # Skip if no volume data

            current_volume = df["volume"].iloc[-1]
            avg_volume = df["volume_sma"].iloc[-1]

            if pd.isna(avg_volume) or avg_volume == 0:
                return True

            volume_ratio = current_volume / avg_volume
            min_ratio = self.strategy_config.get("min_volume_ratio", 0.8)

            return volume_ratio >= min_ratio

        except Exception as e:
            self.logger.error(f"Error checking volume confirmation: {e}")
            return True

    def _check_trend_alignment(self, df: pd.DataFrame, side: str) -> bool:
        """
        Check if signal aligns with overall trend.

        Args:
            df: DataFrame with indicators
            side: Trade side

        Returns:
            True if aligned with trend
        """
        try:
            if len(df) < 50:
                return True

            current_price = df["close"].iloc[-1]
            sma_50 = df["close"].rolling(window=50).mean().iloc[-1]

            if pd.isna(sma_50):
                return True

            if side == "buy":
                return current_price >= sma_50 * 0.98  # Allow slight below
            else:
                return current_price <= sma_50 * 1.02  # Allow slight above

        except Exception as e:
            self.logger.error(f"Error checking trend alignment: {e}")
            return True

    def _check_rsi_momentum(self, df: pd.DataFrame, side: str) -> bool:
        """
        Check RSI momentum direction.

        Args:
            df: DataFrame with indicators
            side: Trade side

        Returns:
            True if RSI momentum is favorable
        """
        try:
            if len(df) < 3:
                return True

            rsi_current = df["rsi"].iloc[-1]
            rsi_previous = df["rsi"].iloc[-2]

            if pd.isna(rsi_current) or pd.isna(rsi_previous):
                return True

            if side == "buy":
                # RSI should be recovering from oversold
                return rsi_current > rsi_previous
            else:
                # RSI should be declining from overbought
                return rsi_current < rsi_previous

        except Exception as e:
            self.logger.error(f"Error checking RSI momentum: {e}")
            return True

    def _check_macd_confirmation(self, df: pd.DataFrame, side: str) -> bool:
        """
        Check MACD confirmation for signal.

        Args:
            df: DataFrame with indicators
            side: Trade side

        Returns:
            True if MACD confirms signal
        """
        try:
            if "macd" not in df.columns or "macd_signal" not in df.columns:
                return True

            macd = df["macd"].iloc[-1]
            macd_signal = df["macd_signal"].iloc[-1]

            if pd.isna(macd) or pd.isna(macd_signal):
                return True

            if side == "buy":
                # MACD should be above signal line or converging
                return macd >= macd_signal * 0.95
            else:
                # MACD should be below signal line or diverging
                return macd <= macd_signal * 1.05

        except Exception as e:
            self.logger.error(f"Error checking MACD confirmation: {e}")
            return True

    def _check_bullish_divergence(self) -> float:
        """
        Check for bullish RSI-price divergence.

        Returns:
            Divergence strength (0.0 to 1.0)
        """
        try:
            if len(self.rsi_history) < 20 or len(self.price_history) < 20:
                return 0.0

            # Look for recent lows in both RSI and price
            recent_periods = 20
            rsi_recent = self.rsi_history[-recent_periods:]
            price_recent = self.price_history[-recent_periods:]

            # Find local minimums
            rsi_low_idx = rsi_recent.index(min(rsi_recent))
            price_low_idx = price_recent.index(min(price_recent))

            # Check if there's a previous low to compare
            if rsi_low_idx < 10 or price_low_idx < 10:
                return 0.0

            # Compare current low with previous low
            prev_rsi_low = min(rsi_recent[:rsi_low_idx])
            prev_price_low = min(price_recent[:price_low_idx])

            current_rsi_low = rsi_recent[rsi_low_idx]
            current_price_low = price_recent[price_low_idx]

            # Bullish divergence: price makes lower low but RSI makes higher low
            if current_price_low < prev_price_low and current_rsi_low > prev_rsi_low:
                # Calculate divergence strength
                rsi_diff = (current_rsi_low - prev_rsi_low) / prev_rsi_low
                price_diff = (prev_price_low - current_price_low) / prev_price_low

                strength = min(1.0, (rsi_diff + price_diff) * 5)
                return max(0.0, strength)

            return 0.0

        except Exception as e:
            self.logger.error(f"Error checking bullish divergence: {e}")
            return 0.0

    def _check_bearish_divergence(self) -> float:
        """
        Check for bearish RSI-price divergence.

        Returns:
            Divergence strength (0.0 to 1.0)
        """
        try:
            if len(self.rsi_history) < 20 or len(self.price_history) < 20:
                return 0.0

            # Look for recent highs in both RSI and price
            recent_periods = 20
            rsi_recent = self.rsi_history[-recent_periods:]
            price_recent = self.price_history[-recent_periods:]

            # Find local maximums
            rsi_high_idx = rsi_recent.index(max(rsi_recent))
            price_high_idx = price_recent.index(max(price_recent))

            # Check if there's a previous high to compare
            if rsi_high_idx < 10 or price_high_idx < 10:
                return 0.0

            # Compare current high with previous high
            prev_rsi_high = max(rsi_recent[:rsi_high_idx])
            prev_price_high = max(price_recent[:price_high_idx])

            current_rsi_high = rsi_recent[rsi_high_idx]
            current_price_high = price_recent[price_high_idx]

            # Bearish divergence: price makes higher high but RSI makes lower high
            if (
                current_price_high > prev_price_high
                and current_rsi_high < prev_rsi_high
            ):
                # Calculate divergence strength
                rsi_diff = (prev_rsi_high - current_rsi_high) / prev_rsi_high
                price_diff = (current_price_high - prev_price_high) / prev_price_high

                strength = min(1.0, (rsi_diff + price_diff) * 5)
                return max(0.0, strength)

            return 0.0

        except Exception as e:
            self.logger.error(f"Error checking bearish divergence: {e}")
            return 0.0

    def _calculate_buy_strength(
        self, df: pd.DataFrame, current_rsi: float, current_price: float
    ) -> float:
        """
        Calculate buy signal strength.

        Args:
            df: DataFrame with indicators
            current_rsi: Current RSI value
            current_price: Current price

        Returns:
            Signal strength (0.0 to 1.0)
        """
        try:
            oversold_threshold = self.strategy_config["oversold"]

            # Base strength from RSI level
            rsi_strength = (oversold_threshold - current_rsi) / oversold_threshold
            base_strength = max(0.3, min(0.8, rsi_strength))

            # Volume boost
            volume_boost = 0.0
            if "volume_ratio" in df.columns:
                volume_ratio = df["volume_ratio"].iloc[-1]
                if not pd.isna(volume_ratio) and volume_ratio > 1.0:
                    volume_boost = min(0.1, (volume_ratio - 1.0) * 0.05)

            # Trend alignment boost
            trend_boost = 0.0
            if len(df) >= 20:
                sma_20 = df["close"].rolling(window=20).mean().iloc[-1]
                if not pd.isna(sma_20) and current_price > sma_20:
                    trend_boost = 0.1

            total_strength = base_strength + volume_boost + trend_boost
            return max(0.1, min(1.0, total_strength))

        except Exception as e:
            self.logger.error(f"Error calculating buy strength: {e}")
            return 0.5

    def _calculate_sell_strength(
        self, df: pd.DataFrame, current_rsi: float, current_price: float
    ) -> float:
        """
        Calculate sell signal strength.

        Args:
            df: DataFrame with indicators
            current_rsi: Current RSI value
            current_price: Current price

        Returns:
            Signal strength (0.0 to 1.0)
        """
        try:
            overbought_threshold = self.strategy_config["overbought"]

            # Base strength from RSI level
            rsi_strength = (current_rsi - overbought_threshold) / (
                100 - overbought_threshold
            )
            base_strength = max(0.3, min(0.8, rsi_strength))

            # Volume boost
            volume_boost = 0.0
            if "volume_ratio" in df.columns:
                volume_ratio = df["volume_ratio"].iloc[-1]
                if not pd.isna(volume_ratio) and volume_ratio > 1.0:
                    volume_boost = min(0.1, (volume_ratio - 1.0) * 0.05)

            # Trend alignment boost
            trend_boost = 0.0
            if len(df) >= 20:
                sma_20 = df["close"].rolling(window=20).mean().iloc[-1]
                if not pd.isna(sma_20) and current_price < sma_20:
                    trend_boost = 0.1

            total_strength = base_strength + volume_boost + trend_boost
            return max(0.1, min(1.0, total_strength))

        except Exception as e:
            self.logger.error(f"Error calculating sell strength: {e}")
            return 0.5

    async def handle_order_filled(self, order: Dict[str, Any]):
        """Handle order filled event for RSI strategy."""
        try:
            side = order.get("side")
            symbol = order.get("symbol")
            price = order.get("price", 0)
            amount = order.get("amount", 0)

            self.logger.info(
                f"RSI strategy order filled: {side} {amount} {symbol} @ {price}"
            )

        except Exception as e:
            self.logger.error(f"Error handling order filled: {e}")

    async def handle_trade_closed(self, trade: Dict[str, Any]):
        """Handle trade closed event for RSI strategy."""
        try:
            profit_loss = trade.get("profit_loss", 0)
            symbol = trade.get("symbol")

            self.logger.info(
                f"RSI strategy trade closed for {symbol}: P&L = {profit_loss:.4f}"
            )

        except Exception as e:
            self.logger.error(f"Error handling trade closed: {e}")

    def get_strategy_state(self) -> Dict[str, Any]:
        """
        Get current strategy state.

        Returns:
            Dictionary with strategy state information
        """
        return {
            "last_rsi": self.last_rsi,
            "rsi_history_length": len(self.rsi_history),
            "price_history_length": len(self.price_history),
            "position_count": self.position_count,
            "divergence_points": len(self.divergence_points),
        }
