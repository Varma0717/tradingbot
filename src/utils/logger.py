"""
Logging configuration and utilities for the trading bot.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO", log_file: Optional[str] = None, verbose: bool = False
) -> None:
    """
    Setup logging configuration for the trading bot.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        verbose: Enable verbose logging
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(detailed_formatter if verbose else simple_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from external libraries
    logging.getLogger("ccxt").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class TradingLogger:
    """
    Custom logger class for trading-specific logging needs.
    """

    def __init__(self, name: str):
        """
        Initialize trading logger.

        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.trade_logger = logging.getLogger(f"{name}.trades")
        self.strategy_logger = logging.getLogger(f"{name}.strategy")
        self.risk_logger = logging.getLogger(f"{name}.risk")

    def log_trade(self, trade_info: dict) -> None:
        """
        Log trade information.

        Args:
            trade_info: Dictionary containing trade details
        """
        self.trade_logger.info(
            f"TRADE: {trade_info.get('side', 'UNKNOWN')} "
            f"{trade_info.get('amount', 'UNKNOWN')} "
            f"{trade_info.get('symbol', 'UNKNOWN')} "
            f"@ {trade_info.get('price', 'UNKNOWN')} "
            f"- Status: {trade_info.get('status', 'UNKNOWN')}"
        )

    def log_signal(self, signal_info: dict) -> None:
        """
        Log trading signal information.

        Args:
            signal_info: Dictionary containing signal details
        """
        self.strategy_logger.info(
            f"SIGNAL: {signal_info.get('action', 'UNKNOWN')} "
            f"{signal_info.get('symbol', 'UNKNOWN')} "
            f"- Confidence: {signal_info.get('confidence', 'UNKNOWN')} "
            f"- Reason: {signal_info.get('reason', 'UNKNOWN')}"
        )

    def log_risk_event(self, risk_info: dict) -> None:
        """
        Log risk management event.

        Args:
            risk_info: Dictionary containing risk event details
        """
        self.risk_logger.warning(
            f"RISK: {risk_info.get('event_type', 'UNKNOWN')} "
            f"- Details: {risk_info.get('details', 'UNKNOWN')} "
            f"- Action: {risk_info.get('action', 'UNKNOWN')}"
        )

    def log_performance(self, performance_info: dict) -> None:
        """
        Log performance metrics.

        Args:
            performance_info: Dictionary containing performance metrics
        """
        self.logger.info(
            f"PERFORMANCE: "
            f"Total PnL: {performance_info.get('total_pnl', 'UNKNOWN')}, "
            f"Win Rate: {performance_info.get('win_rate', 'UNKNOWN')}, "
            f"Drawdown: {performance_info.get('max_drawdown', 'UNKNOWN')}"
        )


def configure_exchange_logging():
    """Configure logging for exchange-specific operations."""

    # Create exchange-specific loggers
    binance_logger = logging.getLogger("exchange.binance")
    coinbase_logger = logging.getLogger("exchange.coinbase")
    kraken_logger = logging.getLogger("exchange.kraken")

    # Set appropriate levels
    binance_logger.setLevel(logging.INFO)
    coinbase_logger.setLevel(logging.INFO)
    kraken_logger.setLevel(logging.INFO)


def log_startup_info():
    """Log important startup information."""
    logger = get_logger(__name__)

    logger.info("=" * 50)
    logger.info("CRYPTO TRADING BOT STARTING")
    logger.info("=" * 50)
    logger.info(f"Python version: {os.sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Log level: {logging.getLogger().level}")
    logger.info("=" * 50)


def log_shutdown_info():
    """Log shutdown information."""
    logger = get_logger(__name__)

    logger.info("=" * 50)
    logger.info("CRYPTO TRADING BOT SHUTDOWN")
    logger.info("=" * 50)
