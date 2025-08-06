"""
Custom exceptions for the trading bot.
"""


class TradingBotError(Exception):
    """Base exception for trading bot errors."""

    pass


class ConfigurationError(TradingBotError):
    """Raised when there's a configuration error."""

    pass


class ExchangeError(TradingBotError):
    """Raised when there's an exchange-related error."""

    pass


class OrderError(TradingBotError):
    """Raised when there's an order-related error."""

    pass


class InsufficientFundsError(OrderError):
    """Raised when there are insufficient funds for an order."""

    pass


class InvalidOrderError(OrderError):
    """Raised when an order is invalid."""

    pass


class StrategyError(TradingBotError):
    """Raised when there's a strategy-related error."""

    pass


class RiskManagementError(TradingBotError):
    """Raised when risk management rules are violated."""

    pass


class PortfolioError(TradingBotError):
    """Raised when there's a portfolio-related error."""

    pass


class RiskError(TradingBotError):
    """Raised when there's a risk-related error."""

    pass


class RiskViolationError(TradingBotError):
    """Raised when risk management rules are violated."""

    pass


class DataError(TradingBotError):
    """Raised when there's a data-related error."""

    pass


class WebSocketError(TradingBotError):
    """Raised when there's a WebSocket connection error."""

    pass


class NotificationError(TradingBotError):
    """Raised when there's a notification error."""

    pass


class DatabaseError(TradingBotError):
    """Raised when there's a database error."""

    pass


class BacktestError(TradingBotError):
    """Raised when there's a backtesting error."""

    pass
