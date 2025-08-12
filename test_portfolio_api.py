#!/usr/bin/env python3
"""
Test the portfolio API endpoint to see what data is being returned
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json


def test_portfolio_api():
    """Test the portfolio API endpoints"""
    base_url = "http://127.0.0.1:5000"

    # Test different combinations
    test_cases = [
        {"mode": "paper", "market": "stocks"},
        {"mode": "paper", "market": "crypto"},
        {"mode": "live", "market": "stocks"},
        {"mode": "live", "market": "crypto"},
    ]

    print("=== Testing Portfolio API Endpoints ===")

    for test_case in test_cases:
        mode = test_case["mode"]
        market = test_case["market"]

        url = f"{base_url}/api/portfolio?mode={mode}&market={market}"

        print(f"\n🔍 Testing: {url}")

        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")

                # Check portfolio data specifically
                if "portfolio" in data:
                    portfolio = data["portfolio"]
                    print(f"Portfolio keys: {list(portfolio.keys())}")
                    print(f"Total Value: {portfolio.get('total_value', 'N/A')}")
                    print(f"Cash Balance: {portfolio.get('cash_balance', 'N/A')}")
                    print(f"Holdings count: {len(portfolio.get('holdings', []))}")

                    # Show first few holdings
                    holdings = portfolio.get("holdings", [])
                    if holdings:
                        print(f"Sample holdings: {holdings[:2]}")
                    else:
                        print("No holdings found")
                else:
                    print("No 'portfolio' key in response")
                    print(f"Full response: {json.dumps(data, indent=2)[:500]}...")
            else:
                print(f"Error: {response.text}")

        except requests.exceptions.ConnectionError:
            print("❌ Connection failed - is the Flask app running?")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_portfolio_api()
