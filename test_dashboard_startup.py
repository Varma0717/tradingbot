"""
Quick test to see if dashboard starts without errors.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


def test_dashboard_startup():
    print("🔧 Testing Dashboard Startup...")

    try:
        from src.dashboard.main import DashboardApp
        from src.core.config import Config
        from src.utils.logger import setup_logging

        # Setup logging
        setup_logging(level="INFO")

        # Initialize configuration
        config = Config()

        # Create dashboard app
        dashboard_app = DashboardApp(config)

        print("✅ Dashboard app created successfully!")
        print("✅ All imports working!")
        print("✅ Configuration loaded!")
        print(f"✅ Default host: {config.dashboard.host}")
        print(f"✅ Default port: {config.dashboard.port}")

        print("\n🚀 Ready to start dashboard!")
        print("   Run: python start_dashboard.py")
        print("   Access: http://127.0.0.1:8001")

    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_dashboard_startup()
