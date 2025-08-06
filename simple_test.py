"""Simple Binance API test."""

import ccxt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def simple_binance_test():
    """Simple test of Binance API connection."""
    try:
        print("🔧 Simple Binance API Test")
        print("=" * 40)

        # Get API keys from environment
        api_key = os.getenv("BINANCE_API_KEY", "")
        secret_key = os.getenv("BINANCE_SECRET_KEY", "")
        sandbox = os.getenv("BINANCE_SANDBOX", "true").lower() == "true"

        print(f"API Key Present: {'Yes' if api_key else 'No'}")
        print(f"Secret Key Present: {'Yes' if secret_key else 'No'}")
        print(f"Sandbox Mode: {sandbox}")

        # Create exchange instance
        exchange = ccxt.binance(
            {
                "apiKey": api_key,
                "secret": secret_key,
                "sandbox": sandbox,
                "enableRateLimit": True,
            }
        )

        print("\n📡 Testing public endpoints...")

        # Test 1: Server time (no auth needed)
        try:
            server_time = exchange.fetch_time()
            print("✅ Server connection successful")
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            return False

        # Test 2: Fetch ticker (no auth needed)
        try:
            ticker = exchange.fetch_ticker("BTC/USDT")
            print(f"✅ BTC/USDT Price: ${ticker['last']:,.2f}")
        except Exception as e:
            print(f"❌ Ticker fetch failed: {e}")
            return False

        # Test 3: If API keys provided, test account access
        if api_key and secret_key:
            print("\n🔐 Testing authenticated endpoints...")
            try:
                balance = exchange.fetch_balance()
                print("✅ Account access successful!")

                # Show available balances
                total = balance.get("total", {})
                non_zero = {k: v for k, v in total.items() if v > 0}
                if non_zero:
                    print("   Balances:")
                    for currency, amount in non_zero.items():
                        print(f"     {currency}: {amount}")
                else:
                    print("   No balances found (this is normal for testnet)")

            except ccxt.AuthenticationError as e:
                print(f"❌ Authentication failed: {e}")
                print("   Check your API key and secret")
                return False
            except Exception as e:
                print(f"❌ Account access failed: {e}")
                return False
        else:
            print("\n⚠️  No API keys provided - only public data tested")

        print("\n🎉 Test completed successfully!")

        if sandbox:
            print("\n💡 You're using sandbox mode - safe for testing!")
        else:
            print("\n⚠️  WARNING: Live mode detected - be careful with real money!")

        return True

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    simple_binance_test()
