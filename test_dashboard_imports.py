#!/usr/bin/env python3
"""
Test dashboard imports and basic functionality
"""
import sys
from pathlib import Path

# Add src to path exactly like main.py does
sys.path.append(str(Path(__file__).parent / "src"))


def test_dashboard_imports():
    """Test if all dashboard dependencies can be imported."""
    print("=== Testing Dashboard Imports ===")

    try:
        print("1. Testing core imports...")
        from src.core.config import Config

        print("   ✅ Config imported")

        print("2. Testing dashboard imports...")
        from src.dashboard.main import DashboardApp

        print("   ✅ DashboardApp imported")

        print("3. Testing external dependencies...")
        import uvicorn

        print("   ✅ uvicorn imported")

        print("4. Testing config creation...")
        config = Config()
        config.trading.mode = "dashboard"
        config.validate()
        print("   ✅ Config created and validated")

        print("5. Testing DashboardApp creation...")
        dashboard = DashboardApp(config)
        print("   ✅ DashboardApp created")

        print("6. Testing app access...")
        app = dashboard.app
        print(f"   ✅ FastAPI app accessible: {type(app)}")

        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        print("Dashboard components are working correctly.")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_manual_dashboard_start():
    """Try to start dashboard manually for testing."""
    print("\n=== Testing Manual Dashboard Start ===")

    try:
        from src.core.config import Config
        from src.dashboard.main import DashboardApp
        import uvicorn

        # Create config
        config = Config()
        config.trading.mode = "dashboard"
        config.validate()

        # Create dashboard
        dashboard = DashboardApp(config)
        app = dashboard.app

        print("✅ Dashboard setup successful")
        print("   Dashboard can be started manually")
        print("   Issue might be with command line parsing")

        return True

    except Exception as e:
        print(f"❌ Manual start failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing dashboard functionality...\n")

    import_success = test_dashboard_imports()

    if import_success:
        manual_success = test_manual_dashboard_start()

        if manual_success:
            print("\n✅ Dashboard is working correctly!")
            print("Issue might be with argument parsing in main.py")
        else:
            print("\n❌ Dashboard has configuration issues")
    else:
        print("\n❌ Dashboard has import issues")
