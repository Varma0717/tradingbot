"""
Test script to check Binance API credentials and signature generation
"""

import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode


def test_binance_api():
    # Test with sample credentials (replace with your actual ones)
    API_KEY = "your_actual_api_key_here"
    API_SECRET = "your_actual_secret_here"

    # Use testnet for testing
    BASE_URL = "https://testnet.binance.vision/api"

    if API_KEY == "your_actual_api_key_here":
        print(
            "Please update the API_KEY and API_SECRET with your actual Binance credentials"
        )
        return

    def generate_signature(query_string, secret):
        return hmac.new(
            secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def get_server_time():
        response = requests.get(f"{BASE_URL}/v3/time")
        return response.json()["serverTime"]

    try:
        # Get server time
        server_time = get_server_time()
        print(f"Server time: {server_time}")

        # Test account endpoint
        timestamp = server_time
        params = {"timestamp": timestamp}

        query_string = urlencode(params)
        signature = generate_signature(query_string, API_SECRET)
        params["signature"] = signature

        headers = {"X-MBX-APIKEY": API_KEY}

        response = requests.get(
            f"{BASE_URL}/v3/account", headers=headers, params=params
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ API credentials are valid!")
            account_info = response.json()
            print(f"Account Type: {account_info.get('accountType')}")
            print(f"Can Trade: {account_info.get('canTrade')}")
        else:
            print(f"❌ API request failed: {response.text}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Testing Binance API connectivity...")
    test_binance_api()
