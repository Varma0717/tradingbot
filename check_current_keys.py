#!/usr/bin/env python3
"""
Check current API key values after cleanup
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection


def check_current_keys():
    """Check what API keys are currently stored"""
    app = create_app()

    with app.app_context():
        print("=== Current API Keys ===")

        connections = ExchangeConnection.query.filter_by(user_id=2).all()

        for conn in connections:
            print(f"\nConnection ID: {conn.id}")
            print(f"Exchange: {conn.exchange_name}")
            print(
                f"API Key: {conn.api_key[:10] if conn.api_key else 'None'}... (length: {len(conn.api_key) if conn.api_key else 0})"
            )
            print(
                f"Secret: {conn.api_secret[:6] if conn.api_secret else 'None'}... (length: {len(conn.api_secret) if conn.api_secret else 0})"
            )


if __name__ == "__main__":
    check_current_keys()
