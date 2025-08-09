import pandas as pd
import numpy as np
import ta
from flask import current_app


class BaseStrategy:
    def __init__(self, params=None):
        self.params = params or {}
        self.risk_controls = {
            "max_capital_per_trade": self.params.get(
                "max_capital_per_trade", 0.05
            ),  # 5% of capital
            "max_daily_trades": self.params.get("max_daily_trades", 10),
            "global_stop_loss_pct": self.params.get(
                "global_stop_loss_pct", 0.10
            ),  # 10% daily portfolio stop
        }

    def generate_signals(self, market_data):
        """
        Generates trading signals based on market data.
        Should return a list of signals, e.g., [{'symbol': 'RELIANCE', 'action': 'BUY', 'confidence': 0.8}]
        """
        raise NotImplementedError

    def backtest(self, historical_df, params=None):
        """
        Runs a backtest on historical data.
        Should return performance metrics.
        """
        if params:
            # Temporarily update params for backtest
            original_params = self.params.copy()
            self.params.update(params)

        try:
            # Initialize backtest variables
            initial_capital = 100000
            capital = initial_capital
            positions = {}
            trades = []
            equity_curve = []

            # Group data by symbol for processing
            symbols = (
                historical_df["symbol"].unique()
                if "symbol" in historical_df.columns
                else ["TEST"]
            )

            for i in range(len(historical_df)):
                current_date = (
                    historical_df.index[i]
                    if hasattr(historical_df.index, "__getitem__")
                    else i
                )

                # Prepare market data for this point in time
                market_data = {}
                for symbol in symbols:
                    symbol_data = (
                        historical_df[historical_df["symbol"] == symbol]
                        if "symbol" in historical_df.columns
                        else historical_df
                    )
                    market_data[symbol] = symbol_data.iloc[
                        : i + 1
                    ]  # Data up to current point

                # Generate signals
                signals = self.generate_signals(market_data)

                # Process signals
                for signal in signals:
                    if signal["action"] in ["BUY", "SELL"]:
                        symbol = signal["symbol"]
                        quantity = signal["quantity"]
                        price = market_data[symbol]["close"].iloc[-1]

                        if signal["action"] == "BUY":
                            cost = quantity * price
                            if capital >= cost:
                                capital -= cost
                                positions[symbol] = positions.get(symbol, 0) + quantity
                                trades.append(
                                    {
                                        "date": current_date,
                                        "symbol": symbol,
                                        "action": "BUY",
                                        "quantity": quantity,
                                        "price": price,
                                        "value": cost,
                                    }
                                )

                        elif (
                            signal["action"] == "SELL"
                            and symbol in positions
                            and positions[symbol] > 0
                        ):
                            sell_quantity = min(quantity, positions[symbol])
                            proceeds = sell_quantity * price
                            capital += proceeds
                            positions[symbol] -= sell_quantity
                            if positions[symbol] == 0:
                                del positions[symbol]
                            trades.append(
                                {
                                    "date": current_date,
                                    "symbol": symbol,
                                    "action": "SELL",
                                    "quantity": sell_quantity,
                                    "price": price,
                                    "value": proceeds,
                                }
                            )

                # Calculate portfolio value
                portfolio_value = capital
                for symbol, qty in positions.items():
                    if symbol in market_data and len(market_data[symbol]) > 0:
                        current_price = market_data[symbol]["close"].iloc[-1]
                        portfolio_value += qty * current_price

                equity_curve.append(portfolio_value)

            # Calculate performance metrics
            total_return = (
                (equity_curve[-1] - initial_capital) / initial_capital
                if equity_curve
                else 0
            )

            # Calculate additional metrics
            returns = (
                np.diff(equity_curve) / equity_curve[:-1]
                if len(equity_curve) > 1
                else [0]
            )
            avg_return = np.mean(returns) if returns else 0
            volatility = np.std(returns) if returns else 0
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0

            max_value = max(equity_curve) if equity_curve else initial_capital
            min_value = min(equity_curve) if equity_curve else initial_capital
            max_drawdown = (max_value - min_value) / max_value if max_value > 0 else 0

            metrics = {
                "initial_capital": initial_capital,
                "final_capital": equity_curve[-1] if equity_curve else initial_capital,
                "total_return": total_return,
                "total_trades": len(trades),
                "avg_return": avg_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "equity_curve": equity_curve,
                "trades": trades,
            }

            return metrics

        finally:
            # Restore original params
            if params:
                self.params = original_params


class MovingAverageCrossover(BaseStrategy):
    """Simple two-moving average crossover with stop-loss and take-profit."""

    def __init__(self, params=None):
        super().__init__(params)
        self.short_window = self.params.get("short_window", 10)
        self.long_window = self.params.get("long_window", 30)
        self.stop_loss_pct = self.params.get("stop_loss_pct", 0.02)  # 2%
        self.take_profit_pct = self.params.get("take_profit_pct", 0.04)  # 4%

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < self.long_window:
                continue

            # Calculate moving averages
            short_ma = data["close"].rolling(window=self.short_window).mean()
            long_ma = data["close"].rolling(window=self.long_window).mean()

            current_price = data["close"].iloc[-1]
            current_short_ma = short_ma.iloc[-1]
            current_long_ma = long_ma.iloc[-1]
            prev_short_ma = short_ma.iloc[-2]
            prev_long_ma = long_ma.iloc[-2]

            # Check for crossover
            if current_short_ma > current_long_ma and prev_short_ma <= prev_long_ma:
                # Bullish crossover
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": self._calculate_position_size(current_price),
                        "stop_loss": current_price * (1 - self.stop_loss_pct),
                        "take_profit": current_price * (1 + self.take_profit_pct),
                        "confidence": 0.7,
                        "reason": "MA crossover bullish",
                    }
                )
            elif current_short_ma < current_long_ma and prev_short_ma >= prev_long_ma:
                # Bearish crossover
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": self._calculate_position_size(current_price),
                        "stop_loss": current_price * (1 + self.stop_loss_pct),
                        "take_profit": current_price * (1 - self.take_profit_pct),
                        "confidence": 0.7,
                        "reason": "MA crossover bearish",
                    }
                )

        return signals

    def _calculate_position_size(self, price):
        """Calculate position size based on risk management"""
        # Simple position sizing: 5% of capital / price
        capital = 100000  # Mock capital, should come from user's account
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class MomentumBreakout(BaseStrategy):
    """Trade breakouts above X-day high with volume filter."""

    def __init__(self, params=None):
        super().__init__(params)
        self.lookback_period = self.params.get("lookback_period", 20)
        self.volume_threshold = self.params.get(
            "volume_threshold", 1.5
        )  # 1.5x avg volume
        self.stop_loss_pct = self.params.get("stop_loss_pct", 0.03)  # 3%

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < self.lookback_period + 1:
                continue

            # Calculate highest high in lookback period
            highest_high = data["high"].rolling(window=self.lookback_period).max()
            avg_volume = data["volume"].rolling(window=self.lookback_period).mean()

            current_price = data["close"].iloc[-1]
            current_high = data["high"].iloc[-1]
            current_volume = data["volume"].iloc[-1]
            prev_highest_high = highest_high.iloc[-2]
            avg_vol = avg_volume.iloc[-1]

            # Check for breakout with volume confirmation
            if (
                current_high > prev_highest_high
                and current_volume > avg_vol * self.volume_threshold
            ):
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": self._calculate_position_size(current_price),
                        "stop_loss": prev_highest_high * (1 - self.stop_loss_pct),
                        "confidence": 0.8,
                        "reason": "Momentum breakout with volume",
                    }
                )

        return signals

    def _calculate_position_size(self, price):
        capital = 100000
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class MeanReversionRSI(BaseStrategy):
    """Buy when RSI < 30, sell when RSI > 70 with trailing SL."""

    def __init__(self, params=None):
        super().__init__(params)
        self.rsi_period = self.params.get("rsi_period", 14)
        self.oversold_threshold = self.params.get("oversold_threshold", 30)
        self.overbought_threshold = self.params.get("overbought_threshold", 70)
        self.stop_loss_pct = self.params.get("stop_loss_pct", 0.02)

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < self.rsi_period + 1:
                continue

            # Calculate RSI using ta library
            rsi = ta.momentum.RSIIndicator(
                close=data["close"], window=self.rsi_period
            ).rsi()

            current_rsi = rsi.iloc[-1]
            current_price = data["close"].iloc[-1]

            # Generate signals based on RSI levels
            if current_rsi < self.oversold_threshold:
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": self._calculate_position_size(current_price),
                        "stop_loss": current_price * (1 - self.stop_loss_pct),
                        "confidence": 0.6,
                        "reason": f"RSI oversold: {current_rsi:.2f}",
                    }
                )
            elif current_rsi > self.overbought_threshold:
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": self._calculate_position_size(current_price),
                        "stop_loss": current_price * (1 + self.stop_loss_pct),
                        "confidence": 0.6,
                        "reason": f"RSI overbought: {current_rsi:.2f}",
                    }
                )

        return signals

    def _calculate_position_size(self, price):
        capital = 100000
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class VwapIntradayScalper(BaseStrategy):
    """Intraday trades relative to VWAP."""

    def __init__(self, params=None):
        super().__init__(params)
        self.vwap_period = self.params.get("vwap_period", 20)
        self.deviation_threshold = self.params.get("deviation_threshold", 0.005)  # 0.5%

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < self.vwap_period:
                continue

            # Calculate VWAP
            typical_price = (data["high"] + data["low"] + data["close"]) / 3
            vwap = (typical_price * data["volume"]).rolling(
                window=self.vwap_period
            ).sum() / data["volume"].rolling(window=self.vwap_period).sum()

            current_price = data["close"].iloc[-1]
            current_vwap = vwap.iloc[-1]

            price_deviation = (current_price - current_vwap) / current_vwap

            # Generate signals based on VWAP deviation
            if price_deviation < -self.deviation_threshold:  # Price below VWAP
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": self._calculate_position_size(current_price),
                        "confidence": 0.5,
                        "reason": f"Price below VWAP by {abs(price_deviation):.2%}",
                    }
                )
            elif price_deviation > self.deviation_threshold:  # Price above VWAP
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": self._calculate_position_size(current_price),
                        "confidence": 0.5,
                        "reason": f"Price above VWAP by {price_deviation:.2%}",
                    }
                )

        return signals

    def _calculate_position_size(self, price):
        capital = 100000
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class PairTradingCointegration(BaseStrategy):
    """Market-neutral pairs with z-score threshold."""

    def __init__(self, params=None):
        super().__init__(params)
        self.pairs = self.params.get("pairs", [("RELIANCE", "TCS")])
        self.lookback_period = self.params.get("lookback_period", 30)
        self.z_score_threshold = self.params.get("z_score_threshold", 2.0)

    def generate_signals(self, market_data):
        signals = []

        for pair in self.pairs:
            symbol1, symbol2 = pair
            if symbol1 not in market_data or symbol2 not in market_data:
                continue

            data1 = market_data[symbol1]
            data2 = market_data[symbol2]

            if len(data1) < self.lookback_period or len(data2) < self.lookback_period:
                continue

            # Calculate price ratio and z-score
            ratio = data1["close"] / data2["close"]
            ratio_mean = ratio.rolling(window=self.lookback_period).mean()
            ratio_std = ratio.rolling(window=self.lookback_period).std()
            z_score = (ratio - ratio_mean) / ratio_std

            current_z_score = z_score.iloc[-1]

            if current_z_score > self.z_score_threshold:
                # Ratio is high - sell symbol1, buy symbol2
                signals.extend(
                    [
                        {
                            "symbol": symbol1,
                            "action": "SELL",
                            "quantity": self._calculate_position_size(
                                data1["close"].iloc[-1]
                            ),
                            "confidence": 0.6,
                            "reason": f"Pair trade: {symbol1} overvalued vs {symbol2}",
                        },
                        {
                            "symbol": symbol2,
                            "action": "BUY",
                            "quantity": self._calculate_position_size(
                                data2["close"].iloc[-1]
                            ),
                            "confidence": 0.6,
                            "reason": f"Pair trade: {symbol2} undervalued vs {symbol1}",
                        },
                    ]
                )
            elif current_z_score < -self.z_score_threshold:
                # Ratio is low - buy symbol1, sell symbol2
                signals.extend(
                    [
                        {
                            "symbol": symbol1,
                            "action": "BUY",
                            "quantity": self._calculate_position_size(
                                data1["close"].iloc[-1]
                            ),
                            "confidence": 0.6,
                            "reason": f"Pair trade: {symbol1} undervalued vs {symbol2}",
                        },
                        {
                            "symbol": symbol2,
                            "action": "SELL",
                            "quantity": self._calculate_position_size(
                                data2["close"].iloc[-1]
                            ),
                            "confidence": 0.6,
                            "reason": f"Pair trade: {symbol2} overvalued vs {symbol1}",
                        },
                    ]
                )

        return signals

    def _calculate_position_size(self, price):
        capital = 100000
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class BollingerBandReversal(BaseStrategy):
    """Buy near lower band, sell near upper band."""

    def __init__(self, params=None):
        super().__init__(params)
        self.period = self.params.get("period", 20)
        self.std_dev = self.params.get("std_dev", 2)

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < self.period:
                continue

            # Calculate Bollinger Bands
            bb = ta.volatility.BollingerBands(
                close=data["close"], window=self.period, window_dev=self.std_dev
            )

            upper_band = bb.bollinger_hband()
            lower_band = bb.bollinger_lband()
            middle_band = bb.bollinger_mavg()

            current_price = data["close"].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_middle = middle_band.iloc[-1]

            # Generate signals based on band position
            if current_price <= current_lower:  # Near lower band - oversold
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": self._calculate_position_size(current_price),
                        "take_profit": current_middle,
                        "confidence": 0.7,
                        "reason": "Price at lower Bollinger Band",
                    }
                )
            elif current_price >= current_upper:  # Near upper band - overbought
                signals.append(
                    {
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": self._calculate_position_size(current_price),
                        "take_profit": current_middle,
                        "confidence": 0.7,
                        "reason": "Price at upper Bollinger Band",
                    }
                )

        return signals

    def _calculate_position_size(self, price):
        capital = 100000
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class TrendFollowingADX(BaseStrategy):
    """Only act if ADX > threshold."""

    def __init__(self, params=None):
        super().__init__(params)
        self.adx_period = self.params.get("adx_period", 14)
        self.adx_threshold = self.params.get("adx_threshold", 25)
        self.ma_period = self.params.get("ma_period", 20)

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < max(self.adx_period, self.ma_period) + 1:
                continue

            # Calculate ADX
            adx_indicator = ta.trend.ADXIndicator(
                high=data["high"],
                low=data["low"],
                close=data["close"],
                window=self.adx_period,
            )
            adx = adx_indicator.adx()

            # Calculate moving average for trend direction
            ma = data["close"].rolling(window=self.ma_period).mean()

            current_adx = adx.iloc[-1]
            current_price = data["close"].iloc[-1]
            current_ma = ma.iloc[-1]

            # Only trade if ADX indicates strong trend
            if current_adx > self.adx_threshold:
                if current_price > current_ma:
                    # Uptrend confirmed by ADX
                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "quantity": self._calculate_position_size(current_price),
                            "confidence": min(
                                0.9, current_adx / 50
                            ),  # Higher ADX = higher confidence
                            "reason": f"Strong uptrend confirmed by ADX: {current_adx:.1f}",
                        }
                    )
                elif current_price < current_ma:
                    # Downtrend confirmed by ADX
                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "SELL",
                            "quantity": self._calculate_position_size(current_price),
                            "confidence": min(0.9, current_adx / 50),
                            "reason": f"Strong downtrend confirmed by ADX: {current_adx:.1f}",
                        }
                    )

        return signals

    def _calculate_position_size(self, price):
        capital = 100000
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class VolumeSpikeReversal(BaseStrategy):
    """Detect abnormal volume then trade short-term reversal."""

    def __init__(self, params=None):
        super().__init__(params)
        self.volume_period = self.params.get("volume_period", 20)
        self.volume_threshold = self.params.get("volume_threshold", 2.0)  # 2x average
        self.price_change_threshold = self.params.get(
            "price_change_threshold", 0.02
        )  # 2%

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < self.volume_period + 1:
                continue

            # Calculate average volume
            avg_volume = data["volume"].rolling(window=self.volume_period).mean()

            current_volume = data["volume"].iloc[-1]
            avg_vol = avg_volume.iloc[-1]
            current_price = data["close"].iloc[-1]
            prev_price = data["close"].iloc[-2]

            price_change = (current_price - prev_price) / prev_price

            # Check for volume spike
            if current_volume > avg_vol * self.volume_threshold:
                # Volume spike detected, look for reversal opportunity
                if price_change < -self.price_change_threshold:
                    # Sharp price drop with high volume - potential reversal up
                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "quantity": self._calculate_position_size(current_price),
                            "confidence": 0.6,
                            "reason": f"Volume spike reversal: {current_volume/avg_vol:.1f}x avg volume",
                        }
                    )
                elif price_change > self.price_change_threshold:
                    # Sharp price rise with high volume - potential reversal down
                    signals.append(
                        {
                            "symbol": symbol,
                            "action": "SELL",
                            "quantity": self._calculate_position_size(current_price),
                            "confidence": 0.6,
                            "reason": f"Volume spike reversal: {current_volume/avg_vol:.1f}x avg volume",
                        }
                    )

        return signals

    def _calculate_position_size(self, price):
        capital = 100000
        max_capital_per_trade = capital * self.risk_controls["max_capital_per_trade"]
        return int(max_capital_per_trade / price)


class BreakoutATRStop(BaseStrategy):
    """Use ATR to set SL & position sizing."""

    def __init__(self, params=None):
        super().__init__(params)
        self.atr_period = self.params.get("atr_period", 14)
        self.breakout_period = self.params.get("breakout_period", 20)
        self.atr_multiplier = self.params.get("atr_multiplier", 2.0)

    def generate_signals(self, market_data):
        signals = []

        for symbol, data in market_data.items():
            if len(data) < max(self.atr_period, self.breakout_period) + 1:
                continue

            # Calculate ATR
            atr_indicator = ta.volatility.AverageTrueRange(
                high=data["high"],
                low=data["low"],
                close=data["close"],
                window=self.atr_period,
            )
            atr = atr_indicator.average_true_range()

            # Calculate breakout levels
            highest_high = data["high"].rolling(window=self.breakout_period).max()
            lowest_low = data["low"].rolling(window=self.breakout_period).min()

            current_price = data["close"].iloc[-1]
            current_atr = atr.iloc[-1]
            prev_highest = highest_high.iloc[-2]
            prev_lowest = lowest_low.iloc[-2]

            # Check for breakouts
            if current_price > prev_highest:
                # Upside breakout
                stop_loss = current_price - (current_atr * self.atr_multiplier)
                position_size = self._calculate_atr_position_size(
                    current_price, current_atr
                )

                signals.append(
                    {
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": position_size,
                        "stop_loss": stop_loss,
                        "confidence": 0.7,
                        "reason": f"ATR breakout above {prev_highest:.2f}",
                    }
                )
            elif current_price < prev_lowest:
                # Downside breakout
                stop_loss = current_price + (current_atr * self.atr_multiplier)
                position_size = self._calculate_atr_position_size(
                    current_price, current_atr
                )

                signals.append(
                    {
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": position_size,
                        "stop_loss": stop_loss,
                        "confidence": 0.7,
                        "reason": f"ATR breakout below {prev_lowest:.2f}",
                    }
                )

        return signals

    def _calculate_atr_position_size(self, price, atr):
        """Calculate position size based on ATR for risk management"""
        capital = 100000
        risk_per_trade = capital * self.risk_controls["max_capital_per_trade"]

        # Risk per share = ATR * multiplier
        risk_per_share = atr * self.atr_multiplier

        # Position size = Risk per trade / Risk per share
        if risk_per_share > 0:
            position_size = int(risk_per_trade / risk_per_share)
            return max(1, position_size)  # At least 1 share
        else:
            return int(risk_per_trade / price)  # Fallback calculation


class NewsSentimentGate(BaseStrategy):
    """Strategy that requires a news sentiment feed (stubbed)."""

    def __init__(self, params=None):
        super().__init__(params)
        self.news_connector_ready = False  # Gating mechanism

    def generate_signals(self, market_data):
        if not self.news_connector_ready:
            # TODO: Log a warning that the connector is not available
            return [{"action": "HOLD", "reason": "News connector not available"}]
        # TODO: Implement sentiment-based logic
        return [{"action": "HOLD"}]


# Mapping for the strategy engine
STRATEGY_MAP = {
    "Moving Average Crossover": MovingAverageCrossover,
    "Momentum Breakout": MomentumBreakout,
    "Mean Reversion (RSI-based)": MeanReversionRSI,
    "VWAP Intraday Scalper": VwapIntradayScalper,
    "Pair Trading (Cointegration)": PairTradingCointegration,
    "Bollinger Band Reversal": BollingerBandReversal,
    "Trend Following (ADX filter)": TrendFollowingADX,
    "Volume Spike Reversals": VolumeSpikeReversal,
    "Breakout with ATR-based SL": BreakoutATRStop,
    "News Sentiment Gate": NewsSentimentGate,
}
