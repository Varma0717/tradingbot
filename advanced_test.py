"""Advanced Binance API diagnostics."""

import ccxt
import os
import hashlib
import hmac
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def advanced_binance_test():
    """Advanced Binance API diagnostics."""

    print("🔬 Advanced Binance API Diagnostics")
    print("=" * 50)

    # Get API keys from environment
    api_key = os.getenv("BINANCE_API_KEY", "")
    secret_key = os.getenv("BINANCE_SECRET_KEY", "")

    print(f"API Key: {api_key[:8]}...{api_key[-8:] if len(api_key) > 16 else 'SHORT'}")
    print(
        f"Secret Key: {secret_key[:8]}...{secret_key[-8:] if len(secret_key) > 16 else 'SHORT'}"
    )
    print(f"API Key Length: {len(api_key)}")
    print(f"Secret Key Length: {len(secret_key)}")

    # Test 1: Check API key format
    print("\n📝 API Key Format Check:")
    if len(api_key) == 64:
        print("✅ API key length is correct (64 characters)")
    else:
        print(f"❌ API key length is incorrect. Expected 64, got {len(api_key)}")

    if len(secret_key) == 64:
        print("✅ Secret key length is correct (64 characters)")
    else:
        print(f"❌ Secret key length is incorrect. Expected 64, got {len(secret_key)}")

    # Test 2: Test both sandbox modes
    print("\n🧪 Testing Different Modes:")

    for sandbox_mode in [True, False]:
        mode_name = "Testnet" if sandbox_mode else "Mainnet"
        print(f"\n--- Testing {mode_name} ---")

        try:
            exchange = ccxt.binance(
                {
                    "apiKey": api_key,
                    "secret": secret_key,
                    "sandbox": sandbox_mode,
                    "enableRateLimit": True,
                }
            )

            # Test server time first
            server_time = exchange.fetch_time()
            print(f"✅ {mode_name} server time: OK")

            # Test account endpoint
            balance = exchange.fetch_balance()
            print(f"✅ {mode_name} authentication: SUCCESS!")

            # Show account info
            info = balance.get("info", {})
            if "accountType" in info:
                print(f"   Account Type: {info['accountType']}")
            if "canTrade" in info:
                print(f"   Can Trade: {info['canTrade']}")
            if "canWithdraw" in info:
                print(f"   Can Withdraw: {info['canWithdraw']}")
            if "canDeposit" in info:
                print(f"   Can Deposit: {info['canDeposit']}")

        except ccxt.AuthenticationError as e:
            print(f"❌ {mode_name} authentication failed: {e}")
        except Exception as e:
            print(f"❌ {mode_name} error: {e}")

    # Test 3: Manual signature test (for mainnet)
    print("\n🔐 Manual Signature Test:")
    try:
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            secret_key.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        url = "https://api.binance.com/api/v3/account"
        headers = {"X-MBX-APIKEY": api_key}
        params = {"timestamp": timestamp, "signature": signature}

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            print("✅ Manual signature test: SUCCESS!")
            data = response.json()
            print(f"   Account Type: {data.get('accountType', 'Unknown')}")
            print(f"   Can Trade: {data.get('canTrade', 'Unknown')}")
        else:
            print(f"❌ Manual signature test failed: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ Manual signature test error: {e}")

    # Test 4: Check IP
    print("\n🌐 IP Address Check:")
    try:
        ip_response = requests.get("https://api.ipify.org?format=json", timeout=10)
        if ip_response.status_code == 200:
            current_ip = ip_response.json()["ip"]
            print(f"✅ Current IP: {current_ip}")
        else:
            print("❌ Could not determine IP")
    except Exception as e:
        print(f"❌ IP check failed: {e}")

    # Test 5: Testnet-specific test
    print("\n🧪 Binance Testnet Specific Test:")
    try:
        # For testnet, we need to use the testnet URL
        testnet_exchange = ccxt.binance(
            {
                "apiKey": api_key,
                "secret": secret_key,
                "sandbox": True,
                "enableRateLimit": True,
                "urls": {
                    "api": {
                        "public": "https://testnet.binance.vision/api",
                        "private": "https://testnet.binance.vision/api",
                    }
                },
            }
        )

        balance = testnet_exchange.fetch_balance()
        print("✅ Testnet with explicit URLs: SUCCESS!")

    except Exception as e:
        print(f"❌ Testnet explicit URL test failed: {e}")


if __name__ == "__main__":
    advanced_binance_test()
