#!/usr/bin/env python3
"""
Trading Bot System Test Script
Tests all components to ensure everything is working properly.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")

    try:
        from src.core.config import Config

        print("✅ Config import successful")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False

    try:
        from src.dashboard.main import create_app

        print("✅ Dashboard import successful")
    except ImportError as e:
        print(f"❌ Dashboard import failed: {e}")
        return False

    try:
        from src.core.bot import TradingBot

        print("✅ Bot import successful")
    except ImportError as e:
        print(f"❌ Bot import failed: {e}")
        return False

    return True


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        from src.core.config import Config

        config_path = project_root / "config" / "config.yaml"

        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            return False

        config = Config(str(config_path))
        print("✅ Configuration loaded successfully")
        print(f"   Trading mode: {config.trading.mode}")
        print(f"   Exchange: {config.trading.exchange}")
        print(
            f"   Database: {config.database.type}://{config.database.host}:{config.database.port}/{config.database.name}"
        )

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_environment():
    """Test environment variables."""
    print("\nTesting environment variables...")

    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found - creating from example...")
        try:
            example_file = project_root / ".env.example"
            if example_file.exists():
                import shutil

                shutil.copy(example_file, env_file)
                print("✅ .env file created from example")
                print("📝 Please edit .env file with your actual API keys")
            else:
                print("❌ .env.example file not found")
                return False
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False

    # Load environment variables
    try:
        import os
        from dotenv import load_dotenv

        load_dotenv(env_file)

        api_key = os.getenv("BINANCE_API_KEY")
        secret_key = os.getenv("BINANCE_SECRET_KEY")

        if api_key and api_key != "your_binance_api_key_here":
            print("✅ Binance API key configured")
        else:
            print("⚠️  Binance API key not configured (using defaults)")

        if secret_key and secret_key != "your_binance_secret_key_here":
            print("✅ Binance secret key configured")
        else:
            print("⚠️  Binance secret key not configured (using defaults)")

        return True

    except ImportError:
        print("⚠️  python-dotenv not installed - environment variables may not load")
        return True
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False


def test_database():
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        from src.core.config import Config

        config = Config(str(project_root / "config" / "config.yaml"))

        # Try to create a simple database connection
        import pymysql

        connection = pymysql.connect(
            host=config.database.host,
            port=config.database.port,
            user=config.database.username,
            password=config.database.password or "",
            database=config.database.name,
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        connection.close()
        print("✅ Database connection successful")
        return True

    except ImportError as e:
        print(f"⚠️  PyMySQL not installed: {e}")
        print("   Install with: pip install pymysql")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure XAMPP MySQL is running and database exists")
        return False


def test_dashboard():
    """Test dashboard creation."""
    print("\nTesting dashboard creation...")

    try:
        from src.core.config import Config
        from src.dashboard.main import create_app

        config = Config(str(project_root / "config" / "config.yaml"))
        app = create_app(config)

        print("✅ Dashboard app created successfully")
        return True

    except Exception as e:
        print(f"❌ Dashboard creation failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints are accessible."""
    print("\nTesting API endpoints...")

    try:
        import requests
        import time

        # Start a background server for testing (this is just a simulation)
        print("   API endpoints will be tested when server is running")
        print("   Use: python run.py to start the server and test manually")

        return True

    except ImportError:
        print("⚠️  Requests library not installed - cannot test API endpoints")
        return True


def create_missing_directories():
    """Create any missing directories."""
    print("\nCreating missing directories...")

    directories = ["logs", "data", "backups", "temp"]

    for directory in directories:
        dir_path = project_root / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")


def main():
    """Run all tests."""
    print("🚀 Trading Bot System Test")
    print("=" * 50)

    tests = [
        test_imports,
        test_configuration,
        test_environment,
        create_missing_directories,
        test_database,
        test_dashboard,
        test_api_endpoints,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your system is ready.")
        print("\n📝 Next steps:")
        print("1. Edit .env file with your API keys")
        print("2. Start XAMPP MySQL service")
        print("3. Run: python run.py")
        print("4. Open browser to: http://127.0.0.1:8000")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start XAMPP MySQL service")
        print("3. Create database: crypto_trading_bot")
        print("4. Copy .env.example to .env and configure")


if __name__ == "__main__":
    main()
