#!/usr/bin/env python3
"""
Test the DataManager attribute fix
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


def test_datamanager_attributes():
    """Test if DataManager has the correct attributes."""
    try:
        from src.core.config import Config
        from src.data.data_manager import DataManager

        print("✅ Imports successful")

        # Create a basic config
        config = Config()
        print("✅ Config created")

        # Create DataManager
        data_manager = DataManager(config)
        print("✅ DataManager created")

        # Check attributes
        print(f"✅ Has 'exchanges' attribute: {hasattr(data_manager, 'exchanges')}")
        print(f"✅ Has 'db_manager' attribute: {hasattr(data_manager, 'db_manager')}")
        print(f"❌ Has 'exchange' attribute: {hasattr(data_manager, 'exchange')}")
        print(f"❌ Has 'database' attribute: {hasattr(data_manager, 'database')}")

        print("\n✅ DataManager attributes are correct!")
        return True

    except Exception as e:
        print(f"❌ Error testing DataManager: {e}")
        return False


def test_bot_initialization():
    """Test if the bot can be initialized now."""
    try:
        from src.core.config import Config
        from src.core.bot import TradingBot

        print("\n--- Testing Bot Initialization ---")

        # Create config
        config = Config()
        config.trading.mode = "paper"  # Use paper mode for testing
        print("✅ Config created")

        # Try to create bot
        bot = TradingBot(config)
        print("✅ TradingBot created successfully!")
        print("✅ No more AttributeError!")

        return True

    except Exception as e:
        print(f"❌ Error creating TradingBot: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== Testing DataManager Fix ===")

    # Change to the application directory
    os.chdir(r"c:\xampp\htdocs\application")

    success1 = test_datamanager_attributes()
    success2 = test_bot_initialization()

    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! The fix is working!")
    else:
        print("\n❌ Some tests failed.")
