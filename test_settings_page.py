#!/usr/bin/env python3
"""
Test script to verify the settings page functionality.
"""

import requests
import json
from datetime import datetime


def test_settings_page():
    """Test the settings page and its API endpoints."""

    print("⚙️  Testing Settings Page Functionality")
    print("=" * 50)

    base_url = "http://127.0.0.1:8001"

    # Test settings page load
    try:
        response = requests.get(f"{base_url}/settings", timeout=5)
        if response.status_code == 200:
            print("✅ Settings page loads successfully")
        else:
            print(f"❌ Settings page failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Error loading settings page: {e}")
        return

    # Test settings API endpoints
    api_endpoints = [
        ("GET", "/api/settings", "Load current settings"),
        ("GET", "/api/status", "Bot status for indicators"),
        ("PUT", "/api/settings/trading", "Save trading settings"),
        ("GET", "/api/settings/export", "Export settings"),
        ("POST", "/api/settings/import", "Import settings"),
        ("POST", "/api/bot/start", "Bot control - start"),
        ("POST", "/api/bot/stop", "Bot control - stop"),
        ("POST", "/api/bot/restart", "Bot control - restart"),
    ]

    print("\n🔧 Testing Settings API Endpoints:")
    working_count = 0

    for method, endpoint, description in api_endpoints:
        url = f"{base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=5)
            elif method == "PUT":
                test_data = {"mode": "paper", "max_positions": 5, "risk_per_trade": 1.0}
                response = requests.put(url, json=test_data, timeout=5)

            if response.status_code in [200, 201]:
                print(f"✅ {method:4} {endpoint:25} - {description}")
                working_count += 1
            else:
                print(f"⚠️  {method:4} {endpoint:25} - Status {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"🔌 {method:4} {endpoint:25} - Server not running")
        except Exception as e:
            print(f"💥 {method:4} {endpoint:25} - Error: {e}")

    # Test specific settings functionality
    print(f"\n📊 Testing Settings Data Structure:")
    try:
        response = requests.get(f"{base_url}/api/settings", timeout=5)
        if response.status_code == 200:
            settings = response.json()

            print("✅ Settings structure:")
            if "trading" in settings:
                print(f"   📈 Trading settings: {len(settings['trading'])} fields")
            if "risk" in settings:
                print(f"   ⚠️  Risk settings: {len(settings['risk'])} fields")

            # Test if required fields exist
            required_fields = {
                "trading": ["mode", "symbol", "amount"],
                "risk": ["max_position_size", "stop_loss_percentage"],
            }

            for section, fields in required_fields.items():
                if section in settings:
                    missing = [f for f in fields if f not in settings[section]]
                    if missing:
                        print(f"   ⚠️  Missing {section} fields: {missing}")
                    else:
                        print(f"   ✅ All required {section} fields present")
        else:
            print(f"❌ Failed to load settings: {response.status_code}")

    except Exception as e:
        print(f"❌ Error testing settings data: {e}")

    print("\n" + "=" * 50)
    success_rate = (working_count / len(api_endpoints)) * 100
    print(
        f"Results: {working_count}/{len(api_endpoints)} endpoints working ({success_rate:.1f}%)"
    )

    if working_count >= len(api_endpoints) * 0.8:
        print("🎉 Settings page should work well!")
        print("✨ Features available:")
        print("   - Live status indicators")
        print("   - Form validation")
        print("   - Toast notifications")
        print("   - Settings import/export")
        print("   - Bot control buttons")
    else:
        print("⚠️  Some settings features may not work correctly")

    print(f"\n🌐 Test the settings page at: {base_url}/settings")


if __name__ == "__main__":
    test_settings_page()
