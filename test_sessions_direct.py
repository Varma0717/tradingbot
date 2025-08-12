#!/usr/bin/env python3
"""
Test the current sessions API response
"""
import requests
import json
import sys


def test_sessions_directly():
    """Test sessions API directly"""
    try:
        # Test sessions API directly (will need authentication)
        url = "http://127.0.0.1:5000/user/automation/sessions"
        response = requests.get(url, timeout=10)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")

        if response.status_code == 200:
            try:
                data = response.json()
                if "data" in data:
                    stock_sessions = data["data"].get("stock_sessions", [])
                    crypto_sessions = data["data"].get("crypto_sessions", [])

                    print(f"\n📊 Stock sessions: {len(stock_sessions)}")
                    print(f"📊 Crypto sessions: {len(crypto_sessions)}")

                    if stock_sessions:
                        print("✅ Indian stock sessions found!")
                        for session in stock_sessions:
                            print(f"  - {session}")
                    else:
                        print("❌ No stock sessions in response")

                    if crypto_sessions:
                        print("✅ Crypto sessions found!")
                        print(
                            f"  Sample: {crypto_sessions[0] if crypto_sessions else 'None'}"
                        )

                else:
                    print("❌ No 'data' field in response")

            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🔍 Testing Sessions API...")
    test_sessions_directly()
