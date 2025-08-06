"""
Technical indicators for trading strategies.
Uses TA-Lib for efficient calculation of technical indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union

try:
    import talib

    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False


class TechnicalIndicators:
    """
    Technical indicators calculator using TA-Lib and custom implementations.
    """

    @staticmethod
    def sma(
        data: Union[pd.Series, np.ndarray], period: int
    ) -> Union[pd.Series, np.ndarray]:
        """
        Simple Moving Average.

        Args:
            data: Price data
            period: Period for moving average

        Returns:
            Simple moving average
        """
        if TALIB_AVAILABLE and isinstance(data, np.ndarray):
            return talib.SMA(data, timeperiod=period)
        else:
            if isinstance(data, pd.Series):
                return data.rolling(window=period).mean()
            else:
                return pd.Series(data).rolling(window=period).mean().values

    @staticmethod
    def ema(
        data: Union[pd.Series, np.ndarray], period: int
    ) -> Union[pd.Series, np.ndarray]:
        """
        Exponential Moving Average.

        Args:
            data: Price data
            period: Period for moving average

        Returns:
            Exponential moving average
        """
        if TALIB_AVAILABLE and isinstance(data, np.ndarray):
            return talib.EMA(data, timeperiod=period)
        else:
            if isinstance(data, pd.Series):
                return data.ewm(span=period).mean()
            else:
                return pd.Series(data).ewm(span=period).mean().values

    @staticmethod
    def rsi(
        data: Union[pd.Series, np.ndarray], period: int = 14
    ) -> Union[pd.Series, np.ndarray]:
        """
        Relative Strength Index.

        Args:
            data: Price data
            period: Period for RSI calculation

        Returns:
            RSI values
        """
        if TALIB_AVAILABLE and isinstance(data, np.ndarray):
            return talib.RSI(data, timeperiod=period)
        else:
            # Manual RSI calculation
            if isinstance(data, np.ndarray):
                data = pd.Series(data)

            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.values if isinstance(data, np.ndarray) else rsi

    @staticmethod
    def macd(
        data: Union[pd.Series, np.ndarray],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Tuple[
        Union[pd.Series, np.ndarray],
        Union[pd.Series, np.ndarray],
        Union[pd.Series, np.ndarray],
    ]:
        """
        MACD (Moving Average Convergence Divergence).

        Args:
            data: Price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        if TALIB_AVAILABLE and isinstance(data, np.ndarray):
            macd_line, signal_line, histogram = talib.MACD(
                data,
                fastperiod=fast_period,
                slowperiod=slow_period,
                signalperiod=signal_period,
            )
            return macd_line, signal_line, histogram
        else:
            # Manual MACD calculation
            fast_ema = TechnicalIndicators.ema(data, fast_period)
            slow_ema = TechnicalIndicators.ema(data, slow_period)

            macd_line = fast_ema - slow_ema
            signal_line = TechnicalIndicators.ema(macd_line, signal_period)
            histogram = macd_line - signal_line

            return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        data: Union[pd.Series, np.ndarray], period: int = 20, std_dev: float = 2.0
    ) -> Tuple[
        Union[pd.Series, np.ndarray],
        Union[pd.Series, np.ndarray],
        Union[pd.Series, np.ndarray],
    ]:
        """
        Bollinger Bands.

        Args:
            data: Price data
            period: Period for moving average and standard deviation
            std_dev: Number of standard deviations for bands

        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        if TALIB_AVAILABLE and isinstance(data, np.ndarray):
            upper, middle, lower = talib.BBANDS(
                data, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev
            )
            return upper, middle, lower
        else:
            # Manual Bollinger Bands calculation
            if isinstance(data, np.ndarray):
                data = pd.Series(data)

            middle = data.rolling(window=period).mean()
            std = data.rolling(window=period).std()

            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)

            if isinstance(data, pd.Series):
                return upper, middle, lower
            else:
                return upper.values, middle.values, lower.values

    @staticmethod
    def stochastic(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        k_period: int = 14,
        d_period: int = 3,
    ) -> Tuple[Union[pd.Series, np.ndarray], Union[pd.Series, np.ndarray]]:
        """
        Stochastic Oscillator.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: Period for %K calculation
            d_period: Period for %D calculation

        Returns:
            Tuple of (%K, %D)
        """
        if TALIB_AVAILABLE and all(
            isinstance(x, np.ndarray) for x in [high, low, close]
        ):
            k_percent, d_percent = talib.STOCH(
                high,
                low,
                close,
                fastk_period=k_period,
                slowk_period=d_period,
                slowd_period=d_period,
            )
            return k_percent, d_percent
        else:
            # Manual Stochastic calculation
            if isinstance(high, np.ndarray):
                high = pd.Series(high)
                low = pd.Series(low)
                close = pd.Series(close)

            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()

            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()

            return k_percent, d_percent

    @staticmethod
    def atr(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        period: int = 14,
    ) -> Union[pd.Series, np.ndarray]:
        """
        Average True Range.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for ATR calculation

        Returns:
            ATR values
        """
        if TALIB_AVAILABLE and all(
            isinstance(x, np.ndarray) for x in [high, low, close]
        ):
            return talib.ATR(high, low, close, timeperiod=period)
        else:
            # Manual ATR calculation
            if isinstance(high, np.ndarray):
                high = pd.Series(high)
                low = pd.Series(low)
                close = pd.Series(close)

            prev_close = close.shift(1)

            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()

            return atr.values if isinstance(high, np.ndarray) else atr

    @staticmethod
    def adx(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        period: int = 14,
    ) -> Union[pd.Series, np.ndarray]:
        """
        Average Directional Index.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for ADX calculation

        Returns:
            ADX values
        """
        if TALIB_AVAILABLE and all(
            isinstance(x, np.ndarray) for x in [high, low, close]
        ):
            return talib.ADX(high, low, close, timeperiod=period)
        else:
            # Simplified ADX calculation (complex indicator)
            if isinstance(high, np.ndarray):
                high = pd.Series(high)
                low = pd.Series(low)
                close = pd.Series(close)

            # This is a simplified version - full ADX is more complex
            atr_val = TechnicalIndicators.atr(high, low, close, period)
            return atr_val

    @staticmethod
    def williams_r(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        period: int = 14,
    ) -> Union[pd.Series, np.ndarray]:
        """
        Williams %R.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for Williams %R calculation

        Returns:
            Williams %R values
        """
        if TALIB_AVAILABLE and all(
            isinstance(x, np.ndarray) for x in [high, low, close]
        ):
            return talib.WILLR(high, low, close, timeperiod=period)
        else:
            # Manual Williams %R calculation
            if isinstance(high, np.ndarray):
                high = pd.Series(high)
                low = pd.Series(low)
                close = pd.Series(close)

            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()

            williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))

            return williams_r.values if isinstance(high, np.ndarray) else williams_r

    @staticmethod
    def calculate_all_indicators(
        df: pd.DataFrame, price_col: str = "close", volume_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate all major technical indicators for a DataFrame.

        Args:
            df: DataFrame with OHLCV data
            price_col: Column name for price data
            volume_col: Column name for volume data (optional)

        Returns:
            DataFrame with all indicators added
        """
        result_df = df.copy()

        # Price data
        close = df[price_col].values
        high = df["high"].values if "high" in df.columns else close
        low = df["low"].values if "low" in df.columns else close

        # Moving Averages
        result_df["sma_20"] = TechnicalIndicators.sma(close, 20)
        result_df["sma_50"] = TechnicalIndicators.sma(close, 50)
        result_df["ema_12"] = TechnicalIndicators.ema(close, 12)
        result_df["ema_26"] = TechnicalIndicators.ema(close, 26)

        # RSI
        result_df["rsi"] = TechnicalIndicators.rsi(close, 14)

        # MACD
        macd, signal, histogram = TechnicalIndicators.macd(close)
        result_df["macd"] = macd
        result_df["macd_signal"] = signal
        result_df["macd_histogram"] = histogram

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(close)
        result_df["bb_upper"] = bb_upper
        result_df["bb_middle"] = bb_middle
        result_df["bb_lower"] = bb_lower

        # Stochastic
        stoch_k, stoch_d = TechnicalIndicators.stochastic(high, low, close)
        result_df["stoch_k"] = stoch_k
        result_df["stoch_d"] = stoch_d

        # ATR
        result_df["atr"] = TechnicalIndicators.atr(high, low, close)

        # Williams %R
        result_df["williams_r"] = TechnicalIndicators.williams_r(high, low, close)

        # Price change indicators
        result_df["price_change"] = df[price_col].pct_change()
        result_df["price_change_5"] = df[price_col].pct_change(5)

        # Volume indicators (if volume data available)
        if volume_col and volume_col in df.columns:
            result_df["volume_sma"] = TechnicalIndicators.sma(df[volume_col].values, 20)
            result_df["volume_ratio"] = df[volume_col] / result_df["volume_sma"]

        return result_df

    @staticmethod
    def detect_patterns(df: pd.DataFrame) -> Dict[str, List[int]]:
        """
        Detect common chart patterns.

        Args:
            df: DataFrame with OHLCV data and indicators

        Returns:
            Dictionary of pattern names and their occurrence indices
        """
        patterns = {
            "golden_cross": [],
            "death_cross": [],
            "bullish_divergence": [],
            "bearish_divergence": [],
            "breakout": [],
            "breakdown": [],
        }

        if "sma_20" not in df.columns or "sma_50" not in df.columns:
            return patterns

        # Golden Cross and Death Cross
        for i in range(1, len(df)):
            # Golden Cross: Short MA crosses above Long MA
            if (
                df["sma_20"].iloc[i] > df["sma_50"].iloc[i]
                and df["sma_20"].iloc[i - 1] <= df["sma_50"].iloc[i - 1]
            ):
                patterns["golden_cross"].append(i)

            # Death Cross: Short MA crosses below Long MA
            if (
                df["sma_20"].iloc[i] < df["sma_50"].iloc[i]
                and df["sma_20"].iloc[i - 1] >= df["sma_50"].iloc[i - 1]
            ):
                patterns["death_cross"].append(i)

        # Bollinger Band breakouts
        if "bb_upper" in df.columns and "bb_lower" in df.columns:
            for i in range(1, len(df)):
                # Breakout above upper band
                if (
                    df["close"].iloc[i] > df["bb_upper"].iloc[i]
                    and df["close"].iloc[i - 1] <= df["bb_upper"].iloc[i - 1]
                ):
                    patterns["breakout"].append(i)

                # Breakdown below lower band
                if (
                    df["close"].iloc[i] < df["bb_lower"].iloc[i]
                    and df["close"].iloc[i - 1] >= df["bb_lower"].iloc[i - 1]
                ):
                    patterns["breakdown"].append(i)

        return patterns
