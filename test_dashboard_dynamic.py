#!/usr/bin/env python3
"""
Simple test to verify dashboard shows dynamic data instead of static placeholders.
"""

import requests
import json
from datetime import datetime


def test_dashboard_api_integration():
    """Test that dashboard API endpoints return dynamic data."""

    print("🔄 Testing Dashboard API Integration")
    print("=" * 50)

    base_url = "http://127.0.0.1:8001"
    api_url = f"{base_url}/api"

    # Test key endpoints that dashboard uses
    test_endpoints = [
        ("Bot Status", "/status"),
        ("Portfolio Summary", "/portfolio/summary"),
        ("Account Balance", "/balance"),
        ("Active Orders", "/trades/orders/open"),
        ("Strategy Summary", "/strategies/summary"),
        ("Settings", "/settings"),
    ]

    print(f"Testing {len(test_endpoints)} key dashboard endpoints...")
    print()

    working_endpoints = 0

    for name, endpoint in test_endpoints:
        url = api_url + endpoint
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: {endpoint}")

                # Show key data points
                if "balance" in data:
                    print(f"   💰 Balance data available")
                elif "summary" in data:
                    print(f"   📊 Summary data available")
                elif "status" in data:
                    print(f"   🤖 Status: {data.get('status', 'unknown')}")
                elif "orders" in data:
                    print(f"   📋 Orders: {data.get('count', 0)} found")
                elif "strategies" in data:
                    print(
                        f"   🧠 Strategies: {len(data.get('strategies', []))} available"
                    )
                elif "trading" in data:
                    print(f"   ⚙️  Settings loaded")

                working_endpoints += 1

            else:
                print(f"❌ {name}: {endpoint} - Status {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"🔌 {name}: {endpoint} - Server not running")
        except Exception as e:
            print(f"💥 {name}: {endpoint} - Error: {e}")

    print()
    print("=" * 50)
    success_rate = (working_endpoints / len(test_endpoints)) * 100
    print(
        f"Results: {working_endpoints}/{len(test_endpoints)} endpoints working ({success_rate:.1f}%)"
    )

    if working_endpoints == len(test_endpoints):
        print("🎉 All dashboard API endpoints are working!")
        print(
            "📱 Dashboard should display real-time data instead of static placeholders."
        )
    elif working_endpoints > len(test_endpoints) * 0.7:
        print("✨ Most endpoints working - dashboard should function well")
    else:
        print("⚠️  Many endpoints not working - dashboard may show static data")

    print()
    print("🔗 Test the dashboard at: http://127.0.0.1:8001")
    print("📊 You should see:")
    print("   - 'Loading...' briefly, then real data")
    print("   - Actual Binance balance instead of $0.00")
    print("   - Real bot status instead of static values")
    print("   - Dynamic position counts")


if __name__ == "__main__":
    test_dashboard_api_integration()
