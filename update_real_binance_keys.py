#!/usr/bin/env python3
"""
Update Binance API credentials with real keys (mainnet)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection, db


def update_real_binance_credentials():
    """Update Binance API credentials with real mainnet keys"""
    app = create_app()

    with app.app_context():
        print("=== Update Real Binance API Credentials ===")

        # Get the binance connection for user 2
        conn = ExchangeConnection.query.filter_by(
            user_id=2, exchange_name="binance_testnet"
        ).first()

        if not conn:
            # Check if there's a regular binance connection
            conn = ExchangeConnection.query.filter_by(
                user_id=2, exchange_name="binance"
            ).first()

        if not conn:
            print("Creating new Binance connection...")
            conn = ExchangeConnection(
                user_id=2, exchange_name="binance"  # Use mainnet, not testnet
            )
            db.session.add(conn)

        print(f"\nCurrent connection:")
        print(f"Exchange: {conn.exchange_name}")
        print(f"API Key: {conn.api_key[:10] if conn.api_key else 'None'}...")
        print(f"API Secret: {conn.api_secret[:6] if conn.api_secret else 'None'}...")

        # Real Binance mainnet API credentials
        real_api_key = (
            "WrIqz8z9Yir49uSRpGLG2nmP4gtWgSXNnTTCMOhpOYaLOcmgtDIIXI0dtCXu7eP3"
        )
        real_secret = "AFKsFkSdSBCuJOZTCY6praP5ain1j64cSv7VXWM4OpI4OmLYMuBpspGibmkCN28S"

        # Validate the key format
        if len(real_api_key) == 64 and real_api_key.isalnum():
            print("✅ API Key format is valid (64 alphanumeric characters)")
        else:
            print(
                f"⚠️ API Key format warning: length={len(real_api_key)}, alphanumeric={real_api_key.isalnum()}"
            )

        if len(real_secret) == 64 and real_secret.isalnum():
            print("✅ Secret Key format is valid (64 alphanumeric characters)")
        else:
            print(
                f"⚠️ Secret Key format warning: length={len(real_secret)}, alphanumeric={real_secret.isalnum()}"
            )

        # Update the connection
        conn.exchange_name = "binance"  # Use mainnet (remove testnet)
        conn.api_key = real_api_key
        conn.api_secret = real_secret

        db.session.commit()

        print(f"\n✅ Updated connection successfully!")
        print(f"Exchange: {conn.exchange_name}")
        print(f"API Key: {conn.api_key[:10]}... (length: {len(conn.api_key)})")
        print(f"Secret Key: {conn.api_secret[:10]}... (length: {len(conn.api_secret)})")

        print("\n" + "=" * 60)
        print("IMPORTANT NOTES:")
        print("=" * 60)
        print("✅ Using MAINNET Binance API (not testnet)")
        print("⚠️ Make sure your API key has the required permissions:")
        print("   - Spot & Margin Trading (if you want to place real orders)")
        print("   - Enable Reading (required for portfolio/balance data)")
        print("   - Consider IP restrictions for security")
        print("⚠️ This will make REAL trades on your Binance account!")
        print("⚠️ Start with small amounts or paper trading mode first")


if __name__ == "__main__":
    update_real_binance_credentials()
