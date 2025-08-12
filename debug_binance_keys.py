#!/usr/bin/env python3
"""
Debug script to check Binance API key loading and validation
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection
from sqlalchemy import func
import re


def check_api_key_format(api_key):
    """Check if API key matches expected Binance format"""
    if not api_key:
        return False, "API key is empty"

    # Binance API keys are typically 64-character alphanumeric strings
    if len(api_key) != 64:
        return False, f"API key length is {len(api_key)}, expected 64"

    # Should contain only alphanumeric characters
    if not re.match(r"^[A-Za-z0-9]+$", api_key):
        return False, "API key contains invalid characters (only alphanumeric allowed)"

    return True, "API key format appears valid"


def check_api_secret_format(api_secret):
    """Check if API secret matches expected Binance format"""
    if not api_secret:
        return False, "API secret is empty"

    # Binance API secrets are typically 64-character alphanumeric strings
    if len(api_secret) != 64:
        return False, f"API secret length is {len(api_secret)}, expected 64"

    # Should contain only alphanumeric characters
    if not re.match(r"^[A-Za-z0-9]+$", api_secret):
        return (
            False,
            "API secret contains invalid characters (only alphanumeric allowed)",
        )

    return True, "API secret format appears valid"


def main():
    app = create_app()

    with app.app_context():
        print("=== Binance API Key Debug ===")

        # Check all users with exchange connections
        all_connections = ExchangeConnection.query.all()
        print(f"\nTotal exchange connections: {len(all_connections)}")

        for conn in all_connections:
            print(f"\nUser ID: {conn.user_id}")
            print(f"Exchange: {conn.exchange_name}")
            print(f"Connection ID: {conn.id}")
            print(f"Created: {conn.created_at}")
            print(f"Updated: {conn.updated_at}")

            # Check API key
            if conn.api_key:
                key_valid, key_msg = check_api_key_format(conn.api_key)
                print(
                    f"API Key: Present (length={len(conn.api_key)}, starts with '{conn.api_key[:6]}...')"
                )
                print(f"API Key Status: {key_msg}")

                # Check for common issues
                if conn.api_key.strip() != conn.api_key:
                    print("WARNING: API key has leading/trailing whitespace!")

                if any(char in conn.api_key for char in [" ", "\n", "\r", "\t"]):
                    print("WARNING: API key contains whitespace characters!")

            else:
                print("API Key: Missing")

            # Check API secret
            secret = conn.api_secret or conn.access_token
            if secret:
                secret_valid, secret_msg = check_api_secret_format(secret)
                print(
                    f"API Secret: Present (length={len(secret)}, starts with '{secret[:6]}...')"
                )
                print(f"API Secret Status: {secret_msg}")

                # Check for common issues
                if secret.strip() != secret:
                    print("WARNING: API secret has leading/trailing whitespace!")

                if any(char in secret for char in [" ", "\n", "\r", "\t"]):
                    print("WARNING: API secret contains whitespace characters!")

            else:
                print("API Secret: Missing")

            print("-" * 50)

        # Test specific Binance connections
        print("\n=== Binance-specific Connections ===")
        binance_connections = ExchangeConnection.query.filter(
            func.lower(ExchangeConnection.exchange_name).in_(
                ["binance", "binance_testnet"]
            )
        ).all()

        if not binance_connections:
            print("No Binance connections found!")
        else:
            for conn in binance_connections:
                print(f"\nBinance Connection Found:")
                print(f"User ID: {conn.user_id}")
                print(f"Exchange: {conn.exchange_name}")

                if conn.api_key and (conn.api_secret or conn.access_token):
                    print("✓ Has both API key and secret")

                    # Test key format
                    key_valid, key_msg = check_api_key_format(conn.api_key)
                    secret = conn.api_secret or conn.access_token
                    secret_valid, secret_msg = check_api_secret_format(secret)

                    if key_valid and secret_valid:
                        print("✓ Both key and secret appear to have valid format")
                    else:
                        print(f"✗ Format issues: Key={key_msg}, Secret={secret_msg}")
                else:
                    print("✗ Missing API key or secret")


if __name__ == "__main__":
    main()
