#!/usr/bin/env python3
"""
Create exchange_connections table using Flask app context
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import ExchangeConnection


def create_exchange_table():
    """Create the exchange_connections table using Flask's app context"""
    app = create_app()

    with app.app_context():
        try:
            # Check if table exists using inspector
            from sqlalchemy import inspect

            inspector = inspect(db.engine)

            if "exchange_connections" not in inspector.get_table_names():
                print("Creating exchange_connections table...")

                # Create the table
                ExchangeConnection.__table__.create(db.engine)

                print("✅ exchange_connections table created successfully!")
            else:
                print("✅ exchange_connections table already exists!")

        except Exception as e:
            print(f"❌ Error creating table: {e}")


if __name__ == "__main__":
    create_exchange_table()
