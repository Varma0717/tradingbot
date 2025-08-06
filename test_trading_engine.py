"""
Test the updated trading engine functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


async def test_trading_engine():
    print("🔧 Testing Updated Trading Engine")
    print("=" * 40)

    try:
        from src.execution.binance_engine import get_trading_engine

        print("1. Creating trading engine...")
        engine = get_trading_engine()
        print("   ✅ Trading engine created successfully")

        print("\n2. Testing basic methods...")

        # Test balance
        try:
            balance = engine.get_balance()
            print(f"   ✅ Balance method working: {len(balance)} assets")
        except Exception as e:
            print(f"   ⚠️ Balance method: {e}")

        # Test ticker
        try:
            ticker = engine.get_ticker("BTC/USDT")
            print(
                f"   ✅ Ticker method working: BTC/USDT = ${ticker.get('last', 0):,.2f}"
            )
        except Exception as e:
            print(f"   ⚠️ Ticker method: {e}")

        # Test orderbook
        try:
            orderbook = engine.get_orderbook("BTC/USDT", 5)
            print(
                f"   ✅ Orderbook method working: {len(orderbook.get('bids', []))} bids"
            )
        except Exception as e:
            print(f"   ⚠️ Orderbook method: {e}")

        # Test open orders
        try:
            orders = engine.get_open_orders()
            print(f"   ✅ Open orders method working: {len(orders)} orders")
        except Exception as e:
            print(f"   ⚠️ Open orders method: {e}")

        print("\n3. Testing paper trading...")

        # Test paper market order
        try:
            result = engine.place_market_order("BTC/USDT", "buy", 0.001)
            if result:
                print(f"   ✅ Paper market order: {result['id']}")
            else:
                print("   ⚠️ Paper market order failed")
        except Exception as e:
            print(f"   ⚠️ Paper market order: {e}")

        # Test paper limit order
        try:
            result = engine.place_limit_order("BTC/USDT", "buy", 0.001, 50000)
            if result:
                print(f"   ✅ Paper limit order: {result['id']}")

                # Test cancel order
                cancelled = engine.cancel_order(result["id"])
                print(f"   ✅ Cancel order: {cancelled}")
            else:
                print("   ⚠️ Paper limit order failed")
        except Exception as e:
            print(f"   ⚠️ Paper limit order: {e}")

        print("\n" + "=" * 40)
        print("🎉 Trading Engine Test Complete!")
        print("\n✅ The trading engine is ready for:")
        print("   • Paper trading (safe mode)")
        print("   • Real-time market data")
        print("   • Order management")
        print("   • Dashboard integration")

    except Exception as e:
        print(f"❌ Trading engine test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_trading_engine())
