"""
Test script to verify settings database functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.data.database import DatabaseManager
from src.core.config import Config


async def test_settings():
    """Test settings save and load functionality."""
    print("Testing settings functionality...")

    try:
        # Initialize database manager
        config = Config()
        db_manager = DatabaseManager(config)

        # Test saving settings
        print("1. Testing save settings...")
        settings_data = {
            "trading": {
                "mode": "paper",
                "primary_symbol": "BTC/USDT",
                "base_amount": 100.0,
                "max_trades": 5,
            },
            "risk": {"max_daily_loss": 5.0, "stop_loss_pct": 3.0},
            "notifications": {
                "enable_email": True,
                "notification_email": "test@example.com",
            },
        }

        success = await db_manager.save_settings_batch(settings_data)
        print(f"   Save result: {'✅ SUCCESS' if success else '❌ FAILED'}")

        # Test loading settings
        print("2. Testing load settings...")
        trading_settings = await db_manager.get_settings_by_category("trading")
        risk_settings = await db_manager.get_settings_by_category("risk")
        notification_settings = await db_manager.get_settings_by_category(
            "notifications"
        )

        print(f"   Trading settings loaded: {trading_settings}")
        print(f"   Risk settings loaded: {risk_settings}")
        print(f"   Notification settings loaded: {notification_settings}")

        # Test individual setting retrieval
        print("3. Testing individual setting retrieval...")
        mode = await db_manager.get_setting("trading", "mode", "unknown")
        email = await db_manager.get_setting("notifications", "notification_email", "")

        print(f"   Trading mode: {mode}")
        print(f"   Notification email: {email}")

        # Verify data integrity
        print("4. Verifying data integrity...")
        if (
            trading_settings.get("mode") == "paper"
            and risk_settings.get("max_daily_loss") == 5.0
            and notification_settings.get("enable_email") is True
        ):
            print("   ✅ Data integrity verified!")
            return True
        else:
            print("   ❌ Data integrity check failed!")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_settings())
    print(f"\nOverall test result: {'✅ PASSED' if success else '❌ FAILED'}")
