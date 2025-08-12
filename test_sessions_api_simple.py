#!/usr/bin/env python3
"""
Test script to check the automation sessions API
"""
import requests
import json


def test_sessions_api():
    """Test the sessions API to see if Indian stock sessions appear"""
    try:
        # First, login to get a session
        login_url = "http://127.0.0.1:5000/auth/login"
        session = requests.Session()

        # Get login page to get CSRF token if needed
        login_page = session.get(login_url)

        # Login with test credentials
        login_data = {
            "username": "admin",  # Assuming admin user exists
            "password": "admin",  # Assuming admin password
        }

        login_response = session.post(login_url, data=login_data)

        if login_response.status_code == 200:
            print("✅ Login successful")

            # Now test the sessions API
            sessions_url = "http://127.0.0.1:5000/user/automation/sessions"
            response = session.get(sessions_url)

            if response.status_code == 200:
                data = response.json()
                print("✅ Sessions API responded successfully")
                print(f"Response: {json.dumps(data, indent=2)}")

                # Check if stock sessions are present
                stock_sessions = data.get("data", {}).get("stock_sessions", [])
                crypto_sessions = data.get("data", {}).get("crypto_sessions", [])

                print(f"\n📊 Stock sessions count: {len(stock_sessions)}")
                print(f"📊 Crypto sessions count: {len(crypto_sessions)}")

                if stock_sessions:
                    print("\n🎯 Stock sessions found:")
                    for session in stock_sessions:
                        print(
                            f"  - {session.get('strategy_name', 'Unknown')} | {session.get('symbol', 'No symbol')} | PnL: {session.get('pnl', 0)}"
                        )
                else:
                    print("\n❌ No stock sessions found")

                if crypto_sessions:
                    print("\n🚀 Crypto sessions found:")
                    for session in crypto_sessions:
                        print(
                            f"  - {session.get('strategy_name', 'Unknown')} | {session.get('symbol', 'No symbol')} | PnL: {session.get('pnl', 0)}"
                        )
                else:
                    print("\n❌ No crypto sessions found")

            else:
                print(f"❌ Sessions API failed with status: {response.status_code}")
                print(f"Response: {response.text}")
        else:
            print(f"❌ Login failed with status: {login_response.status_code}")
            print("Trying sessions API without authentication...")

            # Try direct API call
            sessions_url = "http://127.0.0.1:5000/user/automation/sessions"
            response = requests.get(sessions_url)
            print(f"Direct API status: {response.status_code}")
            print(f"Direct API response: {response.text[:200]}...")

    except Exception as e:
        print(f"❌ Error testing sessions API: {e}")


if __name__ == "__main__":
    print("🔍 Testing Automation Sessions API...")
    test_sessions_api()
