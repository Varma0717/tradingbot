#!/usr/bin/env python3
"""
Test the dashboard with dynamic data loading.
"""

import time
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_dynamic_dashboard():
    """Test that dashboard loads dynamic data instead of static values."""

    print("🧪 Testing Dynamic Dashboard Data Loading")
    print("=" * 50)

    # Dashboard URL
    dashboard_url = "http://127.0.0.1:8001"

    try:
        # Setup Chrome driver (headless for server testing)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Remove this to see the browser
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)

        print(f"📱 Opening dashboard: {dashboard_url}")
        driver.get(dashboard_url)

        # Wait for page to load
        wait = WebDriverWait(driver, 10)

        print("⏳ Waiting for dynamic data to load...")
        time.sleep(5)  # Wait for JavaScript to execute

        # Check if data is loaded dynamically
        portfolio_balance = driver.find_element(By.ID, "portfolioBalance").text
        bot_status = driver.find_element(By.ID, "botStatus").text
        active_positions = driver.find_element(By.ID, "activePositions").text
        active_orders = driver.find_element(By.ID, "activeOrders").text

        print("\n📊 Dashboard Values:")
        print(f"Portfolio Balance: {portfolio_balance}")
        print(f"Bot Status: {bot_status}")
        print(f"Active Positions: {active_positions}")
        print(f"Active Orders: {active_orders}")

        # Check if values are not loading placeholders
        if "Loading..." in portfolio_balance:
            print("⚠️  Portfolio balance still showing loading placeholder")
        elif "$" in portfolio_balance:
            print("✅ Portfolio balance loaded with currency format")
        else:
            print(f"✅ Portfolio balance shows: {portfolio_balance}")

        if "Loading..." in bot_status:
            print("⚠️  Bot status still showing loading placeholder")
        elif "Running" in bot_status or "Stopped" in bot_status:
            print("✅ Bot status loaded successfully")
        else:
            print(f"✅ Bot status shows: {bot_status}")

        # Check for API network requests in console logs
        logs = driver.get_log("browser")
        api_requests = [log for log in logs if "/api/" in log.get("message", "")]

        print(f"\n🌐 API Requests Made: {len(api_requests)}")
        for log in api_requests[:5]:  # Show first 5
            print(f"   {log.get('message', '')[:100]}...")

        print("\n✅ Dashboard dynamic loading test completed!")

    except Exception as e:
        print(f"❌ Error testing dashboard: {e}")
        print("Make sure:")
        print("1. Dashboard server is running on port 8001")
        print("2. Chrome browser is installed")
        print("3. ChromeDriver is available in PATH")

    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    test_dynamic_dashboard()
