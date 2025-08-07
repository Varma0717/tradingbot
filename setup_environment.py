#!/usr/bin/env python3
"""
Trading Bot Environment Setup Script
Automatically sets up the environment and fixes common issues.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent


def setup_environment():
    """Set up .env file from example."""
    print("🔧 Setting up environment file...")

    env_file = project_root / ".env"
    example_file = project_root / ".env.example"

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if not example_file.exists():
        print("❌ .env.example file not found")
        return False

    try:
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from example")
        print("📝 Please edit .env file with your actual configuration")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def setup_database():
    """Create database if it doesn't exist."""
    print("\n🗄️ Setting up database...")

    try:
        import pymysql

        # Connect without specifying database
        connection = pymysql.connect(
            host="localhost", port=3306, user="root", password=""
        )

        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_trading_bot")
            cursor.execute("USE crypto_trading_bot")

            # Create basic tables
            tables = [
                """
                CREATE TABLE IF NOT EXISTS bot_status (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    status VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details JSON
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS trades (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    side ENUM('buy', 'sell') NOT NULL,
                    amount DECIMAL(20, 8) NOT NULL,
                    price DECIMAL(20, 8) NOT NULL,
                    fee DECIMAL(20, 8) DEFAULT 0,
                    pnl DECIMAL(20, 8) DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'pending',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    amount DECIMAL(20, 8) NOT NULL,
                    value DECIMAL(20, 8) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_symbol (symbol)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS strategies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    status ENUM('active', 'inactive', 'paused') DEFAULT 'inactive',
                    config JSON,
                    performance JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """,
            ]

            for table_sql in tables:
                cursor.execute(table_sql)

            # Insert sample data
            sample_data = [
                "INSERT IGNORE INTO bot_status (status, details) VALUES ('stopped', '{\"message\": \"Bot initialized\"}')",
                """INSERT IGNORE INTO portfolio (symbol, amount, value) VALUES 
                   ('USDT', 10000.00, 10000.00),
                   ('BTC', 0.0, 0.0),
                   ('ETH', 0.0, 0.0)""",
                """INSERT IGNORE INTO strategies (name, symbol, status, config) VALUES 
                   ('MA Crossover BTC', 'BTC/USDT', 'inactive', '{"fast_ma": 20, "slow_ma": 50}'),
                   ('RSI Strategy ETH', 'ETH/USDT', 'inactive', '{"rsi_period": 14, "overbought": 70, "oversold": 30}')""",
            ]

            for sql in sample_data:
                cursor.execute(sql)

            connection.commit()

        connection.close()
        print("✅ Database setup completed")
        return True

    except ImportError:
        print("❌ PyMySQL not installed. Install with: pip install pymysql")
        return False
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("   Make sure XAMPP MySQL is running")
        return False


def install_dependencies():
    """Install required Python packages."""
    print("\n📦 Installing dependencies...")

    requirements_file = project_root / "requirements.txt"

    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")

    directories = [
        "logs",
        "data",
        "backups",
        "temp",
        "src/dashboard/static/css",
        "src/dashboard/static/js",
        "src/dashboard/templates",
    ]

    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory ready: {directory}")


def setup_configuration():
    """Ensure configuration is properly set."""
    print("\n⚙️ Checking configuration...")

    config_file = project_root / "config" / "config.yaml"

    if not config_file.exists():
        print("❌ config.yaml not found")
        return False

    # Read and validate config
    try:
        import yaml

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Check essential settings
        essential_keys = ["trading", "database", "exchanges", "risk", "strategies"]

        missing_keys = [key for key in essential_keys if key not in config]

        if missing_keys:
            print(f"❌ Missing configuration sections: {missing_keys}")
            return False

        print("✅ Configuration file is valid")
        return True

    except ImportError:
        print("❌ PyYAML not installed. Install with: pip install pyyaml")
        return False
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def check_xampp():
    """Check if XAMPP services are running."""
    print("\n🔍 Checking XAMPP services...")

    try:
        import socket

        # Check MySQL
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 3306))
        sock.close()

        if result == 0:
            print("✅ MySQL service is running")
            return True
        else:
            print("❌ MySQL service is not running")
            print("   Please start XAMPP and enable MySQL service")
            return False

    except Exception as e:
        print(f"❌ Failed to check XAMPP services: {e}")
        return False


def main():
    """Run the complete setup process."""
    print("🚀 Trading Bot Environment Setup")
    print("=" * 50)

    steps = [
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Installing dependencies", install_dependencies),
        ("Checking configuration", setup_configuration),
        ("Checking XAMPP services", check_xampp),
        ("Setting up database", setup_database),
    ]

    failed_steps = []

    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} crashed: {e}")
            failed_steps.append(step_name)

    print("\n" + "=" * 50)

    if not failed_steps:
        print("🎉 Environment setup completed successfully!")
        print("\n📝 Next steps:")
        print(
            "1. Edit .env file with your Binance API keys (optional for paper trading)"
        )
        print("2. Run: python test_system.py (to verify everything works)")
        print("3. Run: python run.py (to start the dashboard)")
        print("4. Open browser to: http://127.0.0.1:8000")
        print("\n⚠️  Important: Start with paper trading mode before using real money!")
    else:
        print(f"❌ Setup failed at: {', '.join(failed_steps)}")
        print("\n🔧 Please fix the issues above and run the setup again.")


if __name__ == "__main__":
    main()
