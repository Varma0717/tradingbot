#!/usr/bin/env python3
"""
Comprehensive Database Schema Update Script for Trade Mantra
Updates User model and creates missing tables
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app, db
from app.models import User, TradingBotStatus
from sqlalchemy import text


def create_trading_bot_status_table():
    """Create the trading_bot_status table if it doesn't exist"""
    app = create_app("default")

    with app.app_context():
        try:
            print("🔄 Creating trading_bot_status table...")

            # Check if table already exists
            with db.engine.connect() as connection:
                result = connection.execute(
                    text("SHOW TABLES LIKE 'trading_bot_status'")
                )
                table_exists = result.fetchone() is not None

            if not table_exists:
                # Create the table using raw SQL to match the model exactly
                create_table_sql = """
                CREATE TABLE trading_bot_status (
                    id INTEGER AUTO_INCREMENT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    is_running BOOLEAN DEFAULT FALSE NOT NULL,
                    bot_type VARCHAR(20) DEFAULT 'stock' NOT NULL,
                    strategies JSON NULL,
                    started_at DATETIME NULL,
                    stopped_at DATETIME NULL,
                    total_trades INTEGER DEFAULT 0,
                    daily_pnl FLOAT DEFAULT 0.0,
                    win_rate FLOAT DEFAULT 0.0,
                    open_positions INTEGER DEFAULT 0,
                    strategies_active INTEGER DEFAULT 0,
                    last_heartbeat DATETIME NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY uq_user_bot_type (user_id, bot_type)
                )
                """

                with db.engine.connect() as connection:
                    connection.execute(text(create_table_sql))
                    connection.commit()

                print("   ✅ Created trading_bot_status table successfully")
                return True
            else:
                print("   ⚠️ trading_bot_status table already exists")
                return True

        except Exception as e:
            print(f"❌ Failed to create trading_bot_status table: {e}")
            return False


def update_user_schema():
    """Add enhanced fields to users table"""
    app = create_app("default")

    with app.app_context():
        try:
            print("🔄 Updating users table schema...")

            # List of new columns to add
            new_columns = [
                ("subscription_tier", "VARCHAR(20) DEFAULT 'starter'"),
                ("subscription_expires", "DATETIME NULL"),
                ("subscription_auto_renew", "BOOLEAN DEFAULT TRUE"),
                ("ai_enabled", "BOOLEAN DEFAULT FALSE"),
                ("risk_tolerance", "FLOAT DEFAULT 0.5"),
                ("trader_rating", "FLOAT DEFAULT 0.0"),
                ("total_followers", "INTEGER DEFAULT 0"),
                ("total_copiers", "INTEGER DEFAULT 0"),
                ("total_profit", "FLOAT DEFAULT 0.0"),
                ("win_rate", "FLOAT DEFAULT 0.0"),
                ("sharpe_ratio", "FLOAT DEFAULT 0.0"),
            ]

            # Check which columns already exist
            with db.engine.connect() as connection:
                result = connection.execute(text("DESCRIBE users"))
                existing_columns = [row[0] for row in result]

            # Add missing columns
            added_count = 0
            for column_name, column_def in new_columns:
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"
                        with db.engine.connect() as connection:
                            connection.execute(text(sql))
                            connection.commit()
                        print(f"   ✅ Added column: {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"   ❌ Failed to add {column_name}: {e}")
                else:
                    print(f"   ⚠️ Column {column_name} already exists")

            if added_count > 0:
                print(
                    f"\n🎉 Users table update completed! Added {added_count} new columns"
                )
            else:
                print(f"\n✅ Users table schema is already up to date")

            return True

        except Exception as e:
            print(f"❌ Users table update failed: {e}")
            return False


def verify_enhanced_schema():
    """Verify that all enhanced fields and tables are present"""
    app = create_app("default")

    with app.app_context():
        try:
            print("\n🔍 Verifying complete enhanced schema...")

            # Check trading_bot_status table
            with db.engine.connect() as connection:
                result = connection.execute(
                    text("SHOW TABLES LIKE 'trading_bot_status'")
                )
                if result.fetchone():
                    print("   ✅ trading_bot_status table: EXISTS")
                else:
                    print("   ❌ trading_bot_status table: MISSING")
                    return False

            # Test accessing enhanced User fields
            user = User.query.first()
            if user:
                test_fields = [
                    "subscription_tier",
                    "subscription_expires",
                    "subscription_auto_renew",
                    "ai_enabled",
                    "risk_tolerance",
                    "trader_rating",
                    "total_followers",
                    "total_copiers",
                    "total_profit",
                    "win_rate",
                    "sharpe_ratio",
                ]

                for field in test_fields:
                    try:
                        getattr(user, field)
                        print(f"   ✅ User.{field}: OK")
                    except Exception as e:
                        print(f"   ❌ User.{field}: {e}")
                        return False
            else:
                print("   ⚠️ No users found to test, but schema appears correct")

            # Test TradingBotStatus model
            try:
                bot_status_count = TradingBotStatus.query.count()
                print(f"   ✅ TradingBotStatus model: OK ({bot_status_count} records)")
            except Exception as e:
                print(f"   ❌ TradingBotStatus model: {e}")
                return False

            print(f"\n🎉 Complete schema verification successful!")
            return True

        except Exception as e:
            print(f"❌ Schema verification failed: {e}")
            return False


if __name__ == "__main__":
    print("🚀 Trade Mantra Complete Schema Update")
    print("=" * 50)

    success = True

    # 1. Update User table schema
    if not update_user_schema():
        success = False

    # 2. Create trading_bot_status table
    if not create_trading_bot_status_table():
        success = False

    # 3. Verify everything is working
    if success and verify_enhanced_schema():
        print("\n🎉 Complete database schema update successful!")
        print("🚀 All enhanced features are now database-ready!")
    else:
        print("\n❌ Schema update failed. Please check the errors above.")
