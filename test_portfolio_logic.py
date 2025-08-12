#!/usr/bin/env python3
"""
Test portfolio data building logic
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection
from app.exchange_adapter.binance_adapter import BinanceAdapter


def test_portfolio_data_logic():
    """Test the portfolio data building logic"""
    app = create_app()

    with app.app_context():
        print("=== Testing Portfolio Data Logic ===")

        user_id = 2

        # Step 1: Get connected exchanges (same as portfolio code)
        connected_exchanges = ExchangeConnection.query.filter_by(
            user_id=user_id, status="connected"
        ).all()

        print(f"Connected exchanges for user {user_id}: {len(connected_exchanges)}")

        total_value = 0.0
        crypto_value = 0.0
        exchange_details = []

        for exchange in connected_exchanges:
            print(f"\nProcessing exchange: {exchange.exchange_name}")

            if exchange.exchange_name in ["binance", "binance_testnet"]:
                print("  → This is a Binance exchange, creating adapter...")

                try:
                    # Create adapter (same as portfolio code)
                    adapter = BinanceAdapter(user_id=user_id)
                    print(f"  → Adapter created, is_connected: {adapter.is_connected}")

                    if adapter.is_connected:
                        print("  → Adapter is connected, getting balances...")

                        # Get balances (same as portfolio code)
                        balances = adapter.get_balances()
                        print(f"  → Got {len(balances)} balances")

                        # Show all balances for debugging
                        for balance in balances:
                            if balance["total"] > 0:
                                print(f"    - {balance['asset']}: {balance['total']}")

                        # Calculate value (same as portfolio code)
                        usdt_balances = [b for b in balances if b["asset"] == "USDT"]
                        usdt_value = sum([b["total"] for b in usdt_balances])
                        print(f"  → USDT value: {usdt_value}")

                        total_value += usdt_value
                        crypto_value += usdt_value

                        exchange_details.append(
                            {
                                "type": "crypto",
                                "name": exchange.get_display_name(),
                                "value": usdt_value,
                                "balances": balances,
                            }
                        )

                    else:
                        print("  → Adapter not connected!")

                except Exception as e:
                    print(f"  → Error with adapter: {e}")
                    exchange_details.append(
                        {
                            "type": "crypto",
                            "name": exchange.get_display_name(),
                            "error": str(e),
                        }
                    )
            else:
                print(f"  → Skipping non-Binance exchange: {exchange.exchange_name}")

        print(f"\n=== Final Results ===")
        print(f"Total value: {total_value}")
        print(f"Crypto value: {crypto_value}")
        print(f"Exchange details: {len(exchange_details)}")

        if exchange_details:
            for detail in exchange_details:
                print(f"  - {detail}")
        else:
            print("  - No exchange details (will use mock data)")


if __name__ == "__main__":
    test_portfolio_data_logic()
