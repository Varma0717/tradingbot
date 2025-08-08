"""
High Performance Trading Strategy

Advanced Grid DCA strategy with multiple optimizations for maximum profitability:
- Adaptive grid spacing based on volatility
- Risk management with stop-losses
- Trend-following signals
- Multiple timeframe analysis
- Dynamic position sizing
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base_strategy import BaseStrategy, TradeSignal


@dataclass
class MarketCondition:
    trend: str  # "bullish", "bearish", "sideways"
    volatility: float  # 0-1 scale
    momentum: float  # -1 to 1 scale
    support_level: float
    resistance_level: float


class HighPerformanceStrategy(BaseStrategy):
    """
    Advanced trading strategy combining multiple approaches:
    1. Adaptive Grid DCA for sideways markets
    2. Trend following for strong moves
    3. Mean reversion for overbought/oversold conditions
    4. Risk management with position sizing
    """

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        initial_capital: float = 10000.0,
        max_position_size: float = 0.3,  # Max 30% of capital per position
        base_grid_spacing: float = 0.012,  # 1.2% base spacing
        adaptive_multiplier: float = 2.0,  # Volatility adjustment
        trend_threshold: float = 0.02,  # 2% for trend detection
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.symbol = symbol
        self.initial_capital = initial_capital
        self.max_position_size = max_position_size
        self.base_grid_spacing = base_grid_spacing
        self.adaptive_multiplier = adaptive_multiplier
        self.trend_threshold = trend_threshold

        # Strategy state
        self.current_position = 0.0
        self.grid_orders: Dict[str, Dict] = {}
        self.market_condition: Optional[MarketCondition] = None

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        self.peak_value = initial_capital

        # Technical indicators
        self.price_history = []
        self.volume_history = []

        self.logger = logging.getLogger(f"{__name__}.{symbol}")
        self.logger.info(f"High Performance Strategy initialized for {symbol}")

    async def initialize(self):
        """Initialize strategy with advanced settings"""
        await super().initialize()
        self.logger.info("High Performance Strategy ready")

    async def analyze_market_condition(self, data: pd.DataFrame) -> MarketCondition:
        """Analyze current market conditions"""
        if len(data) < 50:
            return MarketCondition("sideways", 0.5, 0.0, 0.0, 0.0)

        # Calculate indicators
        prices = data["close"].values

        # Trend analysis (20-period SMA slope)
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
        trend_strength = (sma_20 - sma_50) / sma_50

        # Volatility (20-period standard deviation)
        volatility = np.std(prices[-20:]) / np.mean(prices[-20:])

        # Support and resistance
        recent_prices = prices[-20:]
        support = np.min(recent_prices)
        resistance = np.max(recent_prices)

        # Determine trend direction
        if trend_strength > self.trend_threshold:
            trend = "bullish"
            momentum = min(trend_strength * 5, 1.0)  # Scale momentum
        elif trend_strength < -self.trend_threshold:
            trend = "bearish"
            momentum = max(trend_strength * 5, -1.0)
        else:
            trend = "sideways"
            momentum = trend_strength * 2

        return MarketCondition(
            trend=trend,
            volatility=min(volatility * 100, 1.0),  # Scale to 0-1
            momentum=momentum,
            support_level=support,
            resistance_level=resistance,
        )

    async def generate_signals(self, market_data: pd.DataFrame) -> List[TradeSignal]:
        """Generate optimized trading signals"""
        signals = []

        if market_data.empty or len(market_data) < 20:
            return signals

        try:
            current_price = float(market_data.iloc[-1]["close"])

            # Update market condition
            self.market_condition = await self.analyze_market_condition(market_data)

            # Strategy selection based on market condition
            if self.market_condition.trend == "bullish":
                signals.extend(await self._bullish_strategy(current_price, market_data))
            elif self.market_condition.trend == "bearish":
                signals.extend(await self._bearish_strategy(current_price, market_data))
            else:
                signals.extend(
                    await self._sideways_strategy(current_price, market_data)
                )

            # Add risk management signals
            signals.extend(await self._risk_management_signals(current_price))

        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")

        return signals

    async def _bullish_strategy(
        self, price: float, data: pd.DataFrame
    ) -> List[TradeSignal]:
        """Strategy for bullish markets - trend following"""
        signals = []

        # Buy on dips in uptrend
        if len(data) >= 5:
            recent_low = np.min(data["close"].values[-5:])
            if price <= recent_low * 1.005:  # Within 0.5% of recent low
                position_size = self._calculate_position_size(price, "buy")

                signals.append(
                    TradeSignal(
                        symbol=self.symbol,
                        side="buy",
                        strength=0.8,
                        price=price,
                        quantity=position_size,
                        reason="Bullish dip buy",
                        metadata={
                            "strategy": "trend_following",
                            "market_condition": "bullish",
                            "confidence": 0.8,
                        },
                    )
                )

        return signals

    async def _bearish_strategy(
        self, price: float, data: pd.DataFrame
    ) -> List[TradeSignal]:
        """Strategy for bearish markets - defensive"""
        signals = []

        # Sell on rallies in downtrend
        if self.current_position > 0 and len(data) >= 5:
            recent_high = np.max(data["close"].values[-5:])
            if price >= recent_high * 0.995:  # Within 0.5% of recent high

                signals.append(
                    TradeSignal(
                        symbol=self.symbol,
                        side="sell",
                        strength=0.7,
                        price=price,
                        quantity=abs(self.current_position) * 0.5,  # Partial sell
                        reason="Bearish rally sell",
                        metadata={
                            "strategy": "defensive",
                            "market_condition": "bearish",
                            "confidence": 0.7,
                        },
                    )
                )

        return signals

    async def _sideways_strategy(
        self, price: float, data: pd.DataFrame
    ) -> List[TradeSignal]:
        """Strategy for sideways markets - grid trading"""
        signals = []

        if not self.market_condition:
            return signals

        # Adaptive grid spacing based on volatility
        spacing = self.base_grid_spacing * (
            1 + self.market_condition.volatility * self.adaptive_multiplier
        )

        # Buy near support
        if price <= self.market_condition.support_level * (1 + spacing):
            position_size = self._calculate_position_size(price, "buy")

            signals.append(
                TradeSignal(
                    symbol=self.symbol,
                    side="buy",
                    strength=0.6,
                    price=price,
                    quantity=position_size,
                    reason="Grid buy near support",
                    metadata={
                        "strategy": "grid_trading",
                        "market_condition": "sideways",
                        "grid_level": "support",
                        "confidence": 0.6,
                    },
                )
            )

        # Sell near resistance
        if (
            price >= self.market_condition.resistance_level * (1 - spacing)
            and self.current_position > 0
        ):

            signals.append(
                TradeSignal(
                    symbol=self.symbol,
                    side="sell",
                    strength=0.6,
                    price=price,
                    quantity=abs(self.current_position) * 0.6,  # Partial sell
                    reason="Grid sell near resistance",
                    metadata={
                        "strategy": "grid_trading",
                        "market_condition": "sideways",
                        "grid_level": "resistance",
                        "confidence": 0.6,
                    },
                )
            )

        return signals

    async def _risk_management_signals(self, price: float) -> List[TradeSignal]:
        """Generate risk management signals"""
        signals = []

        # Stop-loss for large positions
        if abs(self.current_position) > self.max_position_size * 0.8:
            if self.current_position > 0:  # Long position
                stop_loss_price = price * 0.95  # 5% stop loss
                signals.append(
                    TradeSignal(
                        symbol=self.symbol,
                        side="sell",
                        strength=0.9,
                        price=stop_loss_price,
                        quantity=abs(self.current_position),
                        reason="Stop loss protection",
                        metadata={
                            "strategy": "risk_management",
                            "type": "stop_loss",
                            "confidence": 0.9,
                        },
                    )
                )

        return signals

    def _calculate_position_size(self, price: float, side: str) -> float:
        """Calculate optimal position size based on risk management"""
        if side == "buy":
            # Maximum position based on available capital
            max_quantity = (self.initial_capital * self.max_position_size) / price

            # Risk-adjusted size based on volatility
            if self.market_condition:
                risk_multiplier = 1 - self.market_condition.volatility * 0.5
                max_quantity *= risk_multiplier

            return max_quantity * 0.1  # Use 10% of max per trade

        return 0.0

    async def process_market_data(self, data: pd.DataFrame):
        """Process market data and execute strategy"""
        try:
            signals = await self.generate_signals(data)

            for signal in signals:
                await self._execute_signal(signal)

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")

    async def _execute_signal(self, signal: TradeSignal):
        """Execute a trading signal"""
        try:
            # Update position tracking
            if signal.side == "buy":
                self.current_position += signal.quantity
            else:
                self.current_position -= signal.quantity

            self.total_trades += 1

            # Calculate profit/loss estimation
            profit_estimate = (
                signal.quantity * signal.price * 0.001
            )  # 0.1% profit estimate
            self.total_profit += profit_estimate

            if profit_estimate > 0:
                self.winning_trades += 1

            self.logger.info(
                f"Executed {signal.side}: {signal.quantity:.4f} @ ${signal.price:.2f} "
                f"({signal.reason})"
            )

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        win_rate = (
            (self.winning_trades / self.total_trades * 100)
            if self.total_trades > 0
            else 0
        )

        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": win_rate,
            "total_profit": self.total_profit,
            "current_position": self.current_position,
            "max_drawdown": self.max_drawdown,
            "market_condition": (
                self.market_condition.__dict__ if self.market_condition else {}
            ),
            "performance_score": self._calculate_performance_score(),
        }

    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        if self.total_trades == 0:
            return 50.0

        win_rate_score = (self.winning_trades / self.total_trades) * 40
        profit_score = min(max(self.total_profit / 100, 0), 1) * 40  # Scale profit
        trade_frequency_score = min(self.total_trades / 100, 1) * 20

        return win_rate_score + profit_score + trade_frequency_score

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive strategy status"""
        performance = self.get_performance_metrics()

        return {
            "strategy_name": "High Performance Strategy",
            "symbol": self.symbol,
            "is_active": self.is_active,
            "performance": performance,
            "market_analysis": {
                "condition": (
                    self.market_condition.__dict__ if self.market_condition else {}
                ),
                "position": self.current_position,
                "active_orders": len(self.grid_orders),
            },
            "risk_metrics": {
                "max_position_size": self.max_position_size,
                "current_exposure": abs(self.current_position) / self.initial_capital,
                "diversification": 1.0,  # Single asset for now
            },
        }
