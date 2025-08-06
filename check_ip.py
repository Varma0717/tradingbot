"""Check current IP address for Binance API setup."""

import requests
import json


def check_ip():
    """Check your current public IP address."""
    try:
        print("🌐 Checking your current IP address...")

        # Try multiple IP checking services
        services = [
            "https://api.ipify.org?format=json",
            "https://httpbin.org/ip",
            "https://api.myip.com",
        ]

        for service in services:
            try:
                response = requests.get(service, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    # Different services return IP in different formats
                    ip = None
                    if "ip" in data:
                        ip = data["ip"]
                    elif "origin" in data:
                        ip = data["origin"]

                    if ip:
                        print(f"✅ Your public IP address: {ip}")
                        print(f"\n📝 To fix the API issue:")
                        print(f"   1. Go to Binance.com → Account → API Management")
                        print(f"   2. Edit your API key")
                        print(
                            f"   3. Add this IP to 'Restrict access to trusted IPs': {ip}"
                        )
                        print(f"   4. Or remove IP restrictions entirely (less secure)")
                        return ip

            except Exception as e:
                print(f"   Service {service} failed: {e}")
                continue

        print("❌ Could not determine your IP address")
        return None

    except Exception as e:
        print(f"❌ Error checking IP: {e}")
        return None


if __name__ == "__main__":
    check_ip()
