# TradingBot - Advanced Cryptocurrency Trading System

A comprehensive cryptocurrency trading bot with web dashboard, real-time data processing, multiple trading strategies, and advanced risk management features.

## 🚀 Features

### Core Trading Features
- **Multiple Trading Strategies**: Moving Average Crossover, RSI, Grid Trading, DCA (Dollar Cost Averaging)
- **Real-time Market Data**: Live market data integration from Binance API
- **Paper Trading Mode**: Test strategies safely without real money
- **Live Trading Mode**: Execute real trades with comprehensive risk controls
- **Advanced Order Management**: Create, modify, cancel, and monitor orders
- **Portfolio Management**: Real-time balance tracking and P&L analysis

### Dashboard & Interface
- **Modern Web Dashboard**: Responsive, real-time trading interface
- **Live Data Visualization**: Charts, market data, and portfolio metrics
- **Settings Management**: Configurable trading parameters and risk controls
- **Real-time Updates**: WebSocket connections for instant data updates
- **Mobile-Friendly**: Optimized for desktop and mobile devices

### Data & Analytics
- **Database Integration**: MySQL storage for all trading data and history
- **Performance Analytics**: Detailed trading statistics and performance metrics
- **Trade History**: Complete record of all executed trades
- **Market Data Storage**: Historical price data for backtesting and analysis

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

### 1. Start the Web Dashboard
```bash
# Navigate to project directory
cd tradingbot

# Start the dashboard
python run.py
```

### 2. Or use Windows Batch Files
- **Dashboard**: Double-click `start_dashboard.bat`
- **Trading Bot**: Double-click `start_bot.bat`

### 3. Access the Dashboard
Open your browser and go to: `http://localhost:8080`

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

## 📦 Git Repository Setup

This project is ready to be uploaded to GitHub. Follow these steps to create your repository:

### 1. Create GitHub Repository
1. Go to [GitHub](https://github.com) and log in to your account
2. Click the "+" icon in the top right corner and select "New repository"
3. Set the repository name to `tradingbot`
4. Add a description: "Advanced Cryptocurrency Trading Bot with Web Dashboard"
5. Choose "Public" or "Private" based on your preference
6. **Do NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

### 2. Connect Local Repository to GitHub
```bash
# Add the remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/tradingbot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 3. Repository Features
- ✅ Git repository initialized
- ✅ `.gitignore` configured to exclude sensitive files
- ✅ Environment variables protected (`.env` excluded)
- ✅ Virtual environment excluded (`venv/` in .gitignore)
- ✅ All source code and documentation included
- ✅ Ready for collaborative development

## 🏗️ Project Structure

```
tradingbot/
├── main.py                 # Main trading bot entry point
├── run.py                  # Web dashboard launcher
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── config/                # Configuration files
├── src/
│   ├── core/              # Core bot logic and configuration
│   ├── dashboard/         # Web dashboard and API
│   ├── data/             # Data management and database
│   ├── execution/        # Order and portfolio management
│   ├── strategies/       # Trading strategies
│   ├── risk/             # Risk management
│   ├── notifications/    # Alerts and notifications
│   ├── backtesting/      # Strategy backtesting
│   └── utils/            # Utilities and helpers
├── setup_env.bat         # Windows environment setup
├── start_bot.bat         # Start trading bot (Windows)
└── start_dashboard.bat   # Start web dashboard (Windows)
```

## 🚀 Deployment Options

### Local Development
- Current setup is ready for local development
- Uses XAMPP MySQL database
- Run dashboard: `python run.py`

### Production Deployment
For production deployment, consider:
- **VPS/Cloud Server**: Deploy on DigitalOcean, AWS, or similar
- **Docker**: Containerize the application
- **Database**: Use managed MySQL or PostgreSQL
- **Process Management**: Use PM2, systemd, or supervisor
- **SSL/HTTPS**: Secure the web dashboard
- **Monitoring**: Add logging and health checks

## 🔒 Security

- 🔐 Never commit API keys to version control
- 🔐 Use environment variables for sensitive data
- 🔐 Enable IP whitelisting on Binance account
- 🔐 Start with paper trading to test everything
- 🔐 Use small amounts for initial live trading
- 🔐 Keep `.env` file local and secure
- 🔐 Use strong passwords for database access

## ⚠️ Important Notes

- **Start with Paper Trading**: Always test strategies with virtual money first
- **Small Live Amounts**: Use small position sizes when starting live trading
- **Monitor Closely**: Keep an eye on the bot especially during initial runs
- **Risk Management**: Never risk more than you can afford to lose
- **Backup Data**: Regularly backup your database and configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For issues or questions:
1. Check the logs for error details
2. Verify configuration settings
3. Test with paper trading first
4. Create an issue on GitHub
5. Check documentation and README files
4. Ensure all dependencies are installed

## 📜 License

This project is for educational and personal use. 

## ⚠️ Disclaimer

**Trading cryptocurrencies involves substantial risk and is not suitable for every investor. Past performance does not guarantee future results. Only trade with money you can afford to lose. This software is provided as-is without any warranty.**
