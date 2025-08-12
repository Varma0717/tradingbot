#!/usr/bin/env python3
"""
Script to run the trading bot status migration safely.
"""

import os
import sys
from flask import Flask
from flask_migrate import upgrade, current, stamp
from app import create_app, db


def run_migration():
    """Run the trading bot status constraint migration."""

    # Create app instance
    app = create_app()

    with app.app_context():
        try:
            print("=" * 60)
            print("TRADING BOT STATUS MIGRATION")
            print("=" * 60)

            # Check current migration state
            current_rev = current()
            print(f"Current migration revision: {current_rev}")

            # Show what we're about to do
            print("\nThis migration will:")
            print("1. Check for duplicate user_id entries in trading_bot_status")
            print(
                "2. Fix any data conflicts by assigning bot_type ('stock' or 'crypto')"
            )
            print("3. Drop the old unique constraint on user_id")
            print("4. Add composite unique constraint on (user_id, bot_type)")

            # Ask for confirmation
            response = input("\nDo you want to proceed? (y/N): ").lower().strip()
            if response != "y":
                print("Migration cancelled.")
                return False

            print("\nStarting migration...")

            # Run the migration
            upgrade()

            print("\nMigration completed successfully!")
            print("You can now start both stock and crypto bots simultaneously.")

            # Verify the results
            print("\nVerifying migration results...")
            result = db.engine.execute(db.text("SHOW INDEX FROM trading_bot_status"))
            indexes = [row[2] for row in result]

            if "uq_user_bot_type" in indexes:
                print("✓ Composite unique constraint (user_id, bot_type) is active")
            else:
                print("✗ Warning: Composite constraint not found")

            if "user_id" not in indexes:
                print("✓ Old user_id unique constraint has been removed")
            else:
                print("✗ Warning: Old user_id constraint still exists")

            # Show current status records
            status_records = db.engine.execute(
                db.text(
                    """
                SELECT user_id, bot_type, is_running, created_at 
                FROM trading_bot_status 
                ORDER BY user_id, bot_type
            """
                )
            ).fetchall()

            if status_records:
                print(f"\nCurrent trading_bot_status records ({len(status_records)}):")
                print("user_id | bot_type | is_running | created_at")
                print("-" * 50)
                for record in status_records:
                    print(
                        f"{record[0]:7} | {record[1]:8} | {record[2]:10} | {record[3]}"
                    )
            else:
                print("\nNo trading bot status records found.")

            return True

        except Exception as e:
            print(f"\nMigration failed: {e}")
            print("You may need to manually fix the database or restore from backup.")
            return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
