#!/usr/bin/env python3
"""
Test the current sessions API response to see what the automation page is receiving
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time


def test_sessions_api():
    print("=== Testing Live Sessions API Response ===")

    try:
        # Test the sessions endpoint
        url = "http://127.0.0.1:5000/user/automation/sessions"

        print(f"Making request to: {url}")
        response = requests.get(url)

        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response Data:")
            print(json.dumps(data, indent=2))

            # Analyze the response
            if data.get("success"):
                sessions_data = data.get("data", {})
                crypto_sessions = sessions_data.get("crypto_sessions", [])
                stock_sessions = sessions_data.get("stock_sessions", [])

                print(f"\n=== Analysis ===")
                print(f"Crypto Sessions: {len(crypto_sessions)}")
                print(f"Stock Sessions: {len(stock_sessions)}")

                for i, session in enumerate(crypto_sessions):
                    print(
                        f"  Crypto Session {i+1}: {session['strategy_name']} - {session['symbol']} - P&L: ${session['pnl']}"
                    )

                for i, session in enumerate(stock_sessions):
                    print(
                        f"  Stock Session {i+1}: {session['strategy_name']} - {session['symbol']} - P&L: ₹{session['pnl']}"
                    )
            else:
                print(
                    f"API returned success=False: {data.get('message', 'Unknown error')}"
                )
        else:
            print(f"HTTP Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Flask app. Is it running on port 5000?")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_sessions_api()
