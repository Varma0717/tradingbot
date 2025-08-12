#!/usr/bin/env python3
"""
Simple test of Binance adapter
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.exchange_adapter.binance_adapter import BinanceAdapter


def test_binance_simple():
    """Simple test of Binance adapter"""
    app = create_app()

    with app.app_context():
        print("=== Simple Binance Test ===")

        # Test with user 2 (has placeholder keys)
        adapter = BinanceAdapter(user_id=2)

        print(f"Is connected: {adapter.is_connected}")
        print(f"Is placeholder key: {adapter._is_placeholder_key()}")
        print(f"Exchange type: {adapter.exchange_type}")
        print(f"Testnet mode: {adapter.testnet}")

        # Test getting balances
        print("\nTesting get_balances()...")
        try:
            balances = adapter.get_balances()
            print(f"Balances: {balances}")
        except Exception as e:
            print(f"Error: {e}")

        # Test getting account info
        print("\nTesting get_account_info()...")
        try:
            account = adapter.get_account_info()
            print(f"Account info: {account}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_binance_simple()
