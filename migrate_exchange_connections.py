#!/usr/bin/env python3
"""
Migration script to add exchange_connections table
"""

import sqlite3
import os


def migrate_exchange_connections():
    """Add exchange_connections table to the database"""
    db_path = os.path.join(os.path.dirname(__file__), "dev.db")

    # Create instance directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if table already exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='exchange_connections'
        """
        )

        if cursor.fetchone() is None:
            print("Creating exchange_connections table...")

            cursor.execute(
                """
                CREATE TABLE exchange_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exchange_name VARCHAR(50) NOT NULL,
                    api_key VARCHAR(255),
                    api_secret VARCHAR(255),
                    access_token VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'disconnected' NOT NULL,
                    last_connected DATETIME,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            print("✅ exchange_connections table created successfully!")
        else:
            print("✅ exchange_connections table already exists!")

        conn.commit()

    except Exception as e:
        print(f"❌ Error creating exchange_connections table: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    migrate_exchange_connections()
