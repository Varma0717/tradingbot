import requests
import json

# Login first
login_url = "http://127.0.0.1:5000/auth/login"
login_data = {"email": "trader@trademantra.com", "password": "password123"}

# Create a session to maintain cookies
session = requests.Session()

# Get login page first to get CSRF token
print("Getting login page...")
login_page = session.get(login_url)
print(f"Login page status: {login_page.status_code}")

# Find CSRF token in the page
from bs4 import BeautifulSoup

soup = BeautifulSoup(login_page.content, "html.parser")
csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
print(f"CSRF token: {csrf_token}")

# Login with CSRF token
login_data["csrf_token"] = csrf_token
print("\nLogging in...")
login_response = session.post(login_url, data=login_data)
print(f"Login response status: {login_response.status_code}")

if login_response.status_code == 200 and "dashboard" in login_response.url:
    print("Login successful")
elif login_response.status_code == 302:
    print(f"Login redirected to: {login_response.headers.get('Location', 'Unknown')}")
else:
    print("Login failed")
    print(login_response.text[:500])

# Now test the sessions API
sessions_url = "http://127.0.0.1:5000/user/automation/sessions"
print(f"\nTesting sessions API...")
sessions_response = session.get(sessions_url)
print(f"Sessions API status: {sessions_response.status_code}")

if sessions_response.status_code == 200:
    try:
        sessions_data = sessions_response.json()
        print("Sessions API response:")
        print(json.dumps(sessions_data, indent=2))
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("Raw response:")
        print(sessions_response.text[:1000])
else:
    print("Sessions API failed")
    print(sessions_response.text[:500])
