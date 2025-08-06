# Advanced Crypto Trading Bot

A comprehensive cryptocurrency trading bot with web dashboard, real-time data processing, multiple trading strategies, and risk management features.

## 🚀 Features

- **Web Dashboard**: Modern responsive web interface for monitoring and control
- **Real-time Data**: Live market data from Binance API
- **Multiple Strategies**: Moving Average Crossover, RSI, and more
- **Risk Management**: Stop-loss, position sizing, portfolio protection
- **Paper Trading**: Test strategies without real money
- **Live Trading**: Execute real trades with proper risk controls
- **Database Storage**: MySQL integration for trade history and analytics
- **Real-time Updates**: WebSocket connections for live data
- **Order Management**: Create, cancel, and monitor orders
- **Portfolio Tracking**: Real-time balance and P&L tracking

## 📋 Requirements

- Python 3.11 or higher
- XAMPP with MySQL
- Binance API keys (for live trading)

## 🛠️ Installation

### 1. Environment Setup (Already Complete)

The virtual environment is already set up with all dependencies installed.

### 2. Setup MySQL Database

1. Start XAMPP and ensure MySQL is running
2. Open phpMyAdmin (http://localhost/phpmyadmin)
3. Create a new database named `crypto_trading_bot`

### 3. Configure API Keys

Your `.env` file should contain:

```env
# Binance API Configuration
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_SANDBOX=false

# Database Configuration
DATABASE_URL=mysql+pymysql://root:@localhost:3306/crypto_trading_bot

# Trading Configuration
DEFAULT_SYMBOL=BTC/USDT
DEFAULT_TIMEFRAME=1h
DEFAULT_STRATEGY=ma_crossover
PAPER_TRADING=true
INITIAL_BALANCE=10000

# Risk Management
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.05
```

## 🚀 Quick Start

### Option 1: Windows Batch Script (Recommended)

Double-click `start_bot.bat` to start the entire system.

### Option 2: PowerShell Script

Right-click `start_bot.ps1` and select "Run with PowerShell".

### Option 3: Manual Startup

```bash
# Activate virtual environment
venv\Scripts\activate

# Setup database tables
python setup_database.py

# Start the dashboard
python start_dashboard.py
```

## 🖥️ Using the Dashboard

1. Open your web browser and go to `http://localhost:8000`
2. The dashboard will show:
   - **Real-time account balance** from Binance
   - **Current positions and orders**
   - **Market data and price charts**
   - **Trading controls and order placement**
   - **Performance analytics**

## 📊 Trading Modes

### Paper Trading (Default)
- ✅ Safe testing with virtual money
- ✅ All features work except actual order execution
- ✅ Perfect for strategy testing

### Live Trading
- ⚠️ Real money trading with actual orders
- ⚠️ Requires proper API keys and sufficient balance
- ⚠️ Enable by setting `PAPER_TRADING=false` in `.env`

## 🔗 API Endpoints

The dashboard provides a comprehensive RESTful API:

- `GET /api/status` - Bot status and connection info
- `GET /api/balance` - Account balance and portfolio
- `GET /api/positions` - Current open positions
- `GET /api/orders` - Order history and active orders
- `POST /api/orders` - Place new order
- `DELETE /api/orders/{id}` - Cancel existing order
- `GET /api/analytics` - Performance analytics and metrics

## 📈 Trading Strategies

### Moving Average Crossover
- **Logic**: Buy when fast MA crosses above slow MA, sell when fast MA crosses below slow MA
- **Parameters**: Configurable periods (default: 20/50)
- **Best for**: Trending markets

### RSI Strategy
- **Logic**: Buy when RSI is oversold (< 30), sell when RSI is overbought (> 70)
- **Parameters**: RSI period and thresholds
- **Best for**: Range-bound markets with momentum confirmation

## 🛡️ Risk Management

- **Stop Loss**: Automatic loss cutting at configurable percentage
- **Position Sizing**: Limits position size relative to account balance
- **Maximum Drawdown**: Monitors and limits total portfolio loss
- **Order Validation**: Checks balance and risk before placing orders
- **Real-time Monitoring**: Continuous risk assessment and position tracking

## 🗄️ Database Schema

The bot stores comprehensive data:
- `market_data`: OHLCV price data and technical indicators
- `trades`: Complete trade history with P&L
- `orders`: Order lifecycle and execution details
- `portfolio_snapshots`: Historical balance and performance
- `performance_metrics`: Strategy performance analytics

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - ✅ Ensure XAMPP MySQL is running
   - ✅ Check database name is `crypto_trading_bot`
   - ✅ Verify connection string in `.env`

2. **Binance API Error**
   - ✅ Check API keys are correct
   - ✅ Ensure IP is whitelisted (for live trading)
   - ✅ Verify account has sufficient balance

3. **Dashboard Not Loading**
   - ✅ Check port 8000 is not in use
   - ✅ Ensure virtual environment is activated
   - ✅ Check Python version (3.11+ required)

### Logs

Comprehensive logging in `logs/` directory:
- `trading_bot.log` - Main application logs
- `api.log` - API request/response logs
- `trading.log` - Trading execution logs

## 🏗️ Project Structure

```
src/
├── core/           # Core bot logic and configuration
├── dashboard/      # Web dashboard and API
├── data/          # Data management and database
├── execution/     # Order and portfolio management
├── strategies/    # Trading strategies
├── risk/          # Risk management
├── notifications/ # Alerts and notifications
├── backtesting/   # Strategy backtesting
└── utils/         # Utilities and helpers
```

## 🔒 Security

- 🔐 Never commit API keys to version control
- 🔐 Use environment variables for sensitive data
- 🔐 Enable IP whitelisting on Binance account
- 🔐 Start with paper trading to test everything
- 🔐 Use small amounts for initial live trading

## ⚠️ Important Notes

- **Start with Paper Trading**: Always test strategies with virtual money first
- **Small Live Amounts**: Use small position sizes when starting live trading
- **Monitor Closely**: Keep an eye on the bot especially during initial runs
- **Risk Management**: Never risk more than you can afford to lose

## 📞 Support

For issues or questions:
1. Check the logs for error details
2. Verify configuration settings
3. Test with paper trading first
4. Ensure all dependencies are installed

## 📜 License

This project is for educational and personal use. 

## ⚠️ Disclaimer

**Trading cryptocurrencies involves substantial risk and is not suitable for every investor. Past performance does not guarantee future results. Only trade with money you can afford to lose. This software is provided as-is without any warranty.**
