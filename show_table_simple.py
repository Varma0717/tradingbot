#!/usr/bin/env python3
"""
Check table structure
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
        result = db.session.execute(text("SHOW CREATE TABLE trading_bot_status;"))
        create_sql = result.fetchone()[1]
        print("Current table structure:")
        print("=" * 60)
        print(create_sql)


if __name__ == "__main__":
    main()
