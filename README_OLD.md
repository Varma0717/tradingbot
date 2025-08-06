# Advanced Crypto Trading Bot

A production-ready, modular cryptocurrency trading bot with multi-exchange support, real-time data streaming, multiple trading strategies, backtesting capabilities, and comprehensive risk management.

## Features

### Core Features
- **Multi-exchange support** via CCXT (Binance, Coinbase Pro, Kraken, etc.)
- **Real-time data streaming** using WebSocket APIs
- **Multiple trading strategies** (Moving Average Crossover, RSI-based, and more)
- **Backtesting engine** with comprehensive performance metrics
- **Paper trading mode** for strategy validation
- **Live trading mode** with real order execution
- **Advanced risk management** (position sizing, stop-loss, take-profit, max drawdown)
- **Multiple order types** (market, limit, stop orders)
- **Real-time portfolio management** with P&L tracking
- **Comprehensive logging and alerting** (email, Telegram)
- **Secure configuration management**
- **Extensible modular architecture**

### Technical Stack
- Python 3.9+
- CCXT for exchange integration
- WebSockets for real-time data
- Pandas, NumPy, TA-Lib for technical analysis
- SQLAlchemy for data persistence
- Matplotlib/Plotly for visualization
- AsyncIO for concurrent operations
- Docker for containerization

## Installation

### Prerequisites
```bash
# Install Python 3.9+ and pip
# Install TA-Lib (required for technical indicators)
```

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd crypto-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Configuration
1. Copy `config/config.example.yaml` to `config/config.yaml`
2. Update the configuration with your preferences
3. Set up API keys in `.env` file
4. Configure risk management parameters

## Usage

### Paper Trading (Recommended for testing)
```bash
python main.py --mode paper --strategy ma_crossover --symbol BTC/USDT
```

### Live Trading (Use with caution)
```bash
python main.py --mode live --strategy rsi_strategy --symbol ETH/USDT
```

### Backtesting
```bash
python backtest.py --strategy ma_crossover --symbol BTC/USDT --start 2023-01-01 --end 2023-12-31
```

### Dashboard
```bash
python dashboard.py
# Access at http://localhost:8080
```

## Project Structure

```
crypto-trading-bot/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bot.py              # Main bot orchestrator
│   │   ├── config.py           # Configuration management
│   │   └── exceptions.py       # Custom exceptions
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_manager.py     # Data fetching and storage
│   │   ├── websocket_client.py # WebSocket data streaming
│   │   └── database.py         # Database models and operations
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base_strategy.py    # Abstract base strategy
│   │   ├── ma_crossover.py     # Moving Average Crossover
│   │   ├── rsi_strategy.py     # RSI-based strategy
│   │   └── ml_strategy.py      # Machine Learning strategy
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── order_manager.py    # Order placement and management
│   │   ├── exchange_client.py  # Exchange API client
│   │   └── portfolio_manager.py # Portfolio tracking
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── risk_manager.py     # Risk management rules
│   │   └── position_sizer.py   # Position sizing algorithms
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── backtest_engine.py  # Backtesting engine
│   │   └── performance.py      # Performance metrics
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── notifier.py         # Base notification class
│   │   ├── email_notifier.py   # Email notifications
│   │   └── telegram_notifier.py # Telegram notifications
│   └── utils/
│       ├── __init__.py
│       ├── indicators.py       # Technical indicators
│       ├── logger.py           # Logging configuration
│       └── helpers.py          # Utility functions
├── config/
│   ├── config.yaml             # Main configuration
│   ├── config.example.yaml     # Example configuration
│   └── logging.yaml            # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_strategies.py
│   ├── test_risk_management.py
│   └── test_backtesting.py
├── scripts/
│   ├── setup_database.py       # Database initialization
│   └── update_data.py          # Data update scripts
├── data/                       # Historical data storage
├── logs/                       # Log files
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py                     # Main entry point
├── backtest.py                 # Backtesting script
├── dashboard.py                # Web dashboard
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Configuration

### Environment Variables (.env)
```
# Exchange API Keys
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET_KEY=your_coinbase_secret_key

# Notification Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database
DATABASE_URL=sqlite:///trading_bot.db
```

### Main Configuration (config/config.yaml)
```yaml
bot:
  name: "CryptoTradingBot"
  version: "1.0.0"
  
trading:
  default_exchange: "binance"
  default_timeframe: "1h"
  max_positions: 5
  
risk_management:
  max_position_size: 0.1  # 10% of portfolio per trade
  stop_loss_pct: 0.02     # 2% stop loss
  take_profit_pct: 0.06   # 6% take profit
  max_drawdown: 0.15      # 15% max drawdown
  
strategies:
  ma_crossover:
    fast_ma: 20
    slow_ma: 50
  rsi_strategy:
    rsi_period: 14
    oversold: 30
    overbought: 70
```

## Trading Strategies

### 1. Moving Average Crossover
- Buys when fast MA crosses above slow MA
- Sells when fast MA crosses below slow MA
- Configurable MA periods

### 2. RSI Strategy
- Buys when RSI is oversold (<30)
- Sells when RSI is overbought (>70)
- Configurable RSI period and thresholds

### 3. Machine Learning Strategy (Optional)
- Uses historical data to train models
- Implements multiple ML algorithms
- Auto-retraining capabilities

## Risk Management

- **Position Sizing**: Kelly Criterion, Fixed Percentage, Fixed Amount
- **Stop Loss**: Percentage-based, ATR-based, Trailing stops
- **Take Profit**: Fixed percentage, Dynamic based on volatility
- **Max Drawdown**: Portfolio-level protection
- **Correlation Limits**: Prevents over-concentration

## Backtesting

The backtesting engine provides:
- Historical simulation with realistic slippage and fees
- Comprehensive performance metrics (Sharpe ratio, max drawdown, etc.)
- Visual charts and reports
- Walk-forward analysis
- Monte Carlo simulation

### Sample Backtest Command
```bash
python backtest.py \
  --strategy ma_crossover \
  --symbol BTC/USDT \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --initial-balance 10000 \
  --timeframe 1h
```

## Deployment

### Local Development
```bash
python main.py --mode paper
```

### Docker Deployment
```bash
# Build image
docker build -t crypto-trading-bot .

# Run container
docker run -d --name trading-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  crypto-trading-bot
```

### VPS Deployment
1. Transfer files to VPS
2. Install dependencies
3. Configure systemd service
4. Set up monitoring and alerts
5. Configure log rotation

## Monitoring and Alerts

- **Real-time dashboard** showing positions, P&L, and performance
- **Email alerts** for important events (trades, errors, drawdowns)
- **Telegram notifications** for instant mobile alerts
- **Comprehensive logging** with different log levels
- **Performance monitoring** with key metrics tracking

## Security

- API keys stored in environment variables
- Input validation and sanitization
- Rate limiting and error handling
- Secure database connections
- Audit logging for all actions

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_strategies.py
pytest tests/test_risk_management.py
pytest tests/test_backtesting.py

# Run with coverage
pytest --cov=src tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Disclaimer

This trading bot is for educational purposes. Cryptocurrency trading involves substantial risk of loss. Use at your own risk and never trade with money you cannot afford to lose.

## License

MIT License - see LICENSE file for details.

## Support

- Create issues for bug reports
- Check documentation for common questions
- Join our community for discussions

## Changelog

### v1.0.0
- Initial release with core functionality
- Multi-exchange support
- Basic trading strategies
- Backtesting engine
- Risk management system
