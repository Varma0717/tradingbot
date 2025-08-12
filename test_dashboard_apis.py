#!/usr/bin/env python3
"""
Test script to verify the unified dashboard APIs are working correctly.
"""

import requests
import json


def test_api_endpoint(url, description):
    """Test an API endpoint and print the result"""
    try:
        print(f"\n🔍 Testing {description}...")
        print(f"URL: {url}")

        # Use session cookie from a logged-in user
        cookies = {
            "session": ".eJyrVkrOyC_OBRJpSqXFpZn5RUrWKs7V9sT2Tm9PTU9My89VQhEtqCxJzQWLlmTmlSqlGulo1wIA2jkT-g.ZrsKng.4CmM7Yf7Jdj2eLOqGY-ZG_7f-Ps"
        }

        response = requests.get(url, cookies=cookies, timeout=10)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success! Data keys: {list(data.keys())}")

                # Print specific data for analysis
                if "success" in data and data["success"]:
                    print(f"✅ API Success: True")
                    if "total_value" in data:
                        print(f"💰 Portfolio Value: ${data.get('total_value', 0)}")
                    if "stock_bot" in data:
                        print(
                            f"🤖 Stock Bot Running: {data['stock_bot'].get('is_running', False)}"
                        )
                    if "crypto_bot" in data:
                        print(
                            f"₿ Crypto Bot Running: {data['crypto_bot'].get('is_running', False)}"
                        )
                else:
                    print(f"⚠️ API Success: {data.get('success', 'Unknown')}")

            except json.JSONDecodeError:
                print(f"⚠️ Response is not JSON: {response.text[:200]}...")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Test all dashboard API endpoints"""
    print("🚀 Testing Unified Dashboard API Endpoints")
    print("=" * 50)

    base_url = "http://localhost:5000"

    # Test all the API endpoints used by the dashboard
    endpoints = [
        ("/user/api/portfolio-summary", "Portfolio Summary"),
        ("/user/api/bot-status", "Bot Status"),
        ("/user/api/portfolio?mode=live", "Live Portfolio"),
        ("/user/api/portfolio?mode=paper", "Paper Portfolio"),
        ("/user/api/recent-activity", "Recent Activity"),
        ("/user/preferences/api", "User Preferences"),
    ]

    for endpoint, description in endpoints:
        test_api_endpoint(f"{base_url}{endpoint}", description)

    print("\n" + "=" * 50)
    print("✅ Dashboard API testing completed!")
    print(
        "\nIf all endpoints returned 200 status codes, the dashboard should be working properly."
    )
    print("Check the browser console for any remaining JavaScript errors.")


if __name__ == "__main__":
    main()
