# Quick Start Guide

## Starting the Dashboard (Easiest Way)

```bash
# Start the web dashboard (most common usage)
python main.py --mode dashboard

# Start on custom port
python main.py --mode dashboard --port 8080
```

Then open your browser to: http://127.0.0.1:8002 (or your custom port)

## Other Modes

```bash
# Paper trading (safe practice mode)
python main.py --mode paper --strategy grid_dca

# Live trading (real money - be careful!)
python main.py --mode live --strategy grid_dca

# Run backtest
python main.py --mode backtest --strategy grid_dca

# Get help
python main.py --help
```

## Note

- The old `run.py` file has been removed - everything is now in `main.py`
- Dashboard mode is the recommended way to interact with the bot
- Always test with paper trading before using live mode
