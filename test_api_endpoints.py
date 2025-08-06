#!/usr/bin/env python3
"""
Test script to check API endpoint availability.
"""

import requests
import json
from datetime import datetime


def test_api_endpoints():
    """Test all critical API endpoints."""

    base_url = "http://127.0.0.1:8001/api"

    # List of endpoints that the templates expect
    endpoints_to_test = [
        # Core endpoints
        ("GET", "/status"),
        ("GET", "/balance"),
        ("GET", "/orders"),
        # Strategy endpoints
        ("GET", "/strategies"),
        ("GET", "/strategies/summary"),
        ("GET", "/strategies/backtests"),
        ("GET", "/strategies/performance"),
        # Symbol and settings
        ("GET", "/symbols"),
        ("GET", "/settings"),
        # Control endpoints
        ("POST", "/control/start"),
        ("POST", "/control/stop"),
        ("POST", "/control/restart"),
        ("POST", "/control/pause"),
        # Portfolio endpoints
        ("GET", "/portfolio/summary"),
        ("GET", "/portfolio/positions"),
        ("GET", "/portfolio/performance"),
        ("GET", "/portfolio/balance-history"),
        # Trade endpoints
        ("GET", "/trades/summary"),
        ("GET", "/trades/history"),
        ("GET", "/trades/orders/open"),
        ("GET", "/trades/performance"),
        # API docs
        ("GET", "/docs"),
    ]

    print("🧪 Testing API Endpoints")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"Testing {len(endpoints_to_test)} endpoints...")
    print()

    success_count = 0
    total_count = len(endpoints_to_test)

    for method, endpoint in endpoints_to_test:
        url = base_url + endpoint

        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, timeout=5)

            if response.status_code == 200:
                print(f"✅ {method:4} {endpoint}")
                success_count += 1
            elif response.status_code == 404:
                print(f"❌ {method:4} {endpoint} - NOT FOUND")
            else:
                print(f"⚠️  {method:4} {endpoint} - Status: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"🔌 {method:4} {endpoint} - Server not running")
        except requests.exceptions.Timeout:
            print(f"⏱️  {method:4} {endpoint} - Timeout")
        except Exception as e:
            print(f"💥 {method:4} {endpoint} - Error: {e}")

    print()
    print("=" * 50)
    print(f"Results: {success_count}/{total_count} endpoints working")
    print(f"Success rate: {(success_count/total_count)*100:.1f}%")

    if success_count == total_count:
        print("🎉 All endpoints are working!")
    elif success_count > total_count * 0.8:
        print("✨ Most endpoints are working - dashboard should function well")
    else:
        print("⚠️  Many endpoints missing - dashboard may have issues")


if __name__ == "__main__":
    test_api_endpoints()
