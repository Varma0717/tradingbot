"""
Test the Pionex-style Grid Trading API endpoints
"""

import requests
import json

# Test the Grid Trading API endpoints
base_url = "http://127.0.0.1:5000/api/grid"


def test_grid_api():
    print("🔥 Testing Pionex-style Grid Trading API...")

    # Test 1: Get Grid Status
    print("\n1. Testing Grid Status:")
    try:
        response = requests.get(f"{base_url}/status")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Get Configuration
    print("\n2. Testing Grid Configuration:")
    try:
        response = requests.get(f"{base_url}/config")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Start Grid Trading
    print("\n3. Testing Start Grid Trading:")
    try:
        config = {
            "initial_capital": 5000,
            "symbols": ["AAPL", "TSLA", "MSFT"],
            "target_daily_return": 0.03,
        }
        response = requests.post(f"{base_url}/start", json=config)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")

    # Wait a moment for the grid to initialize
    import time

    print("\n   Waiting 5 seconds for grid initialization...")
    time.sleep(5)

    # Test 4: Get Performance
    print("\n4. Testing Grid Performance:")
    try:
        response = requests.get(f"{base_url}/performance")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 5: Get Updated Status
    print("\n5. Testing Updated Grid Status:")
    try:
        response = requests.get(f"{base_url}/status")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 6: Stop Grid Trading
    print("\n6. Testing Stop Grid Trading:")
    try:
        response = requests.post(f"{base_url}/stop")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n✅ Grid Trading API Test Complete!")


if __name__ == "__main__":
    test_grid_api()
