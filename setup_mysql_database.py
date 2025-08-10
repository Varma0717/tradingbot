#!/usr/bin/env python3
"""
TradeMantra Database Setup Script for MySQL/XAMPP
This script creates the MySQL database and all required tables
"""

import pymysql
import os
import sys
from datetime import datetime


def create_database():
    """Create the trademantra database if it doesn't exist"""

    # Connection parameters for XAMPP MySQL
    connection_params = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",  # Default XAMPP MySQL has no password
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }

    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(**connection_params)
        print("✅ Connected to MySQL server")

        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS `trademantra` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print("✅ Database 'trademantra' created/verified")

            # Switch to the trademantra database
            cursor.execute("USE `trademantra`")

            # Create tables
            create_tables(cursor)

        # Commit all changes
        connection.commit()
        print("🎉 Database setup completed successfully!")

    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    finally:
        if "connection" in locals():
            connection.close()

    return True


def create_tables(cursor):
    """Create all required tables"""

    # Users table
    users_table = """
    CREATE TABLE IF NOT EXISTS `users` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `username` VARCHAR(64) NOT NULL UNIQUE,
        `email` VARCHAR(120) NOT NULL UNIQUE,
        `password_hash` VARCHAR(128) NOT NULL,
        `role` VARCHAR(20) NOT NULL DEFAULT 'user',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX `idx_username` (`username`),
        INDEX `idx_email` (`email`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(users_table)
    print("✅ Created 'users' table")

    # Subscriptions table
    subscriptions_table = """
    CREATE TABLE IF NOT EXISTS `subscriptions` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL UNIQUE,
        `plan` VARCHAR(20) NOT NULL DEFAULT 'free',
        `start_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `end_date` DATETIME NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'active',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(subscriptions_table)
    print("✅ Created 'subscriptions' table")

    # User Preferences table
    user_preferences_table = """
    CREATE TABLE IF NOT EXISTS `user_preferences` (
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

    # Strategies table
    strategies_table = """
    CREATE TABLE IF NOT EXISTS `strategies` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `name` VARCHAR(100) NOT NULL,
        `parameters` JSON NULL,
        `is_active` BOOLEAN NOT NULL DEFAULT FALSE,
        `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(strategies_table)
    print("✅ Created 'strategies' table")

    # Orders table
    orders_table = """
    CREATE TABLE IF NOT EXISTS `orders` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `strategy_id` INT NULL,
        `symbol` VARCHAR(20) NOT NULL,
        `exchange_type` VARCHAR(10) NOT NULL DEFAULT 'stocks',
        `quantity` DECIMAL(20,8) NOT NULL,
        `order_type` VARCHAR(20) NOT NULL,
        `side` VARCHAR(10) NOT NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
        `price` DECIMAL(20,8) NULL,
        `filled_price` DECIMAL(20,8) NULL,
        `filled_quantity` DECIMAL(20,8) DEFAULT 0,
        `exchange_order_id` VARCHAR(100) NULL,
        `error_message` TEXT NULL,
        `is_paper` BOOLEAN NOT NULL DEFAULT TRUE,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
        FOREIGN KEY (`strategy_id`) REFERENCES `strategies`(`id`) ON DELETE SET NULL,
        INDEX `idx_user_created` (`user_id`, `created_at`),
        INDEX `idx_symbol` (`symbol`),
        INDEX `idx_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(orders_table)
    print("✅ Created 'orders' table")

    # Trades table
    trades_table = """
    CREATE TABLE IF NOT EXISTS `trades` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `order_id` INT NOT NULL,
        `user_id` INT NOT NULL,
        `symbol` VARCHAR(20) NOT NULL,
        `exchange_type` VARCHAR(10) NOT NULL DEFAULT 'stocks',
        `quantity` DECIMAL(20,8) NOT NULL,
        `price` DECIMAL(20,8) NOT NULL,
        `side` VARCHAR(10) NOT NULL,
        `fees` DECIMAL(20,8) DEFAULT 0.0,
        `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
        INDEX `idx_user_timestamp` (`user_id`, `timestamp`),
        INDEX `idx_symbol` (`symbol`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(trades_table)
    print("✅ Created 'trades' table")

    # Payments table
    payments_table = """
    CREATE TABLE IF NOT EXISTS `payments` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `amount` DECIMAL(10,2) NOT NULL,
        `currency` VARCHAR(10) NOT NULL DEFAULT 'INR',
        `razorpay_payment_id` VARCHAR(100) UNIQUE NULL,
        `razorpay_order_id` VARCHAR(100) UNIQUE NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'created',
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(payments_table)
    print("✅ Created 'payments' table")

    # Exchange Connections table
    exchange_connections_table = """
    CREATE TABLE IF NOT EXISTS `exchange_connections` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `exchange_name` VARCHAR(50) NOT NULL,
        `api_key` VARCHAR(255) NULL,
        `api_secret` VARCHAR(255) NULL,
        `access_token` VARCHAR(255) NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'disconnected',
        `last_connected` DATETIME NULL,
        `error_message` TEXT NULL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
        INDEX `idx_user_exchange` (`user_id`, `exchange_name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(exchange_connections_table)
    print("✅ Created 'exchange_connections' table")

    # Audit Logs table
    audit_logs_table = """
    CREATE TABLE IF NOT EXISTS `audit_logs` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NULL,
        `action` VARCHAR(255) NOT NULL,
        `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `details` JSON NULL,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
        INDEX `idx_timestamp` (`timestamp`),
        INDEX `idx_user_timestamp` (`user_id`, `timestamp`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(audit_logs_table)
    print("✅ Created 'audit_logs' table")


def create_sample_data(cursor):
    """Create sample admin user and initial data"""

    # Create admin user (password: admin123)
    admin_password_hash = (
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNVL6UDGVSqNa"  # admin123
    )

    admin_user = """
    INSERT IGNORE INTO `users` (`username`, `email`, `password_hash`, `role`)
    VALUES ('admin', 'admin@trademantra.com', %s, 'admin')
    """
    cursor.execute(admin_user, (admin_password_hash,))
    print("✅ Created admin user (username: admin, password: admin123)")

    # Create sample regular user (password: user123)
    user_password_hash = (
        "$2b$12$wE0Uqo6LE1KJT7I.ZHs3TOhR2Q9/tGGHt.wV8r7qJhvY5oN5/OoJO"  # user123
    )

    sample_user = """
    INSERT IGNORE INTO `users` (`username`, `email`, `password_hash`, `role`)
    VALUES ('trader', 'trader@trademantra.com', %s, 'user')
    """
    cursor.execute(sample_user, (user_password_hash,))
    print("✅ Created sample user (username: trader, password: user123)")


def check_xampp_status():
    """Check if XAMPP MySQL is running"""
    try:
        connection = pymysql.connect(
            host="localhost", port=3306, user="root", password=""
        )
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Cannot connect to XAMPP MySQL: {e}")
        print("📝 Please make sure:")
        print("   1. XAMPP is installed and running")
        print("   2. MySQL service is started in XAMPP Control Panel")
        print("   3. MySQL is running on port 3306")
        return False


if __name__ == "__main__":
    print("🚀 TradeMantra Database Setup")
    print("=" * 40)

    # Check XAMPP status first
    if not check_xampp_status():
        sys.exit(1)

    # Create database and tables
    if create_database():
        # Create sample data
        try:
            connection = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="",
                database="trademantra",
                charset="utf8mb4",
            )

            with connection.cursor() as cursor:
                create_sample_data(cursor)

            connection.commit()
            connection.close()

            print("\n🎉 Setup completed successfully!")
            print("📊 Database: trademantra")
            print("🔐 Admin login: admin / admin123")
            print("👤 User login: trader / user123")
            print("🌐 Access your app at: http://localhost/application")

        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            sys.exit(1)
    else:
        sys.exit(1)
