#!/usr/bin/env python3
"""
Remove the old user_id unique constraint while keeping the foreign key
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from sqlalchemy import text


def main():
    app = create_app()

    with app.app_context():
        print("=== Removing Old user_id Unique Constraint ===")

        try:
            # Check current constraints
            print("Current constraints:")
            result = db.session.execute(
                text(
                    """
                SHOW INDEX FROM trading_bot_status;
            """
                )
            )

            for row in result:
                print(f"  {row[2]} (non_unique={row[1]}): {row[4]}")

            print("\nRemoving old user_id unique constraint...")

            # Drop the user_id unique constraint (but keep the foreign key)
            db.session.execute(
                text(
                    """
                ALTER TABLE trading_bot_status 
                DROP INDEX user_id;
            """
                )
            )

            db.session.commit()
            print("✅ Successfully removed old user_id unique constraint")

            # Verify the change
            print("\nNew constraints:")
            result = db.session.execute(
                text(
                    """
                SHOW INDEX FROM trading_bot_status;
            """
                )
            )

            for row in result:
                print(f"  {row[2]} (non_unique={row[1]}): {row[4]}")

        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()


if __name__ == "__main__":
    main()
