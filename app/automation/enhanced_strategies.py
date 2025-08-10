"""
Enhanced Strategy Engine for Indian Stock Market
Comprehensive trading strategies with advanced technical analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Advanced technical indicators for Indian stock market analysis."""

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float], period: int = 20, std_dev: float = 2
    ) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands (upper, middle, lower)."""
        if len(prices) < period:
            current_price = prices[-1] if prices else 100
            return current_price * 1.02, current_price, current_price * 0.98

        recent_prices = prices[-period:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)

        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)

        return upper, sma, lower

    @staticmethod
    def calculate_macd(
        prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[float, float, float]:
        """Calculate MACD (macd, signal, histogram)."""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0

        # Calculate EMAs
        fast_ema = TechnicalIndicators._calculate_ema(prices, fast)
        slow_ema = TechnicalIndicators._calculate_ema(prices, slow)

        macd_line = fast_ema - slow_ema

        # For signal line, we'd need historical MACD values
        # Simplified version
        signal_line = macd_line * 0.8  # Approximation
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def _calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return np.mean(prices) if prices else 0

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    @staticmethod
    def calculate_vwap(prices: List[float], volumes: List[float]) -> float:
        """Calculate Volume Weighted Average Price."""
        if not prices or not volumes or len(prices) != len(volumes):
            return np.mean(prices) if prices else 0

        total_volume_price = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)

        return (
            total_volume_price / total_volume if total_volume > 0 else np.mean(prices)
        )

    @staticmethod
    def calculate_stochastic(
        highs: List[float], lows: List[float], closes: List[float], period: int = 14
    ) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator (%K, %D)."""
        if len(closes) < period:
            return 50.0, 50.0

        recent_highs = highs[-period:]
        recent_lows = lows[-period:]
        current_close = closes[-1]

        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)

        if highest_high == lowest_low:
            k_percent = 50.0
        else:
            k_percent = (
                (current_close - lowest_low) / (highest_high - lowest_low)
            ) * 100

        # Simplified %D calculation
        d_percent = k_percent * 0.9  # Approximation

        return k_percent, d_percent


class IndianStockStrategy:
    """Base class for Indian stock market strategies."""

    def __init__(self, name: str, parameters: Dict):
        self.name = name
        self.parameters = parameters
        self.indicators = TechnicalIndicators()

    def generate_signals(self, market_data: Dict) -> List[Dict]:
        """Generate trading signals. To be implemented by subclasses."""
        raise NotImplementedError

    def calculate_position_size(
        self, price: float, account_balance: float, risk_percentage: float = 0.02
    ) -> int:
        """Calculate position size based on risk management."""
        risk_amount = account_balance * risk_percentage
        position_value = risk_amount / 0.03  # Assuming 3% stop loss
        quantity = int(position_value / price)
        return max(1, quantity)


class RSIStrategy(IndianStockStrategy):
    """RSI-based strategy for Indian stocks."""

    def __init__(self, parameters: Dict = None):
        default_params = {
            "rsi_period": 14,
            "oversold_level": 30,
            "overbought_level": 70,
            "min_volume_ratio": 1.2,
        }
        params = {**default_params, **(parameters or {})}
        super().__init__("RSI_Strategy", params)

    def generate_signals(self, market_data: Dict) -> List[Dict]:
        """Generate RSI-based signals."""
        signals = []

        for symbol, data in market_data.items():
            try:
                prices = data.get("price_history", [data.get("close", 100)])
                current_price = prices[-1]
                volume_ratio = data.get("volume_ratio", 1.0)

                # Calculate RSI
                rsi = self.indicators.calculate_rsi(
                    prices, self.parameters["rsi_period"]
                )

                # Check for signals
                if (
                    rsi <= self.parameters["oversold_level"]
                    and volume_ratio >= self.parameters["min_volume_ratio"]
                ):

                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "price": current_price,
                            "quantity": self.calculate_position_size(
                                current_price, 50000
                            ),
                            "reason": f"RSI Oversold: {rsi:.1f}",
                            "strategy": self.name,
                            "confidence": self._calculate_confidence(rsi, "oversold"),
                            "stop_loss": current_price * 0.97,
                            "take_profit": current_price * 1.06,
                        }
                    )

                elif rsi >= self.parameters["overbought_level"]:
                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "SELL",
                            "price": current_price,
                            "quantity": 100,  # Will be adjusted based on position
                            "reason": f"RSI Overbought: {rsi:.1f}",
                            "strategy": self.name,
                            "confidence": self._calculate_confidence(rsi, "overbought"),
                        }
                    )

            except Exception as e:
                logger.error(f"Error generating RSI signal for {symbol}: {e}")

        return signals

    def _calculate_confidence(self, rsi: float, signal_type: str) -> float:
        """Calculate signal confidence based on RSI level."""
        if signal_type == "oversold":
            return min(100, (30 - rsi) * 3)  # Higher confidence for lower RSI
        else:  # overbought
            return min(100, (rsi - 70) * 3)  # Higher confidence for higher RSI


class MomentumStrategy(IndianStockStrategy):
    """Momentum-based breakout strategy."""

    def __init__(self, parameters: Dict = None):
        default_params = {
            "lookback_period": 20,
            "breakout_threshold": 0.02,  # 2% above high
            "volume_threshold": 1.5,
            "min_price": 50,  # Avoid penny stocks
        }
        params = {**default_params, **(parameters or {})}
        super().__init__("Momentum_Strategy", params)

    def generate_signals(self, market_data: Dict) -> List[Dict]:
        """Generate momentum breakout signals."""
        signals = []

        for symbol, data in market_data.items():
            try:
                prices = data.get("price_history", [data.get("close", 100)])
                current_price = prices[-1]
                volume_ratio = data.get("volume_ratio", 1.0)

                if current_price < self.parameters["min_price"]:
                    continue

                # Calculate 20-day high
                lookback_prices = prices[-self.parameters["lookback_period"] :]
                period_high = max(lookback_prices) if lookback_prices else current_price

                breakout_level = period_high * (
                    1 + self.parameters["breakout_threshold"]
                )

                # Check for breakout with volume
                if (
                    current_price >= breakout_level
                    and volume_ratio >= self.parameters["volume_threshold"]
                ):

                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "price": current_price,
                            "quantity": self.calculate_position_size(
                                current_price, 50000
                            ),
                            "reason": f"Momentum Breakout: {((current_price/period_high-1)*100):.1f}% above high",
                            "strategy": self.name,
                            "confidence": min(100, volume_ratio * 30),
                            "stop_loss": period_high * 0.98,  # Just below breakout
                            "take_profit": current_price * 1.08,
                        }
                    )

            except Exception as e:
                logger.error(f"Error generating momentum signal for {symbol}: {e}")

        return signals


class BollingerBandStrategy(IndianStockStrategy):
    """Bollinger Band mean reversion strategy."""

    def __init__(self, parameters: Dict = None):
        default_params = {
            "bb_period": 20,
            "bb_std_dev": 2,
            "rsi_filter": True,
            "rsi_oversold": 40,
            "rsi_overbought": 60,
        }
        params = {**default_params, **(parameters or {})}
        super().__init__("Bollinger_Band_Strategy", params)

    def generate_signals(self, market_data: Dict) -> List[Dict]:
        """Generate Bollinger Band signals."""
        signals = []

        for symbol, data in market_data.items():
            try:
                prices = data.get("price_history", [data.get("close", 100)])
                current_price = prices[-1]

                # Calculate Bollinger Bands
                bb_upper, bb_middle, bb_lower = (
                    self.indicators.calculate_bollinger_bands(
                        prices,
                        self.parameters["bb_period"],
                        self.parameters["bb_std_dev"],
                    )
                )

                # Optional RSI filter
                rsi = (
                    self.indicators.calculate_rsi(prices)
                    if self.parameters["rsi_filter"]
                    else 50
                )

                # Buy signal - price at lower band
                if current_price <= bb_lower and (
                    not self.parameters["rsi_filter"]
                    or rsi <= self.parameters["rsi_oversold"]
                ):

                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "price": current_price,
                            "quantity": self.calculate_position_size(
                                current_price, 50000
                            ),
                            "reason": f"BB Lower Band Touch (RSI: {rsi:.1f})",
                            "strategy": self.name,
                            "confidence": 70,
                            "stop_loss": bb_lower * 0.97,
                            "take_profit": bb_upper,
                        }
                    )

                # Sell signal - price at upper band
                elif current_price >= bb_upper and (
                    not self.parameters["rsi_filter"]
                    or rsi >= self.parameters["rsi_overbought"]
                ):

                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "SELL",
                            "price": current_price,
                            "quantity": 100,  # Will be adjusted based on position
                            "reason": f"BB Upper Band Touch (RSI: {rsi:.1f})",
                            "strategy": self.name,
                            "confidence": 70,
                        }
                    )

            except Exception as e:
                logger.error(f"Error generating BB signal for {symbol}: {e}")

        return signals


class VWAPStrategy(IndianStockStrategy):
    """VWAP-based intraday strategy."""

    def __init__(self, parameters: Dict = None):
        default_params = {
            "vwap_deviation_threshold": 0.01,  # 1% deviation
            "min_volume_surge": 1.3,
            "time_filter": True,  # Only trade during active hours
        }
        params = {**default_params, **(parameters or {})}
        super().__init__("VWAP_Strategy", params)

    def generate_signals(self, market_data: Dict) -> List[Dict]:
        """Generate VWAP-based signals."""
        signals = []

        # Check trading hours
        current_hour = datetime.now().hour
        if self.parameters["time_filter"] and (current_hour < 9 or current_hour > 15):
            return signals

        for symbol, data in market_data.items():
            try:
                prices = data.get("price_history", [data.get("close", 100)])
                volumes = data.get("volume_history", [1000] * len(prices))
                current_price = prices[-1]
                volume_ratio = data.get("volume_ratio", 1.0)

                # Calculate VWAP
                vwap = self.indicators.calculate_vwap(prices, volumes)
                deviation = (current_price - vwap) / vwap

                # Buy signal - price below VWAP with volume
                if (
                    deviation <= -self.parameters["vwap_deviation_threshold"]
                    and volume_ratio >= self.parameters["min_volume_surge"]
                ):

                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "price": current_price,
                            "quantity": self.calculate_position_size(
                                current_price, 50000, 0.015
                            ),  # Lower risk for intraday
                            "reason": f"Below VWAP: {deviation*100:.1f}%",
                            "strategy": self.name,
                            "confidence": min(
                                100, abs(deviation) * 200 + volume_ratio * 20
                            ),
                            "stop_loss": current_price
                            * 0.995,  # Tight stop for intraday
                            "take_profit": vwap * 1.005,  # Target back to VWAP
                        }
                    )

                # Sell signal - price above VWAP with volume
                elif (
                    deviation >= self.parameters["vwap_deviation_threshold"]
                    and volume_ratio >= self.parameters["min_volume_surge"]
                ):

                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "SELL",
                            "price": current_price,
                            "quantity": 100,  # Will be adjusted based on position
                            "reason": f"Above VWAP: {deviation*100:.1f}%",
                            "strategy": self.name,
                            "confidence": min(
                                100, abs(deviation) * 200 + volume_ratio * 20
                            ),
                        }
                    )

            except Exception as e:
                logger.error(f"Error generating VWAP signal for {symbol}: {e}")

        return signals


class MultiStrategyEngine:
    """Combines multiple strategies for comprehensive trading."""

    def __init__(self):
        self.strategies = [
            RSIStrategy(),
            MomentumStrategy(),
            BollingerBandStrategy(),
            VWAPStrategy(),
        ]
        self.strategy_weights = {
            "RSI_Strategy": 0.3,
            "Momentum_Strategy": 0.25,
            "Bollinger_Band_Strategy": 0.25,
            "VWAP_Strategy": 0.2,
        }

    def generate_comprehensive_signals(self, market_data: Dict) -> List[Dict]:
        """Generate signals from all strategies and consolidate."""
        all_signals = []

        # Get signals from each strategy
        for strategy in self.strategies:
            try:
                strategy_signals = strategy.generate_signals(market_data)
                for signal in strategy_signals:
                    signal["weight"] = self.strategy_weights.get(strategy.name, 0.2)
                    all_signals.append(signal)
            except Exception as e:
                logger.error(f"Error in strategy {strategy.name}: {e}")

        # Consolidate signals by symbol
        consolidated_signals = self._consolidate_signals(all_signals)

        return consolidated_signals

    def _consolidate_signals(self, all_signals: List[Dict]) -> List[Dict]:
        """Consolidate multiple signals for the same symbol."""
        symbol_signals = {}

        for signal in all_signals:
            symbol = signal["symbol"]
            action = signal["action"]
            key = f"{symbol}_{action}"

            if key not in symbol_signals:
                symbol_signals[key] = []
            symbol_signals[key].append(signal)

        consolidated = []

        for key, signals in symbol_signals.items():
            if len(signals) >= 2:  # At least 2 strategies agree
                # Calculate weighted confidence
                total_weight = sum(s["weight"] for s in signals)
                weighted_confidence = (
                    sum(s["confidence"] * s["weight"] for s in signals) / total_weight
                )

                # Use the signal with highest individual confidence as base
                best_signal = max(signals, key=lambda x: x["confidence"])
                best_signal["confidence"] = weighted_confidence
                best_signal["reason"] = (
                    f"Multi-Strategy: {', '.join([s['strategy'] for s in signals])}"
                )
                best_signal["strategy_count"] = len(signals)

                consolidated.append(best_signal)

        # Sort by confidence
        return sorted(consolidated, key=lambda x: x["confidence"], reverse=True)


# Export the strategy classes for use in the trading bot
ENHANCED_STRATEGY_MAP = {
    "rsi_strategy": RSIStrategy,
    "momentum_strategy": MomentumStrategy,
    "bollinger_band_strategy": BollingerBandStrategy,
    "vwap_strategy": VWAPStrategy,
    "multi_strategy": MultiStrategyEngine,
}
