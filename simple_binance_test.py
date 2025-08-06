"""Simple Binance API test."""

import ccxt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def simple_binance_test():
    """Simple test of Binance API."""

    print("🔧 Simple Binance API Test")
    print("=" * 40)

    # Get API keys from environment
    api_key = os.getenv("BINANCE_API_KEY", "")
    secret_key = os.getenv("BINANCE_SECRET_KEY", "")
    sandbox = os.getenv("BINANCE_SANDBOX", "true").lower() == "true"

    print(f"API Key Present: {'Yes' if api_key else 'No'}")
    print(f"Secret Key Present: {'Yes' if secret_key else 'No'}")
    print(f"Sandbox Mode: {sandbox}")

    try:
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

        # Test public endpoint
        ticker = exchange.fetch_ticker("BTC/USDT")
        print("✅ Server connection successful")
        print(f"✅ BTC/USDT Price: ${ticker['last']:,.2f}")

        if api_key and secret_key:
            print("\n🔐 Testing authenticated endpoints...")

            # Test authenticated endpoint
            balance = exchange.fetch_balance()
            print("✅ Authentication successful!")
            print(f"✅ Account access granted")

            # Show available balances
            total_balance = balance.get("total", {})
            available_currencies = [
                curr for curr, amount in total_balance.items() if amount > 0
            ]

            if available_currencies:
                print(f"💰 Available currencies: {', '.join(available_currencies)}")
            else:
                print("💰 No balances found (normal for new accounts)")

        else:
            print("\n⚠️ No API keys provided - skipping authenticated tests")

    except ccxt.AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("   Check your API key and secret")
        print("   Make sure IP restrictions allow your IP: 183.83.168.141")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    simple_binance_test()
