#!/usr/bin/env python3
"""
Migration script to add TradingBotStatus table
Run this once to add the new table to your database
"""

from app import create_app, db
from app.models import TradingBotStatus


def run_migration():
    app = create_app()

    with app.app_context():
        print("Creating TradingBotStatus table...")

        try:
            # Create the table
            db.create_all()
            print("✅ TradingBotStatus table created successfully!")

        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return False

    return True


if __name__ == "__main__":
    print("Running migration to add TradingBotStatus table...")
    success = run_migration()

    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
