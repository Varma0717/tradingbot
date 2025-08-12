#!/usr/bin/env python3
"""
Create Missing Database Tables
This script creates the missing trading_bot_status table and any other required tables.
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import TradingBotStatus


def create_missing_tables():
    """Create missing database tables"""
    print("🔧 Creating missing database tables...")

    try:
        # Create Flask app
        app = create_app()

        with app.app_context():
            # Create all tables
            db.create_all()

            print("✅ All database tables created successfully!")

            # Verify the trading_bot_status table exists
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            print(f"📊 Available tables: {len(tables)}")
            for table in sorted(tables):
                print(f"   • {table}")

            if "trading_bot_status" in tables:
                print("✅ trading_bot_status table verified!")
            else:
                print("❌ trading_bot_status table still missing")

            return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


if __name__ == "__main__":
    success = create_missing_tables()
    if success:
        print("\n🎉 Database table creation completed!")
    else:
        print("\n❌ Database table creation failed!")
        sys.exit(1)
