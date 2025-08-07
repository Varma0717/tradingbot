"""
Base strategy class for implementing trading strategies.
All trading strategies should inherit from this class.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from ..core.config import Config
from ..core.exceptions import StrategyError
from ..utils.logger import get_logger
from ..utils.indicators import TechnicalIndicators


class TradeSignal:
    """Represents a trading signal."""

    def __init__(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        strength: float,  # Signal strength 0.0 to 1.0
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_type: str = "market",
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize trade signal.

        Args:
            symbol: Trading symbol
            side: Trade side ('buy' or 'sell')
            strength: Signal strength (0.0 to 1.0)
            price: Entry price (None for market orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            order_type: Order type ('market', 'limit', 'stop')
            reason: Reason for the signal
            metadata: Additional signal metadata
        """
        self.symbol = symbol
        self.side = side.lower()
        self.strength = max(0.0, min(1.0, strength))  # Clamp between 0 and 1
        self.price = price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.order_type = order_type.lower()
        self.reason = reason
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

        # Validate signal
        self._validate()

    def _validate(self):
        """Validate the trade signal."""
        if self.side not in ["buy", "sell"]:
            raise StrategyError(f"Invalid trade side: {self.side}")

        if self.order_type not in ["market", "limit", "stop", "stop_limit"]:
            raise StrategyError(f"Invalid order type: {self.order_type}")

        if self.order_type == "limit" and self.price is None:
            raise StrategyError("Limit orders require a price")

        if self.strength < 0.0 or self.strength > 1.0:
            raise StrategyError(
                f"Signal strength must be between 0.0 and 1.0, got {self.strength}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "strength": self.strength,
            "price": self.price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "order_type": self.order_type,
            "reason": self.reason,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        """String representation of the signal."""
        return f"TradeSignal({self.side.upper()} {self.symbol}, strength={self.strength:.2f}, reason='{self.reason}')"

    def __repr__(self) -> str:
        """Detailed representation of the signal."""
        return (
            f"TradeSignal(symbol='{self.symbol}', side='{self.side}', "
            f"strength={self.strength}, price={self.price}, "
            f"stop_loss={self.stop_loss}, take_profit={self.take_profit}, "
            f"order_type='{self.order_type}', reason='{self.reason}')"
        )


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.

    This class provides the framework for implementing trading strategies.
    Subclasses must implement the generate_signals method.
    """

    def __init__(self, strategy_config: Dict[str, Any], config: Config):
        """
        Initialize the base strategy.

        Args:
            strategy_config: Strategy-specific configuration
            config: Global configuration object
        """
        self.strategy_config = strategy_config
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # Strategy state
        self.is_initialized = False
        self.last_signal_time: Optional[datetime] = None
        self.position_count = 0
        self.total_signals = 0
        self.successful_signals = 0

        # Historical data cache
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
        self.cache_ttl = 300  # 5 minutes

        # Strategy metrics
        self.metrics = {
            "signals_generated": 0,
            "signals_executed": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }

        # Initialize strategy - check if it's async
        if asyncio.iscoroutinefunction(self.initialize):
            # For async initialize methods, create a task or warn user
            self.logger.warning(
                f"{self.__class__.__name__} has async initialize method - call await strategy.initialize() manually"
            )
            # Don't call async method here
        else:
            self.initialize()

    def initialize(self):
        """Initialize the strategy. Override in subclasses if needed."""
        self.is_initialized = True
        self.logger.info(f"{self.__class__.__name__} strategy initialized")

    @abstractmethod
    async def generate_signals(self, market_data: pd.DataFrame) -> List[TradeSignal]:
        """
        Generate trading signals based on market data.

        Args:
            market_data: DataFrame with OHLCV data

        Returns:
            List of TradeSignal objects
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return the strategy description."""
        pass

    @property
    @abstractmethod
    def required_indicators(self) -> List[str]:
        """Return list of required technical indicators."""
        pass

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with indicators added
        """
        try:
            # Add basic indicators that most strategies need
            result_df = df.copy()

            # Only calculate if we have enough data
            if len(df) < 50:
                self.logger.warning(
                    f"Insufficient data for indicators: {len(df)} candles"
                )
                return result_df

            # Calculate all indicators
            result_df = TechnicalIndicators.calculate_all_indicators(result_df)

            return result_df

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return df

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate market data before processing.

        Args:
            df: DataFrame to validate

        Returns:
            True if data is valid
        """
        try:
            # Check if DataFrame is not empty
            if df.empty:
                self.logger.warning("Market data is empty")
                return False

            # Check required columns
            required_columns = ["open", "high", "low", "close", "volume"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return False

            # Check for sufficient data points
            min_data_points = max(50, self.get_min_data_points())
            if len(df) < min_data_points:
                self.logger.warning(
                    f"Insufficient data points: {len(df)} < {min_data_points}"
                )
                return False

            # Check for data quality issues
            if df[required_columns].isnull().any().any():
                self.logger.warning("Data contains null values")
                return False

            if (df[["open", "high", "low", "close"]] <= 0).any().any():
                self.logger.warning("Data contains non-positive prices")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return False

    def get_min_data_points(self) -> int:
        """
        Get minimum required data points for the strategy.
        Override in subclasses for specific requirements.

        Returns:
            Minimum number of data points needed
        """
        return 50

    def should_generate_signal(self, current_time: datetime) -> bool:
        """
        Check if strategy should generate signals at the current time.

        Args:
            current_time: Current datetime

        Returns:
            True if should generate signals
        """
        # Respect minimum time between signals
        min_signal_interval = self.strategy_config.get(
            "min_signal_interval", 300
        )  # 5 minutes default

        if self.last_signal_time:
            time_since_last = (current_time - self.last_signal_time).total_seconds()
            if time_since_last < min_signal_interval:
                return False

        return True

    def create_signal(
        self,
        symbol: str,
        side: str,
        strength: float,
        price: Optional[float] = None,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TradeSignal:
        """
        Create a trade signal with strategy-specific parameters.

        Args:
            symbol: Trading symbol
            side: Trade side
            strength: Signal strength
            price: Entry price
            reason: Signal reason
            metadata: Additional metadata

        Returns:
            TradeSignal object
        """
        # Calculate stop loss and take profit based on strategy config
        stop_loss = None
        take_profit = None

        if price and side == "buy":
            if "stop_loss_pct" in self.strategy_config:
                stop_loss = price * (1 - self.strategy_config["stop_loss_pct"])
            if "take_profit_pct" in self.strategy_config:
                take_profit = price * (1 + self.strategy_config["take_profit_pct"])
        elif price and side == "sell":
            if "stop_loss_pct" in self.strategy_config:
                stop_loss = price * (1 + self.strategy_config["stop_loss_pct"])
            if "take_profit_pct" in self.strategy_config:
                take_profit = price * (1 - self.strategy_config["take_profit_pct"])

        # Use global risk management if not specified in strategy
        if not stop_loss and price:
            stop_loss_pct = self.config.risk.stop_loss_pct
            if side == "buy":
                stop_loss = price * (1 - stop_loss_pct)
            else:
                stop_loss = price * (1 + stop_loss_pct)

        if not take_profit and price:
            take_profit_pct = self.config.risk.take_profit_pct
            if side == "buy":
                take_profit = price * (1 + take_profit_pct)
            else:
                take_profit = price * (1 - take_profit_pct)

        # Create signal
        signal = TradeSignal(
            symbol=symbol,
            side=side,
            strength=strength,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            order_type="market" if price is None else "limit",
            reason=reason,
            metadata=metadata,
        )

        # Update strategy metrics
        self.total_signals += 1
        self.metrics["signals_generated"] += 1
        self.last_signal_time = datetime.now()

        self.logger.info(f"Generated signal: {signal}")

        return signal

    async def on_order_filled(self, order: Dict[str, Any]):
        """
        Handle order filled event.

        Args:
            order: Order information
        """
        try:
            self.logger.info(f"Order filled: {order}")

            # Update strategy metrics
            self.metrics["signals_executed"] += 1

            # Track position count
            if order.get("side") == "buy":
                self.position_count += 1
            elif order.get("side") == "sell":
                self.position_count = max(0, self.position_count - 1)

            # Strategy-specific order handling
            await self.handle_order_filled(order)

        except Exception as e:
            self.logger.error(f"Error handling order filled: {e}")

    async def handle_order_filled(self, order: Dict[str, Any]):
        """
        Strategy-specific order handling. Override in subclasses.

        Args:
            order: Order information
        """
        pass

    async def on_trade_closed(self, trade: Dict[str, Any]):
        """
        Handle trade closed event.

        Args:
            trade: Trade information with P&L
        """
        try:
            profit_loss = trade.get("profit_loss", 0)

            if profit_loss > 0:
                self.successful_signals += 1

            # Update win rate
            if self.metrics["signals_executed"] > 0:
                self.metrics["win_rate"] = (
                    self.successful_signals / self.metrics["signals_executed"]
                )

            self.logger.info(f"Trade closed: P&L = {profit_loss:.4f}")

            # Strategy-specific trade handling
            await self.handle_trade_closed(trade)

        except Exception as e:
            self.logger.error(f"Error handling trade closed: {e}")

    async def handle_trade_closed(self, trade: Dict[str, Any]):
        """
        Strategy-specific trade handling. Override in subclasses.

        Args:
            trade: Trade information
        """
        pass

    def get_current_positions(self) -> int:
        """
        Get current number of open positions.

        Returns:
            Number of open positions
        """
        return self.position_count

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get strategy performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset strategy metrics."""
        self.metrics = {
            "signals_generated": 0,
            "signals_executed": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }
        self.total_signals = 0
        self.successful_signals = 0
        self.position_count = 0

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get strategy parameters.

        Returns:
            Dictionary of strategy parameters
        """
        return self.strategy_config.copy()

    def update_parameters(self, new_params: Dict[str, Any]):
        """
        Update strategy parameters.

        Args:
            new_params: New parameter values
        """
        self.strategy_config.update(new_params)
        self.logger.info(f"Updated strategy parameters: {new_params}")

    def __str__(self) -> str:
        """String representation of the strategy."""
        return f"{self.name} Strategy"

    def __repr__(self) -> str:
        """Detailed representation of the strategy."""
        return f"{self.__class__.__name__}(config={self.strategy_config})"
