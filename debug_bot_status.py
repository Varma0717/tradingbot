#!/usr/bin/env python3
"""
Debug script to test bot status and data flow
"""
import requests
import time
import json


def test_api_endpoints():
    """Test the trading bot API endpoints"""
    base_url = "http://127.0.0.1:5000"

    # Test if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server is running: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return

    # Test sessions endpoint (this should show real data)
    try:
        response = requests.get(f"{base_url}/user/automation/sessions", timeout=10)
        print(f"\n📊 Trading Sessions API:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            if data.get("success"):
                sessions = data.get("data", {})
                print(f"Stock sessions: {len(sessions.get('stock_sessions', []))}")
                print(f"Crypto sessions: {len(sessions.get('crypto_sessions', []))}")
                if sessions.get("crypto_sessions"):
                    print("Crypto sessions data:")
                    for session in sessions["crypto_sessions"][:2]:  # Show first 2
                        print(f"  - {session}")
            else:
                print(f"Error: {data.get('message')}")
        else:
            print(f"HTTP Error: {response.text}")
    except Exception as e:
        print(f"❌ Sessions API error: {e}")

    # Test crypto status
    try:
        response = requests.get(f"{base_url}/user/crypto/status", timeout=10)
        print(f"\n🔄 Crypto Status API:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            if data.get("success"):
                status = data.get("status", {})
                print(f"Bot running: {status.get('is_running')}")
                print(f"Active strategies: {len(status.get('active_strategies', {}))}")
        else:
            print(f"HTTP Error: {response.text}")
    except Exception as e:
        print(f"❌ Crypto Status API error: {e}")


if __name__ == "__main__":
    print("🔍 Testing TradeMantra Bot Status...")
    test_api_endpoints()
    print("\n✅ Test completed!")
