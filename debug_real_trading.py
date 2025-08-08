#!/usr/bin/env python3
"""
Debug Real Trading Initialization

Step-by-step debugging of the real trading initialization process.
"""

import asyncio
import os
import sys
import logging

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def debug_initialization():
    """Debug each step of the initialization process."""

    print("🔍 Debugging Real Trading Initialization")
    print("=" * 60)

    # Step 1: Check environment variables
    print("1️⃣ Checking Environment Variables:")
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_SECRET_KEY")

    if api_key and api_secret:
        print(f"   ✅ BINANCE_API_KEY: {api_key[:8]}...")
        print(f"   ✅ BINANCE_SECRET_KEY: {api_secret[:8]}...")
    else:
        print("   ❌ API keys not found!")
        return False

    # Step 2: Test RealBinanceExchange
    print("\n2️⃣ Testing RealBinanceExchange:")
    try:
        from src.exchanges.real_binance import RealBinanceExchange

        exchange = RealBinanceExchange()
        print("   ✅ RealBinanceExchange created")

        # Test connection
        connected = await exchange.connect()
        if connected:
            print("   ✅ Exchange connection successful")

            # Test balance
            balance = await exchange.get_account_balance("USDT")
            print(f"   ✅ Balance retrieved: ${balance:.2f}")

        else:
            print("   ❌ Exchange connection failed")
            return False

    except Exception as e:
        print(f"   ❌ RealBinanceExchange error: {e}")
        return False

    # Step 3: Test RealUniversalGridDCAStrategy
    print("\n3️⃣ Testing RealUniversalGridDCAStrategy:")
    try:
        from src.strategies.real_universal_strategy import RealUniversalGridDCAStrategy

        strategy = RealUniversalGridDCAStrategy(2.16, exchange)
        print("   ✅ RealUniversalGridDCAStrategy created")

    except Exception as e:
        print(f"   ❌ RealUniversalGridDCAStrategy error: {e}")
        return False

    # Step 4: Test RealStrategyManager
    print("\n4️⃣ Testing RealStrategyManager:")
    try:
        from src.strategies.real_strategy_manager import RealStrategyManager

        manager = RealStrategyManager(2.16)
        print("   ✅ RealStrategyManager created")

        # Test initialization
        success = await manager.initialize()
        if success:
            print("   ✅ RealStrategyManager initialized successfully")
        else:
            print("   ❌ RealStrategyManager initialization failed")
            return False

    except Exception as e:
        print(f"   ❌ RealStrategyManager error: {e}")
        import traceback

        print(f"   📋 Traceback: {traceback.format_exc()}")
        return False

    # Step 5: Test Real Trading Integration
    print("\n5️⃣ Testing Real Trading Integration:")
    try:
        from src.dashboard.real_trading_integration import real_trading_integrator

        success = await real_trading_integrator.initialize_real_trading()
        if success:
            print("   ✅ Real trading integration successful")
        else:
            print("   ❌ Real trading integration failed")
            return False

    except Exception as e:
        print(f"   ❌ Real trading integration error: {e}")
        import traceback

        print(f"   📋 Traceback: {traceback.format_exc()}")
        return False

    print("\n🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
    print("Real trading should now work in the dashboard.")
    return True


if __name__ == "__main__":
    success = asyncio.run(debug_initialization())
    if not success:
        print("\n❌ Fix the issues above before trying real trading")
        sys.exit(1)
    else:
        print("\n✅ Ready for real trading!")
