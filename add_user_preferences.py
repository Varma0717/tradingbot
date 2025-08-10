#!/usr/bin/env python3
"""
Database migration script to add user_preferences table to existing MySQL database
"""

import pymysql
import sys


def update_database():
    """Add user_preferences table to existing database"""

    try:
        # Connect to MySQL database
        connection = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="",
            database="trademantra",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        print("✅ Connected to MySQL database")

        with connection.cursor() as cursor:
            # Check if user_preferences table exists
            cursor.execute("SHOW TABLES LIKE 'user_preferences'")
            if cursor.fetchone():
                print("ℹ️  user_preferences table already exists")
                return True

            # Create user_preferences table
            user_preferences_table = """
            CREATE TABLE `user_preferences` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `user_id` INT NOT NULL UNIQUE,
                `trading_mode` VARCHAR(10) NOT NULL DEFAULT 'paper',
                `default_exchange_type` VARCHAR(10) NOT NULL DEFAULT 'stocks',
                `risk_level` VARCHAR(10) NOT NULL DEFAULT 'medium',
                `max_position_size` DECIMAL(15,2) DEFAULT 10000.00,
                `daily_loss_limit` DECIMAL(15,2) DEFAULT 5000.00,
                `notifications_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
                `email_alerts` BOOLEAN NOT NULL DEFAULT TRUE,
                `sms_alerts` BOOLEAN NOT NULL DEFAULT FALSE,
                `theme` VARCHAR(10) NOT NULL DEFAULT 'dark',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(user_preferences_table)
            print("✅ Created 'user_preferences' table")

            # Create default preferences for existing users
            cursor.execute("SELECT id FROM users")
            users = cursor.fetchall()

            for user in users:
                cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, trading_mode, theme)
                    VALUES (%s, 'paper', 'dark')
                """,
                    (user["id"],),
                )

            print(f"✅ Created default preferences for {len(users)} users")

        # Commit all changes
        connection.commit()
        print("🎉 Database migration completed successfully!")

    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False
    finally:
        if "connection" in locals():
            connection.close()

    return True


if __name__ == "__main__":
    print("🚀 TradeMantra Database Migration - Adding User Preferences")
    print("=" * 60)

    if update_database():
        print("\n✅ Migration completed successfully!")
        print("📊 User preferences table has been added with default values")
    else:
        print("\n❌ Migration failed")
        sys.exit(1)
