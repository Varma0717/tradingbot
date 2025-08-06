"""
Startup script for the crypto trading bot da        # Start the dashboard application (this will block)
        dashboard_app.run(
            host="127.0.0.1",
            port=8001,  # Use port 8001 instead of 8000
            debug=config.dashboard.debug
        )d.
This script runs the web dashboard with integrated trading bot functionality.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.dashboard.main import DashboardApp
from src.core.config import Config
from src.utils.logger import setup_logging


def setup_signal_handlers(dashboard_app):
    """Setup signal handlers for graceful shutdown."""

    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main function to start the dashboard application."""
    logger = None
    try:
        # Setup logging
        setup_logging(level="INFO")
        logger = logging.getLogger(__name__)

        logger.info("Starting Crypto Trading Bot Dashboard...")

        # Initialize configuration
        config = Config()

        # Create and start dashboard app
        dashboard_app = DashboardApp(config)

        # Setup signal handlers for graceful shutdown
        setup_signal_handlers(dashboard_app)

        # Start the dashboard application (this will block)
        dashboard_app.run(
            host=config.dashboard.host,
            port=config.dashboard.port,
            debug=config.dashboard.debug,
        )

    except Exception as e:
        if logger:
            logger.error(f"Failed to start dashboard: {e}")
        else:
            print(f"Failed to start dashboard: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Application failed: {e}")
        sys.exit(1)
