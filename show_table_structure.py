#!/usr/bin/env python3
"""
Check detailed table structure and constraints
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
        # Get detailed table info
        result = db.session.execute(
            """
            SHOW CREATE TABLE trading_bot_status;
        """
        )

        create_sql = result.fetchone()[1]
        print("Current table structure:")
        print("=" * 60)
        print(create_sql)
        print("=" * 60)

        # Show all constraints
        result = db.session.execute(
            """
            SELECT 
                CONSTRAINT_NAME, 
                CONSTRAINT_TYPE, 
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'trading_bot_status'
            ORDER BY CONSTRAINT_NAME;
        """
        )

        print("\nAll constraints:")
        for row in result:
            print(
                f"  {row[0]} ({row[1]}): {row[2]} -> {row[3]}.{row[4] if row[4] else 'N/A'}"
            )


if __name__ == "__main__":
    main()
