"""
Database setup script for the crypto trading bot.
This script creates all necessary tables in the MySQL database.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.data.database import DatabaseManager
from src.core.config import Config
from src.utils.logger import setup_logging


def main():
    """Setup database tables."""
    logger = None
    try:
        # Setup logging
        setup_logging(level="INFO")
        logger = logging.getLogger(__name__)

        logger.info("Starting database setup...")

        # Initialize config and database
        config = Config()

        # Create database manager - this will automatically create tables
        logger.info("Creating database tables...")
        db_manager = DatabaseManager(config)

        logger.info("Database setup completed successfully!")
        logger.info(f"Connected to: {config.database.url}")
        return True

    except Exception as e:
        if logger:
            logger.error(f"Database setup failed: {e}")
        else:
            print(f"Database setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
