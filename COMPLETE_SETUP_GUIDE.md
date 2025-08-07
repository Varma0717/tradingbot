# 🚀 Crypto Trading Bot - Complete Setup & Configuration Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [API Keys Configuration](#api-keys-configuration)
6. [Running the Bot](#running-the-bot)
7. [Making Templates Dynamic](#making-templates-dynamic)
8. [Troubleshooting](#troubleshooting)
9. [Testing](#testing)

---

## 🔧 Prerequisites

### Required Software
- **Python 3.8+** (Download from [python.org](https://python.org))
- **XAMPP** (MySQL Server) - [Download from apachefriends.org](https://www.apachefriends.org)
- **Git** (for version control)
- **Text Editor** (VS Code recommended)

### Knowledge Requirements
- Basic Python understanding
- Basic understanding of cryptocurrency trading concepts
- Basic MySQL/Database concepts

---

## 🌐 Environment Setup

### 1. Clone and Install Dependencies

```bash
# Navigate to your project directory
cd c:\xampp\htdocs\application

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Environment File

```bash
# Copy the example environment file
copy .env.example .env
```

**Edit the `.env` file with your actual values:**

```bash
# Exchange API Keys (Required for live trading)
BINANCE_API_KEY=your_actual_binance_api_key
BINANCE_SECRET_KEY=your_actual_binance_secret_key
BINANCE_SANDBOX=true

# Database (XAMPP MySQL)
DATABASE_URL=mysql+pymysql://root:@localhost:3306/crypto_trading_bot
DB_HOST=localhost
DB_PORT=3306
DB_NAME=crypto_trading_bot
DB_USER=root
DB_PASSWORD=

# Notifications (Optional)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Development
DEBUG=true
LOG_LEVEL=INFO
```

---

## ⚙️ Configuration

### 1. Trading Mode Configuration

Edit `config/config.yaml`:

```yaml
trading:
  mode: paper  # Start with paper trading (safe)
  exchange: binance
  base_currency: USDT
  paper_balance: 10000.0  # Virtual balance for testing
```

### 2. Strategy Configuration

```yaml
strategies:
  ma_crossover:
    enabled: true
    symbol: BTC/USDT
    timeframe: 1h
    fast_ma: 20
    slow_ma: 50
```

---

## 🗄️ Database Setup

### 1. Start XAMPP Services

1. Open **XAMPP Control Panel**
2. Start **Apache** service
3. Start **MySQL** service
4. Click **Admin** next to MySQL (opens phpMyAdmin)

### 2. Create Database

In phpMyAdmin:
```sql
CREATE DATABASE crypto_trading_bot;
USE crypto_trading_bot;

-- Tables will be created automatically by the bot
```

### 3. Verify Database Connection

```bash
# Test database connection
python -c "
from src.core.config import Config
from src.data.database import Database
config = Config('config/config.yaml')
db = Database(config)
print('Database connection successful!')
"
```

---

## 🔑 API Keys Configuration

### 1. Binance API Keys (Required)

1. **Create Binance Account**: [binance.com](https://binance.com)
2. **Enable 2FA** (Two-Factor Authentication)
3. **Create API Key**:
   - Go to Account → API Management
   - Create API Key
   - **Important**: Enable "Enable Spot & Margin Trading" for paper trading
   - **Restrict to IP** (optional but recommended)

4. **Configure in .env**:
```bash
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_SECRET_KEY=your_actual_secret_key_here
BINANCE_SANDBOX=true  # Keep true for testing
```

### 2. Test API Connection

```bash
# Test API connection
python -c "
from src.execution.binance_engine import BinanceEngine
from src.core.config import Config
config = Config('config/config.yaml')
engine = BinanceEngine(config)
print('API connection successful!')
print('Account info:', engine.get_account_balance())
"
```

---

## 🚀 Running the Bot

### 1. Start the Dashboard

```bash
# Activate virtual environment
venv\Scripts\activate

# Start dashboard
python run.py
```

The dashboard will be available at: **http://127.0.0.1:8000**

### 2. Start the Trading Bot

The bot starts automatically when you click "Start" in the dashboard, but you can also run it separately:

```bash
# Run bot separately (optional)
python -c "
from src.core.config import Config
from src.core.bot import TradingBot
import asyncio

async def main():
    config = Config('config/config.yaml')
    bot = TradingBot(config)
    await bot.start()

asyncio.run(main())
"
```

---

## 📊 Making Templates Dynamic

### Problem: Static Data Display

The templates currently show static data (always $0.00, 0 trades, etc.). Here's how to make them dynamic:

### 1. Portfolio Template Dynamic Updates

The portfolio data is fetched from `/api/portfolio` endpoint. To make it work:

**Backend API** (already implemented in `api_routes.py`):
```python
@router.get("/portfolio")
async def get_portfolio_data():
    # Returns real portfolio data
```

**Frontend JavaScript** (in dashboard.js):
```javascript
// Update portfolio data every 30 seconds
setInterval(loadPortfolioData, 30000);

function loadPortfolioData() {
    fetch('/api/portfolio')
        .then(response => response.json())
        .then(data => updatePortfolioDisplay(data));
}
```

### 2. Trades Template Dynamic Updates

**API Endpoint**: `/api/trades`
**Updates**: Trade history, P&L, win rates

### 3. Strategies Template Dynamic Updates

**API Endpoint**: `/api/strategies`
**Updates**: Strategy performance, active strategies

### 4. Grid DCA Template Dynamic Updates

**API Endpoint**: `/api/grid-dca`
**Updates**: Grid status, DCA progress

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. "Bot Always Shows Stopped"

**Cause**: Bot not properly initialized or API connection failed

**Solution**:
```bash
# Check logs
tail -f logs/trading_bot.log

# Verify API keys
python -c "
import os
print('API Key:', os.getenv('BINANCE_API_KEY', 'NOT SET'))
print('Secret Key:', 'SET' if os.getenv('BINANCE_SECRET_KEY') else 'NOT SET')
"

# Test API connection
python test_api_connection.py
```

#### 2. "Database Connection Error"

**Solution**:
1. Ensure XAMPP MySQL is running
2. Verify database exists: `crypto_trading_bot`
3. Check `.env` database settings

#### 3. "Import Errors"

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 4. "Static Data in Templates"

**Solution**: Enable WebSocket connections and API data fetching:

```yaml
# In config.yaml
data:
  websocket_enabled: true
  sources:
    - exchange
    - websocket
```

---

## 🧪 Testing

### 1. Test Bot Components

```bash
# Test configuration
python -m pytest tests/test_config.py

# Test database
python -m pytest tests/test_database.py

# Test API
python -m pytest tests/test_api.py
```

### 2. Test Dashboard

1. Open browser: `http://127.0.0.1:8000`
2. Check all pages load
3. Verify data updates (should see real numbers, not $0.00)
4. Test bot start/stop functionality

### 3. Test Trading (Paper Mode)

1. Set `mode: paper` in config.yaml
2. Start bot
3. Monitor trades in dashboard
4. Check logs for trading activity

---

## 📈 Next Steps

### After Basic Setup Works:

1. **Fine-tune Strategies**: Adjust parameters in `config.yaml`
2. **Enable Live Trading**: Change `mode: live` (only after thorough testing)
3. **Set Up Notifications**: Configure email/Telegram alerts
4. **Monitor Performance**: Use dashboard analytics
5. **Backup Data**: Regular database backups

### Advanced Features:

1. **Custom Strategies**: Develop new trading strategies
2. **Risk Management**: Fine-tune risk parameters
3. **Backtesting**: Test strategies on historical data
4. **Multi-Exchange**: Add support for multiple exchanges

---

## 🆘 Getting Help

### If You Still Have Issues:

1. **Check Logs**: `logs/trading_bot.log`
2. **Review Configuration**: Ensure all required fields are set
3. **Test Components Individually**: Use the test scripts provided
4. **Consult Documentation**: Review inline code comments

### Debug Commands:

```bash
# Check system status
python debug_system.py

# Test all components
python test_all_components.py

# Reset database
python reset_database.py
```

---

## ⚠️ Important Warnings

1. **Start with Paper Trading**: Never use real money until thoroughly tested
2. **Secure API Keys**: Never commit API keys to version control
3. **Monitor Closely**: Watch the bot closely when first running
4. **Have Stop-Loss**: Always set appropriate risk limits
5. **Regular Backups**: Backup your configuration and database regularly

---

## 📞 Support

For additional help:
- Review the code documentation
- Check the logs for error messages
- Test each component individually
- Ensure all prerequisites are properly installed

**Remember**: This is a sophisticated trading system. Take time to understand each component before using with real money.
