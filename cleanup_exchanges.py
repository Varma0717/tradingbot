#!/usr/bin/env python3
"""
Clean up duplicate exchange connections
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection, db


def cleanup_duplicate_exchanges():
    """Remove duplicate exchange connections"""
    app = create_app()

    with app.app_context():
        print("=== Cleaning Up Duplicate Exchanges ===")

        # Find Binance connections for user 2
        binance_connections = ExchangeConnection.query.filter_by(
            user_id=2, exchange_name="binance"
        ).all()

        print(f"Found {len(binance_connections)} Binance connections for user 2:")

        for conn in binance_connections:
            print(f"  ID: {conn.id}, Created: {conn.created_at}")

        if len(binance_connections) > 1:
            # Keep the most recent one, delete the others
            binance_connections.sort(
                key=lambda x: x.created_at or x.updated_at, reverse=True
            )
            to_keep = binance_connections[0]
            to_delete = binance_connections[1:]

            print(f"\nKeeping connection ID {to_keep.id} (most recent)")
            print(f"Deleting {len(to_delete)} duplicate connections...")

            for conn in to_delete:
                print(f"  Deleting ID {conn.id}")
                db.session.delete(conn)

            db.session.commit()
            print("✅ Cleanup completed!")
        else:
            print("No duplicates found.")


if __name__ == "__main__":
    cleanup_duplicate_exchanges()
