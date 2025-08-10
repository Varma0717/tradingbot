#!/usr/bin/env python3
"""
Check database tables and schema
"""

import sqlite3
import os


def check_database():
    db_path = "dev.db"
    if not os.path.exists(db_path):
        print("Database file not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Existing tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # If orders table exists, check its schema
    if any(t[0] == "orders" for t in tables):
        print("\nOrders table schema:")
        cursor.execute("PRAGMA table_info(orders)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

    conn.close()


if __name__ == "__main__":
    check_database()
