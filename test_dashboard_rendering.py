#!/usr/bin/env python3
"""
Test what template is actually being rendered for the dashboard
"""

import requests
from bs4 import BeautifulSoup


def test_dashboard_rendering():
    """Test what the user actually sees on the dashboard"""

    # Login and get dashboard
    session = requests.Session()

    # Get login page for CSRF token
    login_page = session.get("http://localhost:5000/auth/login")
    soup = BeautifulSoup(login_page.content, "html.parser")
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

    # Login
    login_data = {
        "email": "test@trading.com",
        "password": "password123",
        "csrf_token": csrf_token,
        "remember_me": False,
        "submit": "Sign In",
    }

    response = session.post("http://localhost:5000/auth/login", data=login_data)
    print(f"Login response: {response.status_code}")

    if response.status_code == 302:  # Successful login redirects
        # Get dashboard
        dashboard = session.get("http://localhost:5000/user/dashboard")
        print(f"Dashboard response: {dashboard.status_code}")

        if dashboard.status_code == 200:
            soup = BeautifulSoup(dashboard.content, "html.parser")

            # Check for enhanced features
            subscription_elements = soup.find_all(
                text=lambda text: text and "subscription" in text.lower()
            )
            ai_elements = soup.find_all(
                text=lambda text: text and "ai enabled" in text.lower()
            )
            profit_elements = soup.find_all(
                text=lambda text: text and "total profit" in text.lower()
            )
            follower_elements = soup.find_all(
                text=lambda text: text and "followers" in text.lower()
            )

            print(f"\n=== DASHBOARD CONTENT ANALYSIS ===")
            print(f"Subscription mentions: {len(subscription_elements)}")
            print(f"AI mentions: {len(ai_elements)}")
            print(f"Profit mentions: {len(profit_elements)}")
            print(f"Follower mentions: {len(follower_elements)}")

            # Check for specific enhanced elements
            title = soup.find("title")
            if title:
                print(f"Page title: {title.text}")

            # Look for subscription tier display
            subscription_badges = soup.find_all(
                "span", class_=lambda x: x and "bg-green" in x
            )
            print(f"Subscription badges found: {len(subscription_badges)}")

            # Check if we can find the enhanced user info section
            if soup.find(text=lambda text: text and "Welcome back" in text):
                print("✅ Enhanced dashboard template detected!")
                print("✅ 'Welcome back' message found")
            else:
                print("❌ Basic dashboard template detected")

            # Save a sample of the content for debugging
            with open("dashboard_debug.html", "w", encoding="utf-8") as f:
                f.write(dashboard.content.decode("utf-8"))
            print("📁 Dashboard HTML saved to 'dashboard_debug.html'")

        else:
            print(f"❌ Could not access dashboard: {dashboard.status_code}")
    else:
        print(f"❌ Login failed: {response.status_code}")


if __name__ == "__main__":
    test_dashboard_rendering()
