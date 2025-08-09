import pandas as pd

class BaseStrategy:
    def __init__(self, params=None):
        self.params = params or {}
        self.risk_controls = {
            'max_capital_per_trade': self.params.get('max_capital_per_trade', 0.05), # 5% of capital
            'max_daily_trades': self.params.get('max_daily_trades', 10),
            'global_stop_loss_pct': self.params.get('global_stop_loss_pct', 0.10) # 10% daily portfolio stop
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
        raise NotImplementedError

class MovingAverageCrossover(BaseStrategy):
    """Simple two-moving average crossover with stop-loss and take-profit."""
    def generate_signals(self, market_data):
        # TODO: Implement signal generation logic
        # e.g., if short_ma > long_ma -> BUY
        return [{'action': 'HOLD'}]

class MomentumBreakout(BaseStrategy):
    """Trade breakouts above X-day high with volume filter."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class MeanReversionRSI(BaseStrategy):
    """Buy when RSI < 30, sell when RSI > 70 with trailing SL."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class VwapIntradayScalper(BaseStrategy):
    """Intraday trades relative to VWAP."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class PairTradingCointegration(BaseStrategy):
    """Market-neutral pairs with z-score threshold."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class BollingerBandReversal(BaseStrategy):
    """Buy near lower band, sell near upper band."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class TrendFollowingADX(BaseStrategy):
    """Only act if ADX > threshold."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class VolumeSpikeReversal(BaseStrategy):
    """Detect abnormal volume then trade short-term reversal."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class BreakoutATRStop(BaseStrategy):
    """Use ATR to set SL & position sizing."""
    def generate_signals(self, market_data):
        return [{'action': 'HOLD'}]

class NewsSentimentGate(BaseStrategy):
    """Strategy that requires a news sentiment feed (stubbed)."""
    def __init__(self, params=None):
        super().__init__(params)
        self.news_connector_ready = False # Gating mechanism

    def generate_signals(self, market_data):
        if not self.news_connector_ready:
            # TODO: Log a warning that the connector is not available
            return [{'action': 'HOLD', 'reason': 'News connector not available'}]
        # TODO: Implement sentiment-based logic
        return [{'action': 'HOLD'}]

# Mapping for the strategy engine
STRATEGY_MAP = {
    'Moving Average Crossover': MovingAverageCrossover,
    'Momentum Breakout': MomentumBreakout,
    'Mean Reversion (RSI-based)': MeanReversionRSI,
    'VWAP Intraday Scalper': VwapIntradayScalper,
    'Pair Trading (Cointegration)': PairTradingCointegration,
    'Bollinger Band Reversal': BollingerBandReversal,
    'Trend Following (ADX filter)': TrendFollowingADX,
    'Volume Spike Reversals': VolumeSpikeReversal,
    'Breakout with ATR-based SL': BreakoutATRStop,
    'News Sentiment Gate': NewsSentimentGate,
}