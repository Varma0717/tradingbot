# Quick Start Guide

## 🚀 Start Trading in 3 Steps

### 1. Start Dashboard
```bash
python start_dashboard.py
```
📊 Dashboard: http://127.0.0.1:8004

### 2. Choose Trading Mode

**Paper Trading (Safe Testing):**
```bash
python start_bot.py --mode paper
```

**Real Trading (Live Money):**
```bash
python start_bot.py --mode live
```

### 3. Monitor & Control
- Use the web dashboard to monitor trades
- Start/stop strategies through the interface
- View real-time portfolio performance

## 📈 Available Strategies
- **Grid DCA**: Dollar-cost averaging with grid levels
- **RSI**: Relative Strength Index based trades
- **MA Crossover**: Moving average crossover signals

## ⚠️ Important Notes
- Always test with paper trading before using live mode
- Ensure you have sufficient balance for live trading
- Monitor your trades regularly
