"""
Dashboard Launcher
Simple script to start the trading bot dashboard
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.core.config import Config
    from src.dashboard.main import create_app
    from src.core.bot import TradingBot
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install the required dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Main dashboard launcher function."""
    try:
        print("🚀 Starting Crypto Trading Bot Dashboard...")

        # Load configuration
        config_path = project_root / "config" / "config.yaml"
        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            print("Please create a configuration file first.")
            return

        config = Config(str(config_path))
        print("✅ Configuration loaded")

        # Optional: Initialize trading bot
        trading_bot = None
        try:
            trading_bot = TradingBot(config)
            print("✅ Trading bot created")
        except Exception as e:
            print(f"⚠️  Trading bot creation failed: {e}")
            print("Dashboard will run without bot connection")

        # Create dashboard app with bot
        dashboard_app = create_app(config, trading_bot)
        print("✅ Dashboard app created")

        # Connect bot to dashboard if available
        if trading_bot:
            dashboard_app.set_trading_bot(trading_bot)
            print("✅ Trading bot connected to dashboard")

        # Start the dashboard
        print("\n🌐 Dashboard starting at http://127.0.0.1:8001")
        print("📊 Access your trading dashboard in your web browser")
        print("🛑 Press Ctrl+C to stop the dashboard\n")

        dashboard_app.run(host="127.0.0.1", port=8001, debug=True)

    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
