"""
Moving Average Crossover Trading Strategy.

This strategy generates buy signals when a fast moving average crosses above
a slow moving average, and sell signals when the fast MA crosses below the slow MA.
"""

from typing import Dict, List, Any, Optional
import pandas as pd

from .base_strategy import BaseStrategy, TradeSignal
from ..utils.indicators import TechnicalIndicators


class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover strategy implementation.

    Strategy Logic:
    - BUY when fast MA crosses above slow MA
    - SELL when fast MA crosses below slow MA
    - Additional filters: volume, trend strength
    """

    def __init__(self, strategy_config: Dict[str, Any], config):
        """
        Initialize Moving Average Crossover strategy.

        Args:
            strategy_config: Strategy configuration
            config: Global configuration
        """
        # Set default parameters
        default_config = {
            "fast_ma": 20,
            "slow_ma": 50,
            "ma_type": "sma",  # sma, ema
            "min_volume": 1000000,  # Minimum 24h volume
            "volume_filter": True,
            "trend_filter": True,
            "signal_threshold": 0.01,  # 1% minimum price difference
            "stop_loss_pct": 0.02,  # 2% stop loss
            "take_profit_pct": 0.06,  # 6% take profit
            "min_signal_interval": 3600,  # 1 hour between signals
        }

        # Update with provided config
        default_config.update(strategy_config)

        super().__init__(default_config, config)

        # Strategy state
        self.last_fast_ma = None
        self.last_slow_ma = None
        self.trend_direction = None
        self.crossover_count = 0

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Moving Average Crossover"

    @property
    def description(self) -> str:
        """Return strategy description."""
        return (
            f"MA Crossover strategy using {self.strategy_config['fast_ma']}-period "
            f"and {self.strategy_config['slow_ma']}-period {self.strategy_config['ma_type'].upper()}"
        )

    @property
    def required_indicators(self) -> List[str]:
        """Return required indicators."""
        return ["sma", "ema", "volume", "atr"]

    def get_min_data_points(self) -> int:
        """Get minimum data points needed."""
        return max(self.strategy_config["slow_ma"] + 10, 60)

    async def generate_signals(self, market_data: pd.DataFrame) -> List[TradeSignal]:
        """
        Generate trading signals based on moving average crossover.

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
                    f"Insufficient data for strategy: {len(df)} candles"
                )
                return signals

            # Get latest data
            current_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]

            # Calculate moving averages
            fast_ma_current, slow_ma_current = self._calculate_moving_averages(df)
            fast_ma_previous, slow_ma_previous = self._calculate_moving_averages(
                df.iloc[:-1]
            )

            if fast_ma_current is None or slow_ma_current is None:
                return signals

            # Check for crossover
            signal = self._check_crossover(
                fast_ma_current,
                slow_ma_current,
                fast_ma_previous,
                slow_ma_previous,
                current_candle,
                df,
            )

            if signal:
                signals.append(signal)

            # Update strategy state
            self.last_fast_ma = fast_ma_current
            self.last_slow_ma = slow_ma_current

        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")

        return signals

    def _calculate_moving_averages(self, df: pd.DataFrame) -> tuple:
        """
        Calculate fast and slow moving averages.

        Args:
            df: DataFrame with market data

        Returns:
            Tuple of (fast_ma, slow_ma)
        """
        try:
            if len(df) < self.strategy_config["slow_ma"]:
                return None, None

            fast_period = self.strategy_config["fast_ma"]
            slow_period = self.strategy_config["slow_ma"]
            ma_type = self.strategy_config["ma_type"]

            close_prices = df["close"].values

            if ma_type == "ema":
                fast_ma = TechnicalIndicators.ema(close_prices, fast_period)
                slow_ma = TechnicalIndicators.ema(close_prices, slow_period)
            else:  # Default to SMA
                fast_ma = TechnicalIndicators.sma(close_prices, fast_period)
                slow_ma = TechnicalIndicators.sma(close_prices, slow_period)

            # Get latest values
            if hasattr(fast_ma, "iloc"):
                fast_ma_value = fast_ma.iloc[-1]
                slow_ma_value = slow_ma.iloc[-1]
            else:
                fast_ma_value = fast_ma[-1]
                slow_ma_value = slow_ma[-1]

            return fast_ma_value, slow_ma_value

        except Exception as e:
            self.logger.error(f"Error calculating moving averages: {e}")
            return None, None

    def _check_crossover(
        self,
        fast_ma_current: float,
        slow_ma_current: float,
        fast_ma_previous: float,
        slow_ma_previous: float,
        current_candle: pd.Series,
        df: pd.DataFrame,
    ) -> Optional[TradeSignal]:
        """
        Check for moving average crossover and generate signal.

        Args:
            fast_ma_current: Current fast MA value
            slow_ma_current: Current slow MA value
            fast_ma_previous: Previous fast MA value
            slow_ma_previous: Previous slow MA value
            current_candle: Current price candle
            df: Full DataFrame with indicators

        Returns:
            TradeSignal if crossover detected, None otherwise
        """
        try:
            current_price = current_candle["close"]
            symbol = self.config.trading.symbol

            # Check for golden cross (bullish signal)
            if (
                fast_ma_current > slow_ma_current
                and fast_ma_previous <= slow_ma_previous
            ):

                # Validate signal with filters
                if self._validate_buy_signal(current_candle, df):
                    signal_strength = self._calculate_signal_strength(
                        fast_ma_current, slow_ma_current, current_candle, df, "buy"
                    )

                    self.crossover_count += 1

                    return self.create_signal(
                        symbol=symbol,
                        side="buy",
                        strength=signal_strength,
                        price=current_price,
                        reason=f"Golden Cross: Fast MA ({fast_ma_current:.4f}) > Slow MA ({slow_ma_current:.4f})",
                        metadata={
                            "fast_ma": fast_ma_current,
                            "slow_ma": slow_ma_current,
                            "crossover_type": "golden_cross",
                            "crossover_count": self.crossover_count,
                        },
                    )

            # Check for death cross (bearish signal)
            elif (
                fast_ma_current < slow_ma_current
                and fast_ma_previous >= slow_ma_previous
            ):

                # Validate signal with filters
                if self._validate_sell_signal(current_candle, df):
                    signal_strength = self._calculate_signal_strength(
                        fast_ma_current, slow_ma_current, current_candle, df, "sell"
                    )

                    self.crossover_count += 1

                    return self.create_signal(
                        symbol=symbol,
                        side="sell",
                        strength=signal_strength,
                        price=current_price,
                        reason=f"Death Cross: Fast MA ({fast_ma_current:.4f}) < Slow MA ({slow_ma_current:.4f})",
                        metadata={
                            "fast_ma": fast_ma_current,
                            "slow_ma": slow_ma_current,
                            "crossover_type": "death_cross",
                            "crossover_count": self.crossover_count,
                        },
                    )

            return None

        except Exception as e:
            self.logger.error(f"Error checking crossover: {e}")
            return None

    def _validate_buy_signal(self, current_candle: pd.Series, df: pd.DataFrame) -> bool:
        """
        Validate buy signal with additional filters.

        Args:
            current_candle: Current price candle
            df: DataFrame with indicators

        Returns:
            True if signal is valid
        """
        try:
            # Volume filter
            if self.strategy_config.get("volume_filter", True):
                if not self._check_volume_filter(current_candle, df):
                    self.logger.debug("Buy signal rejected: volume filter")
                    return False

            # Trend filter
            if self.strategy_config.get("trend_filter", True):
                if not self._check_trend_filter(df, "buy"):
                    self.logger.debug("Buy signal rejected: trend filter")
                    return False

            # Price momentum filter
            if not self._check_momentum_filter(df, "buy"):
                self.logger.debug("Buy signal rejected: momentum filter")
                return False

            # Signal threshold filter
            if not self._check_signal_threshold(current_candle):
                self.logger.debug("Buy signal rejected: signal threshold")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating buy signal: {e}")
            return False

    def _validate_sell_signal(
        self, current_candle: pd.Series, df: pd.DataFrame
    ) -> bool:
        """
        Validate sell signal with additional filters.

        Args:
            current_candle: Current price candle
            df: DataFrame with indicators

        Returns:
            True if signal is valid
        """
        try:
            # Only generate sell signals if we have open positions
            if self.position_count <= 0:
                self.logger.debug("Sell signal rejected: no open positions")
                return False

            # Volume filter
            if self.strategy_config.get("volume_filter", True):
                if not self._check_volume_filter(current_candle, df):
                    self.logger.debug("Sell signal rejected: volume filter")
                    return False

            # Trend filter
            if self.strategy_config.get("trend_filter", True):
                if not self._check_trend_filter(df, "sell"):
                    self.logger.debug("Sell signal rejected: trend filter")
                    return False

            # Price momentum filter
            if not self._check_momentum_filter(df, "sell"):
                self.logger.debug("Sell signal rejected: momentum filter")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating sell signal: {e}")
            return False

    def _check_volume_filter(self, current_candle: pd.Series, df: pd.DataFrame) -> bool:
        """
        Check volume filter.

        Args:
            current_candle: Current price candle
            df: DataFrame with indicators

        Returns:
            True if volume is sufficient
        """
        try:
            current_volume = current_candle["volume"]
            min_volume = self.strategy_config.get("min_volume", 0)

            if min_volume > 0 and current_volume < min_volume:
                return False

            # Check volume vs average
            if "volume_sma" in df.columns:
                avg_volume = df["volume_sma"].iloc[-1]
                if not pd.isna(avg_volume) and current_volume < avg_volume * 0.5:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking volume filter: {e}")
            return True  # Default to allowing signal

    def _check_trend_filter(self, df: pd.DataFrame, side: str) -> bool:
        """
        Check trend filter using longer-term moving average.

        Args:
            df: DataFrame with indicators
            side: Trade side ('buy' or 'sell')

        Returns:
            True if trend is favorable
        """
        try:
            if len(df) < 200:
                return True  # Skip filter if insufficient data

            current_price = df["close"].iloc[-1]

            # Use 200-period SMA as trend filter
            if "sma_200" in df.columns:
                trend_ma = df["sma_200"].iloc[-1]
            else:
                # Calculate 200-period SMA
                trend_ma = df["close"].rolling(window=200).mean().iloc[-1]

            if pd.isna(trend_ma):
                return True

            if side == "buy":
                return current_price > trend_ma  # Only buy in uptrend
            else:
                return current_price < trend_ma  # Only sell in downtrend

        except Exception as e:
            self.logger.error(f"Error checking trend filter: {e}")
            return True

    def _check_momentum_filter(self, df: pd.DataFrame, side: str) -> bool:
        """
        Check price momentum filter using RSI.

        Args:
            df: DataFrame with indicators
            side: Trade side ('buy' or 'sell')

        Returns:
            True if momentum is favorable
        """
        try:
            if "rsi" not in df.columns:
                return True

            current_rsi = df["rsi"].iloc[-1]

            if pd.isna(current_rsi):
                return True

            if side == "buy":
                # Avoid buying when extremely overbought
                return current_rsi < 80
            else:
                # Avoid selling when extremely oversold
                return current_rsi > 20

        except Exception as e:
            self.logger.error(f"Error checking momentum filter: {e}")
            return True

    def _check_signal_threshold(self, current_candle: pd.Series) -> bool:
        """
        Check if price movement meets minimum threshold.

        Args:
            current_candle: Current price candle

        Returns:
            True if threshold is met
        """
        try:
            if self.last_fast_ma is None or self.last_slow_ma is None:
                return True

            current_price = current_candle["close"]
            threshold = self.strategy_config.get("signal_threshold", 0.01)

            # Calculate price change since last signal
            price_change = abs(
                current_price - (self.last_fast_ma + self.last_slow_ma) / 2
            )
            price_change_pct = price_change / current_price

            return price_change_pct >= threshold

        except Exception as e:
            self.logger.error(f"Error checking signal threshold: {e}")
            return True

    def _calculate_signal_strength(
        self,
        fast_ma: float,
        slow_ma: float,
        current_candle: pd.Series,
        df: pd.DataFrame,
        side: str,
    ) -> float:
        """
        Calculate signal strength based on various factors.

        Args:
            fast_ma: Fast moving average value
            slow_ma: Slow moving average value
            current_candle: Current price candle
            df: DataFrame with indicators
            side: Trade side

        Returns:
            Signal strength (0.0 to 1.0)
        """
        try:
            strength = 0.5  # Base strength

            # MA separation factor (larger separation = stronger signal)
            ma_diff = abs(fast_ma - slow_ma) / slow_ma
            strength += min(ma_diff * 2, 0.3)  # Max 0.3 boost

            # Volume factor
            if "volume_sma" in df.columns:
                current_volume = current_candle["volume"]
                avg_volume = df["volume_sma"].iloc[-1]

                if not pd.isna(avg_volume) and avg_volume > 0:
                    volume_ratio = current_volume / avg_volume
                    volume_boost = min((volume_ratio - 1) * 0.1, 0.2)  # Max 0.2 boost
                    strength += max(volume_boost, 0)

            # Trend alignment factor
            if len(df) >= 200:
                current_price = current_candle["close"]
                long_ma = df["close"].rolling(window=200).mean().iloc[-1]

                if not pd.isna(long_ma):
                    if side == "buy" and current_price > long_ma:
                        strength += 0.1
                    elif side == "sell" and current_price < long_ma:
                        strength += 0.1

            # Clamp between 0.1 and 1.0
            return max(0.1, min(1.0, strength))

        except Exception as e:
            self.logger.error(f"Error calculating signal strength: {e}")
            return 0.5

    async def handle_order_filled(self, order: Dict[str, Any]):
        """Handle order filled event for MA crossover strategy."""
        try:
            side = order.get("side")
            symbol = order.get("symbol")
            price = order.get("price", 0)
            amount = order.get("amount", 0)

            self.logger.info(
                f"MA Crossover order filled: {side} {amount} {symbol} @ {price}"
            )

            # Update trend direction based on filled order
            if side == "buy":
                self.trend_direction = "bullish"
            elif side == "sell":
                self.trend_direction = "bearish"

        except Exception as e:
            self.logger.error(f"Error handling order filled: {e}")

    async def handle_trade_closed(self, trade: Dict[str, Any]):
        """Handle trade closed event for MA crossover strategy."""
        try:
            profit_loss = trade.get("profit_loss", 0)
            symbol = trade.get("symbol")

            self.logger.info(
                f"MA Crossover trade closed for {symbol}: P&L = {profit_loss:.4f}"
            )

            # Reset trend direction when trade is closed
            self.trend_direction = None

        except Exception as e:
            self.logger.error(f"Error handling trade closed: {e}")

    def get_strategy_state(self) -> Dict[str, Any]:
        """
        Get current strategy state.

        Returns:
            Dictionary with strategy state information
        """
        return {
            "last_fast_ma": self.last_fast_ma,
            "last_slow_ma": self.last_slow_ma,
            "trend_direction": self.trend_direction,
            "crossover_count": self.crossover_count,
            "position_count": self.position_count,
        }
