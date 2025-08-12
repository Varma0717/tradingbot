#!/usr/bin/env python3
"""
Simple check of exchange connection status
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import ExchangeConnection, db
from sqlalchemy import text


def main():
    app = create_app()

    with app.app_context():
        # Check exchange connections directly
        result = db.session.execute(
            text(
                """
            SELECT id, user_id, exchange_name, status, created_at, updated_at
            FROM exchange_connections
            ORDER BY user_id, exchange_name;
        """
            )
        )

        print("=== Exchange Connections ===")
        connections = result.fetchall()

        for conn in connections:
            print(
                f"ID: {conn[0]}, User: {conn[1]}, Exchange: {conn[2]}, Status: {conn[3]}"
            )

        # Count by status
        result = db.session.execute(
            text(
                """
            SELECT status, COUNT(*) 
            FROM exchange_connections 
            GROUP BY status;
        """
            )
        )

        print("\n=== Status Summary ===")
        for status, count in result.fetchall():
            print(f"{status}: {count}")


if __name__ == "__main__":
    main()
