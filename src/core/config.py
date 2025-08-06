"""
Configuration management for the trading bot.
Handles loading and validation of configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ExchangeConfig:
    """Configuration for exchange connections."""

    name: str
    api_key: str = ""
    secret_key: str = ""
    passphrase: str = ""  # For Coinbase Pro
    sandbox: bool = True
    rate_limit: int = 10  # requests per second
    timeout: int = 30

    def __post_init__(self):
        """Load API keys from environment variables."""
        if self.name.lower() == "binance":
            self.api_key = os.getenv("BINANCE_API_KEY", "")
            self.secret_key = os.getenv("BINANCE_SECRET_KEY", "")
            self.sandbox = os.getenv("BINANCE_SANDBOX", "true").lower() == "true"
        elif self.name.lower() == "coinbase":
            self.api_key = os.getenv("COINBASE_API_KEY", "")
            self.secret_key = os.getenv("COINBASE_SECRET_KEY", "")
            self.passphrase = os.getenv("COINBASE_PASSPHRASE", "")
            self.sandbox = os.getenv("COINBASE_SANDBOX", "true").lower() == "true"
        elif self.name.lower() == "kraken":
            self.api_key = os.getenv("KRAKEN_API_KEY", "")
            self.secret_key = os.getenv("KRAKEN_SECRET_KEY", "")


@dataclass
class TradingConfig:
    """Configuration for trading parameters."""

    mode: str = "paper"  # paper, live, backtest
    strategy: str = "ma_crossover"
    symbol: str = "BTC/USDT"
    exchange: str = "binance"
    base_currency: str = "USDT"
    paper_balance: float = 10000.0
    timeframe: str = "1h"
    max_positions: int = 5
    initial_balance: float = 10000.0
    dry_run: bool = False
    order_timeout: int = 300  # seconds
    slippage_tolerance: float = 0.001  # 0.1%
    timeframes: List[str] = field(default_factory=lambda: ["1h"])

    # Trading session settings
    trading_hours: Dict[str, str] = field(
        default_factory=lambda: {"start": "00:00", "end": "23:59", "timezone": "UTC"}
    )

    # Symbols to trade
    symbols: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])


@dataclass
@dataclass
class RiskConfig:
    """Configuration for risk management."""

    max_position_size: float = 0.1  # 10% of portfolio per position
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.06  # 6% take profit
    max_drawdown: float = 0.15  # 15% maximum drawdown
    max_daily_loss: float = 0.05  # 5% max daily loss
    risk_per_trade: float = 2.0  # Percentage of portfolio per trade

    # Position sizing method
    position_sizing_method: str = (
        "fixed_percentage"  # fixed_percentage, kelly, fixed_amount
    )

    # Correlation limits
    max_correlation: float = 0.7  # Maximum correlation between positions
    correlation_period: int = 30  # Days to calculate correlation

    # Leverage settings
    max_leverage: float = 1.0  # No leverage by default
    use_margin: bool = False


@dataclass
class StrategyConfig:
    """Configuration for trading strategies."""

    # Moving Average Crossover
    ma_crossover: Dict[str, Any] = field(
        default_factory=lambda: {
            "fast_ma": 20,
            "slow_ma": 50,
            "ma_type": "sma",  # sma, ema, wma
            "min_volume": 1000000,  # Minimum 24h volume
        }
    )

    # RSI Strategy
    rsi_strategy: Dict[str, Any] = field(
        default_factory=lambda: {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70,
            "rsi_ma_period": 9,
            "min_rsi_divergence": 5,
        }
    )

    # Machine Learning Strategy
    ml_strategy: Dict[str, Any] = field(
        default_factory=lambda: {
            "model_type": "xgboost",  # xgboost, random_forest, svm
            "lookback_period": 100,
            "features": ["rsi", "macd", "bb_bands", "volume", "price_change"],
            "retrain_frequency": "weekly",
            "confidence_threshold": 0.6,
        }
    )


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""

    url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
    )
    echo: bool = field(
        default_factory=lambda: os.getenv("DATABASE_ECHO", "false").lower() == "true"
    )
    pool_size: int = field(
        default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "10"))
    )
    max_overflow: int = field(
        default_factory=lambda: int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    )
    pool_timeout: int = field(
        default_factory=lambda: int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    )


@dataclass
class NotificationConfig:
    """Configuration for notifications."""

    enabled: bool = True

    # Email settings
    email: Dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "host": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("EMAIL_PORT", "587")),
            "user": os.getenv("EMAIL_USER", ""),
            "password": os.getenv("EMAIL_PASSWORD", ""),
            "from_email": os.getenv("EMAIL_FROM", "noreply@tradingbot.com"),
            "to_emails": ["trader@example.com"],
            "use_tls": True,
        }
    )

    # Telegram settings
    telegram: Dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
            "parse_mode": "HTML",
        }
    )

    # Notification triggers
    triggers: Dict[str, bool] = field(
        default_factory=lambda: {
            "trade_opened": True,
            "trade_closed": True,
            "stop_loss_hit": True,
            "take_profit_hit": True,
            "error_occurred": True,
            "daily_summary": True,
            "weekly_summary": True,
            "high_drawdown": True,
        }
    )


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = os.getenv("LOG_LEVEL", "INFO")
    file: str = os.getenv("LOG_FILE", "logs/trading_bot.log")
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Structured logging
    structured: bool = True
    json_format: bool = False


@dataclass
class DashboardConfig:
    """Configuration for web dashboard."""

    enabled: bool = True
    host: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port: int = int(os.getenv("DASHBOARD_PORT", "8080"))
    secret_key: str = os.getenv("DASHBOARD_SECRET_KEY", "your-secret-key")
    auto_reload: bool = False
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


class Config:
    """Main configuration class that loads and manages all configuration."""

    def __init__(self, config_file: str = "config/config.yaml"):
        """
        Initialize configuration from file and environment variables.

        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = config_file
        self._config_data = self._load_config_file()

        # Initialize configuration sections
        self.trading = self._init_trading_config()
        self.risk = self._init_risk_config()
        self.strategies = self._init_strategy_config()
        self.database = DatabaseConfig()
        self.notifications = NotificationConfig()
        self.logging = LoggingConfig()
        self.dashboard = DashboardConfig()

        # Initialize exchange configurations
        self.exchanges = self._init_exchange_configs()

    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path(self.config_file)

        if not config_path.exists():
            # Create default config if file doesn't exist
            self._create_default_config(config_path)

        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error loading config file {config_path}: {e}")

    def _create_default_config(self, config_path: Path):
        """Create a default configuration file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "bot": {"name": "CryptoTradingBot", "version": "1.0.0"},
            "trading": {
                "mode": "paper",
                "strategy": "ma_crossover",
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "timeframe": "1h",
                "max_positions": 5,
                "initial_balance": 10000.0,
            },
            "risk_management": {
                "max_position_size": 0.1,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.06,
                "max_drawdown": 0.15,
            },
            "strategies": {
                "ma_crossover": {"fast_ma": 20, "slow_ma": 50},
                "rsi_strategy": {"rsi_period": 14, "oversold": 30, "overbought": 70},
            },
        }

        with open(config_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)

    def _init_trading_config(self) -> TradingConfig:
        """Initialize trading configuration."""
        trading_data = self._config_data.get("trading", {})
        return TradingConfig(**trading_data)

    def _init_risk_config(self) -> RiskConfig:
        """Initialize risk management configuration."""
        risk_data = self._config_data.get("risk_management", {})
        return RiskConfig(**risk_data)

    def _init_strategy_config(self) -> StrategyConfig:
        """Initialize strategy configuration."""
        strategy_data = self._config_data.get("strategies", {})
        config = StrategyConfig()

        # Update with loaded configuration
        if "ma_crossover" in strategy_data:
            config.ma_crossover.update(strategy_data["ma_crossover"])
        if "rsi_strategy" in strategy_data:
            config.rsi_strategy.update(strategy_data["rsi_strategy"])
        if "ml_strategy" in strategy_data:
            config.ml_strategy.update(strategy_data["ml_strategy"])

        return config

    def _init_exchange_configs(self) -> Dict[str, ExchangeConfig]:
        """Initialize exchange configurations."""
        exchanges = {}
        exchange_data = self._config_data.get("exchanges", {})

        # Default exchanges
        for exchange_name in ["binance", "coinbase", "kraken"]:
            exchange_config = exchange_data.get(exchange_name, {})
            exchanges[exchange_name] = ExchangeConfig(
                name=exchange_name, **exchange_config
            )

        return exchanges

    def get_exchange_config(self, exchange_name: str) -> ExchangeConfig:
        """Get configuration for a specific exchange."""
        if exchange_name not in self.exchanges:
            raise ValueError(f"Exchange {exchange_name} not configured")
        return self.exchanges[exchange_name]

    def validate(self) -> bool:
        """
        Validate the configuration for consistency and required values.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        errors = []

        # Validate trading configuration
        if self.trading.mode not in ["paper", "live", "backtest", "dashboard"]:
            errors.append(f"Invalid trading mode: {self.trading.mode}")

        if self.trading.mode == "live":
            # Check if API keys are provided for live trading
            exchange_config = self.get_exchange_config(self.trading.exchange)
            if not exchange_config.api_key or not exchange_config.secret_key:
                errors.append(
                    f"API keys required for live trading on {self.trading.exchange}"
                )

        # Validate risk management
        if not (0 < self.risk.max_position_size <= 1):
            errors.append("max_position_size must be between 0 and 1")

        if self.risk.stop_loss_pct <= 0:
            errors.append("stop_loss_pct must be positive")

        if self.risk.take_profit_pct <= 0:
            errors.append("take_profit_pct must be positive")

        # Validate strategy configuration
        strategy_config = getattr(self.strategies, self.trading.strategy, None)
        if strategy_config is None:
            errors.append(f"Strategy {self.trading.strategy} not configured")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

        return True

    def update_config(self, section: str, updates: Dict[str, Any]) -> None:
        """
        Update configuration section with new values.

        Args:
            section: Configuration section to update
            updates: Dictionary of updates to apply
        """
        if hasattr(self, section):
            config_obj = getattr(self, section)
            for key, value in updates.items():
                if hasattr(config_obj, key):
                    setattr(config_obj, key, value)

    def save_config(self) -> None:
        """Save current configuration to file."""
        config_data = {
            "trading": {
                "mode": self.trading.mode,
                "strategy": self.trading.strategy,
                "symbol": self.trading.symbol,
                "exchange": self.trading.exchange,
                "timeframe": self.trading.timeframe,
                "max_positions": self.trading.max_positions,
                "initial_balance": self.trading.initial_balance,
            },
            "risk_management": {
                "max_position_size": self.risk.max_position_size,
                "stop_loss_pct": self.risk.stop_loss_pct,
                "take_profit_pct": self.risk.take_profit_pct,
                "max_drawdown": self.risk.max_drawdown,
            },
            "strategies": {
                "ma_crossover": self.strategies.ma_crossover,
                "rsi_strategy": self.strategies.rsi_strategy,
                "ml_strategy": self.strategies.ml_strategy,
            },
        }

        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

    def __str__(self) -> str:
        """String representation of configuration."""
        return f"TradingBot Config: {self.trading.mode} mode, {self.trading.strategy} strategy, {self.trading.symbol} on {self.trading.exchange}"
