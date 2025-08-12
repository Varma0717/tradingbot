#!/usr/bin/env python3
"""
Test the Binance adapter with the updated API keys
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.exchange_adapter.binance_adapter import BinanceAdapter


def test_binance_adapter():
    """Test Binance adapter initialization and connection"""
    app = create_app()

    with app.app_context():
        print("=== Testing Binance Adapter ===")

        # Test with user 2 (has placeholder keys)
        print("\nTesting with user 2 (placeholder keys)...")
        adapter = BinanceAdapter(user_id=2)

        print(f"Adapter debug summary:")
        summary = adapter.debug_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")

        print(f"\nIs connected: {adapter.is_connected}")
        print(f"Is placeholder key detected: {adapter._is_placeholder_key()}")

        # Test getting portfolio data
        print("\nTesting portfolio data fetch...")
        try:
            portfolio = adapter.get_portfolio()
            print(f"Portfolio type: {type(portfolio)}")
            print(
                f"Portfolio columns: {list(portfolio.columns) if hasattr(portfolio, 'columns') else 'N/A'}"
            )
            print(
                f"Portfolio shape: {portfolio.shape if hasattr(portfolio, 'shape') else 'N/A'}"
            )
            if not portfolio.empty:
                print(f"Sample portfolio data:\n{portfolio.head()}")
            else:
                print("Portfolio data is empty (expected for demo mode)")
        except Exception as e:
            print(f"Error getting portfolio: {e}")

        # Test getting market data
        print("\nTesting market data fetch...")
        try:
            market_data = adapter.get_market_data("BTCUSDT")
            print(f"Market data type: {type(market_data)}")
            print(
                f"Market data columns: {list(market_data.columns) if hasattr(market_data, 'columns') else 'N/A'}"
            )
            print(
                f"Market data shape: {market_data.shape if hasattr(market_data, 'shape') else 'N/A'}"
            )
            if not market_data.empty:
                print(f"Sample market data:\n{market_data.head()}")
        except Exception as e:
            print(f"Error getting market data: {e}")


if __name__ == "__main__":
    test_binance_adapter()
