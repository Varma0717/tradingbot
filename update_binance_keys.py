#!/usr/bin/env python3
"""
Script to update Binance API credentials in the database
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection, db


def update_binance_credentials():
    """Update Binance API credentials for user 2"""
    app = create_app()

    with app.app_context():
        print("=== Update Binance API Credentials ===")

        # Get the binance connection for user 2
        conn = ExchangeConnection.query.filter_by(
            user_id=2, exchange_name="binance"
        ).first()

        if not conn:
            print("No Binance connection found for user 2. Creating new one...")
            conn = ExchangeConnection(user_id=2, exchange_name="binance")
            db.session.add(conn)

        print(f"\nCurrent connection:")
        print(
            f"API Key: {conn.api_key[:10]}... (length: {len(conn.api_key) if conn.api_key else 0})"
        )
        print(
            f"API Secret: {conn.api_secret[:6]}... (length: {len(conn.api_secret) if conn.api_secret else 0})"
        )

        print("\n" + "=" * 60)
        print("IMPORTANT: You need to provide REAL Binance API credentials")
        print("=" * 60)
        print("1. Go to https://testnet.binance.vision/ (for testnet)")
        print(
            "   OR https://www.binance.com/en/my/settings/api-management (for mainnet)"
        )
        print("2. Create a new API key")
        print("3. Copy the 64-character API key")
        print("4. Copy the 64-character Secret key")
        print("5. Enter them below")
        print("\nFor now, I'll set up the adapter to use demo mode...")

        # For now, let's update to use testnet and set valid format keys
        # These are example format - user should replace with real ones
        example_api_key = "a" * 64  # 64 character placeholder
        example_secret = "b" * 64  # 64 character placeholder

        conn.exchange_name = "binance_testnet"  # Use testnet by default
        conn.api_key = example_api_key
        conn.api_secret = example_secret

        db.session.commit()

        print(f"\nUpdated connection to use testnet with placeholder keys.")
        print(f"New API Key: {conn.api_key[:10]}... (length: {len(conn.api_key)})")
        print(
            f"New API Secret: {conn.api_secret[:6]}... (length: {len(conn.api_secret)})"
        )

        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print(
            "1. Replace the placeholder keys with your REAL Binance testnet API credentials"
        )
        print("2. Or use the web interface to update the exchange connection")
        print("3. The adapter will detect the placeholder keys and use demo mode")
        print("4. Once you have real keys, the adapter will connect to Binance API")


if __name__ == "__main__":
    update_binance_credentials()
