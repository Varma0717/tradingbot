"""
Test the dashboard startup process step by step.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


async def test_dashboard():
    try:
        print("Testing dashboard import...")
        from src.dashboard.main import DashboardApp
        from src.core.config import Config

        print("Creating config...")
        config = Config()

        print("Creating dashboard app...")
        dashboard_app = DashboardApp(config)

        print("Dashboard app created successfully!")
        print("Note: Use start_dashboard.py to actually run the server")

    except Exception as e:
        print(f"Dashboard test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_dashboard())
