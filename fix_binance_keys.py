#!/usr/bin/env python3
"""
Fix the remaining Binance connection with real API keys
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection, db


def fix_binance_keys():
    """Update the remaining Binance connection with real API keys"""
    app = create_app()

    with app.app_context():
        print("=== Fixing Binance API Keys ===")

        # Get the remaining Binance connection
        conn = ExchangeConnection.query.filter_by(
            user_id=2, exchange_name="binance"
        ).first()

        if not conn:
            print("❌ No Binance connection found!")
            return

        print(f"Found Binance connection ID: {conn.id}")
        print(f"Current API Key: {conn.api_key[:10]}... (length: {len(conn.api_key)})")
        print(
            f"Current Secret: {conn.api_secret[:6]}... (length: {len(conn.api_secret)})"
        )

        # Real Binance mainnet API credentials (same as before)
        real_api_key = (
            "WrIqz8z9Yir49uSRpGLG2nmP4gtWgSXNnTTCMOhpOYaLOcmgtDIIXI0dtCXu7eP3"
        )
        real_secret = "AFKsFkSdSBCuJOZTCY6praP5ain1j64cSv7VXWM4OpI4OmLYMuBpspGibmkCN28S"

        # Update with real keys
        conn.api_key = real_api_key
        conn.api_secret = real_secret
        conn.exchange_name = "binance"  # Ensure it's mainnet

        db.session.commit()

        print(f"\n✅ Updated successfully!")
        print(f"New API Key: {conn.api_key[:10]}... (length: {len(conn.api_key)})")
        print(f"New Secret: {conn.api_secret[:10]}... (length: {len(conn.api_secret)})")


if __name__ == "__main__":
    fix_binance_keys()
