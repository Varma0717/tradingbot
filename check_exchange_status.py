#!/usr/bin/env python3
"""
Check exchange connections and their status
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection


def check_exchange_connections():
    """Check all exchange connections and their status"""
    app = create_app()

    with app.app_context():
        print("=== Exchange Connections Status ===")

        connections = ExchangeConnection.query.all()

        if not connections:
            print("No exchange connections found!")
            return

        for conn in connections:
            print(f"\nConnection ID: {conn.id}")
            print(f"User ID: {conn.user_id}")
            print(f"Exchange: {conn.exchange_name}")
            print(f"Status: {conn.status}")
            print(f"Created: {conn.created_at}")
            print(f"Updated: {conn.updated_at}")
            print("-" * 40)

        # Check connected exchanges specifically
        print("\n=== Connected Exchanges ===")
        connected = ExchangeConnection.query.filter_by(status="connected").all()

        if not connected:
            print("❌ No exchanges have status='connected'!")
            print("\nThis is why portfolio shows mock data instead of real data.")
            print("\nTo fix this, we need to update the exchange connection status:")

            # Show how to fix
            for conn in connections:
                if conn.exchange_name in ["binance", "binance_testnet"]:
                    print(f"\nTo enable real data for {conn.exchange_name}:")
                    print(
                        f"UPDATE exchange_connections SET status='connected' WHERE id={conn.id};"
                    )
        else:
            print("✅ Connected exchanges found:")
            for conn in connected:
                print(f"  - {conn.exchange_name} (User {conn.user_id})")


if __name__ == "__main__":
    check_exchange_connections()
