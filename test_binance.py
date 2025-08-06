"""Test Binance API connection and configuration."""

import ccxt
import os
from src.core.config import Config


def test_binance_connection():
    """Test Binance API connection."""
    try:
        # Load configuration
        config = Config()

        print("🔧 Testing Binance API Connection...")
        print(f"Exchange: {config.exchange.name}")
        print(f"Sandbox Mode: {config.exchange.sandbox}")
        print(f"API Key Present: {'Yes' if config.exchange.api_key else 'No'}")
        print(f"Secret Key Present: {'Yes' if config.exchange.secret_key else 'No'}")

        # Create exchange instance
        exchange_config = {
            "apiKey": config.exchange.api_key,
            "secret": config.exchange.secret_key,
            "sandbox": config.exchange.sandbox,
            "enableRateLimit": True,
        }

        exchange = ccxt.binance(exchange_config)

        print("\n📡 Testing connection...")

        # Test 1: Fetch server time (no auth required)
        server_time = exchange.fetch_time()
        print(f"✅ Server Time: {server_time}")

        # Test 2: Fetch ticker (no auth required)
        ticker = exchange.fetch_ticker("BTC/USDT")
        print(f"✅ BTC/USDT Price: ${ticker['last']:,.2f}")

        # Test 3: Check if API keys are provided for account tests
        if config.exchange.api_key and config.exchange.secret_key:
            print("\n🔐 Testing authenticated endpoints...")

            # Test account balance (requires auth)
            balance = exchange.fetch_balance()
            print("✅ Account access successful")
            print(f"   Available currencies: {list(balance['total'].keys())}")

            # Test trading permissions (if in live mode)
            if not config.exchange.sandbox:
                print("⚠️  WARNING: Live trading mode detected!")
                print("   Make sure you want to use real money")
            else:
                print("✅ Sandbox mode active - safe for testing")

        else:
            print("\n⚠️  No API keys configured - only public data available")
            print(
                "   Add your Binance API keys to .env file to test authenticated features"
            )

        print("\n🎉 Connection test completed successfully!")
        return True

    except ccxt.AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("   Check your API key and secret in .env file")
        return False

    except ccxt.NetworkError as e:
        print(f"\n❌ Network Error: {e}")
        print("   Check your internet connection")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_binance_connection()
