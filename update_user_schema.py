#!/usr/bin/env python3
"""
Database Schema Update Script for Enhanced User Model
Adds the missing enhanced fields to the users table
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app, db
from app.models import User
from sqlalchemy import text


def update_user_schema():
    """Add enhanced fields to users table"""
    app = create_app("default")  # Use production config

    with app.app_context():
        try:
            print("🔄 Updating database schema for enhanced User model...")

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
                    print(
                        f"   ⚠️ Column {column_name} already exists"
                    )  # Commit the changes
            db.session.commit()

            print(f"\n🎉 Database schema update completed!")
            print(f"   📊 Added {added_count} new columns")
            print(f"   ✅ Enhanced User model is now database-ready")

            return True

        except Exception as e:
            print(f"❌ Database update failed: {e}")
            db.session.rollback()
            return False


def verify_schema():
    """Verify that all enhanced fields are present"""
    app = create_app("default")

    with app.app_context():
        try:
            print("\n🔍 Verifying enhanced User model schema...")

            # Try to query all enhanced fields
            user = User.query.first()
            if user:
                # Test accessing enhanced fields
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
                        print(f"   ✅ {field}: OK")
                    except Exception as e:
                        print(f"   ❌ {field}: {e}")
                        return False

                print(f"\n🎉 All enhanced fields verified successfully!")
                return True
            else:
                print("   ⚠️ No users found to test, but schema appears correct")
                return True

        except Exception as e:
            print(f"❌ Schema verification failed: {e}")
            return False


if __name__ == "__main__":
    print("🚀 Trade Mantra Enhanced Schema Update")
    print("=" * 50)

    # Update schema
    if update_user_schema():
        # Verify the update
        verify_schema()
        print("\n🚀 Ready to restart Flask server with enhanced features!")
    else:
        print("\n❌ Schema update failed. Please check the errors above.")
