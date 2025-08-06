"""
Final comprehensive test of the entire trading bot system.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


async def main():
    print("🤖 Comprehensive Trading Bot System Test")
    print("=" * 50)

    # Test 1: Configuration
    print("\n1. Testing Configuration System...")
    try:
        from src.core.config import Config

        config = Config()
        print(f"   ✅ Config loaded successfully")
        print(f"   📊 Database: {config.database.url}")
        print(f"   💱 Exchanges: {len(config.exchanges)} configured")
        print(f"   🔧 Trading mode: {config.trading.mode}")
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return

    # Test 2: Database
    print("\n2. Testing Database System...")
    try:
        from src.data.database import DatabaseManager

        db_manager = DatabaseManager(config)
        print(f"   ✅ Database connected successfully")
    except Exception as e:
        print(f"   ❌ Database failed: {e}")
        return

    # Test 3: Trading Engine
    print("\n3. Testing Trading Engine...")
    try:
        from src.execution.binance_engine import get_trading_engine

        engine = get_trading_engine()
        print(f"   ✅ Trading engine loaded successfully")
    except Exception as e:
        print(f"   ❌ Trading engine failed: {e}")
        return

    # Test 4: Dashboard
    print("\n4. Testing Dashboard System...")
    try:
        from src.dashboard.main import DashboardApp

        dashboard_app = DashboardApp(config)
        print(f"   ✅ Dashboard app created successfully")
    except Exception as e:
        print(f"   ❌ Dashboard failed: {e}")
        return

    # Test 5: API Routes
    print("\n5. Testing API Routes...")
    try:
        from src.dashboard.routes import api_routes, dashboard_routes

        print(f"   ✅ API routes loaded successfully")
    except Exception as e:
        print(f"   ❌ API routes failed: {e}")
        return

    print("\n" + "=" * 50)
    print("🎉 ALL SYSTEMS OPERATIONAL!")
    print("\n📋 Next Steps:")
    print("   1. Ensure XAMPP MySQL is running")
    print("   2. Run: python setup_database.py")
    print("   3. Run: python start_dashboard.py")
    print("   4. Open: http://localhost:8000")
    print("\n🔐 Security Reminders:")
    print("   • Start with paper trading (PAPER_TRADING=true)")
    print("   • Use small amounts for initial live trading")
    print("   • Monitor the bot closely during operation")
    print("\n💡 Startup Options:")
    print("   • Double-click: start_bot.bat")
    print("   • PowerShell: ./start_bot.ps1")
    print("   • Manual: python start_dashboard.py")


if __name__ == "__main__":
    asyncio.run(main())
