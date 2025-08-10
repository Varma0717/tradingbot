#!/usr/bin/env python3
"""
Database migration script to add exchange_type columns
"""

import sqlite3
import os
import sys


def migrate_database():
    """Add exchange_type columns to orders and trades tables"""

    db_path = "dev.db"
    if not os.path.exists(db_path):
        print("Database file not found. Will be created on first run.")
        return True

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if exchange_type column exists in orders table
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]

        if "exchange_type" not in columns:
            print("Adding exchange_type column to orders table...")
            cursor.execute(
                'ALTER TABLE orders ADD COLUMN exchange_type VARCHAR(10) DEFAULT "stocks"'
            )
            print("✅ Added exchange_type column to orders table")
        else:
            print("✅ exchange_type column already exists in orders table")

        # Check if exchange_type column exists in trades table
        cursor.execute("PRAGMA table_info(trades)")
        columns = [column[1] for column in cursor.fetchall()]

        if "exchange_type" not in columns:
            print("Adding exchange_type column to trades table...")
            cursor.execute(
                'ALTER TABLE trades ADD COLUMN exchange_type VARCHAR(10) DEFAULT "stocks"'
            )
            print("✅ Added exchange_type column to trades table")
        else:
            print("✅ exchange_type column already exists in trades table")

        conn.commit()
        print("🎉 Database migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if "conn" in locals():
            conn.rollback()
        return False
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
