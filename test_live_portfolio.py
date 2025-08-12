#!/usr/bin/env python3
"""
Test portfolio API in live mode - should show real Binance data
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import create_app
from app.user.routes import _build_portfolio_data

app = create_app()

with app.app_context():
    print("=== Testing Portfolio API in LIVE Mode ===")

    # Test the live mode data that the API will return
    portfolio_data, stock_orders, crypto_orders = _build_portfolio_data(2, "live")

    print(f"Portfolio in LIVE mode:")
    print(f"  Total Value: ${portfolio_data['total_value']:.2f}")
    print(f"  Crypto Value: ${portfolio_data['crypto_value']:.2f}")
    print(f"  Stock Value: ${portfolio_data['stock_value']:.2f}")
    print(f"  Exchange Details: {len(portfolio_data['exchange_details'])}")

    for i, exchange in enumerate(portfolio_data["exchange_details"]):
        print(f"    {i+1}. {exchange['name']}: ${exchange['value']:.2f}")
        if "balances" in exchange:
            for balance in exchange["balances"]:
                if balance["total"] > 0:
                    print(f"       - {balance['asset']}: {balance['total']}")

    print(f"\nCrypto Orders: {len(crypto_orders)}")
    print(f"Stock Orders: {len(stock_orders)}")

    print("\n=== This is what will show in the web interface! ===")
