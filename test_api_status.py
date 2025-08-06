#!/usr/bin/env python3
"""
Test API status endpoint accessibility
"""
import requests
import json


def test_api_status():
    """Test if the /api/status endpoint is accessible."""
    print("=== Testing /api/status Endpoint ===")

    base_url = "http://localhost:8000"

    try:
        # Test root endpoint first
        print("1. Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Root endpoint: {response.status_code}")

        # Test API status endpoint
        print("2. Testing /api/status endpoint...")
        response = requests.get(f"{base_url}/api/status", timeout=5)
        print(f"   API status: {response.status_code}")

        if response.status_code == 200:
            print("✅ /api/status endpoint is working!")
            try:
                data = response.json()
                print(f"   Response data: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response text: {response.text}")
        elif response.status_code == 404:
            print("❌ /api/status endpoint returns 404")
            print("   This means the route is not registered or accessible")
        else:
            print(f"❌ /api/status endpoint returns {response.status_code}")
            print(f"   Response: {response.text}")

        # Test if any API endpoints work
        print("3. Testing /api/settings endpoint...")
        response = requests.get(f"{base_url}/api/settings", timeout=5)
        print(f"   API settings: {response.status_code}")

        if response.status_code == 200:
            print("✅ Other API endpoints are working")
        else:
            print("❌ API endpoints might have broader issues")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to localhost:8000")
        print("   Dashboard server might not be running")
    except Exception as e:
        print(f"❌ Error testing API: {e}")


def check_server_running():
    """Check if the dashboard server is running."""
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    if check_server_running():
        print("✅ Dashboard server is running")
        test_api_status()
    else:
        print("❌ Dashboard server is not running")
        print("   Please start with: python main.py --mode dashboard")
