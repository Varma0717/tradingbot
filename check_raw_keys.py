#!/usr/bin/env python3
"""
Check the actual API key values stored in database
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection


def main():
    app = create_app()

    with app.app_context():
        print("=== Raw API Key Values ===")

        # Get the binance connection for user 2
        conn = ExchangeConnection.query.filter_by(
            user_id=2, exchange_name="binance"
        ).first()

        if conn:
            print(f"Connection ID: {conn.id}")
            print(f"User ID: {conn.user_id}")
            print(f"Exchange: {conn.exchange_name}")
            print(f"API Key raw value: '{conn.api_key}'")
            print(f"API Key length: {len(conn.api_key)}")
            print(f"API Secret raw value: '{conn.api_secret}'")
            print(f"API Secret length: {len(conn.api_secret)}")
            print(f"Access Token raw value: '{conn.access_token}'")

            # Check if these look like actual API keys or placeholders
            if conn.api_key.startswith("WrIqz8") and len(conn.api_key) == 17:
                print("\n⚠️  This looks like a shortened or test API key.")
                print(
                    "Binance API keys should be 64 characters long and contain only alphanumeric characters."
                )
                print("\nTo fix this:")
                print("1. Go to your Binance account API management")
                print(
                    "2. Create a new API key (if using testnet, use testnet.binance.vision)"
                )
                print("3. Copy the FULL 64-character API key")
                print("4. Copy the FULL 64-character Secret key")
                print("5. Update the exchange connection in your app")
        else:
            print("No Binance connection found for user 2")


if __name__ == "__main__":
    main()
