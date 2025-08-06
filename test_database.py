"""
Test database manager initialization step by step.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    print("Testing database manager import...")
    from src.core.config import Config
    from src.data.database import DatabaseManager

    print("Creating config object...")
    config = Config()

    print(f"Database URL: {config.database.url}")
    print(f"Database config type: {type(config.database)}")

    print("Creating database manager...")
    db_manager = DatabaseManager(config)

    print("Database manager created successfully!")

    print("Testing connection...")
    result = db_manager.connect()
    print(f"Connection result: {result}")

except Exception as e:
    print(f"Database test failed: {e}")
    import traceback

    traceback.print_exc()
