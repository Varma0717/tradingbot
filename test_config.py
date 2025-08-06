"""
Simple test to isolate the configuration issue.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    print("Testing configuration import...")
    from src.core.config import Config

    print("Creating config object...")
    config = Config()

    print("Accessing database config...")
    print(f"Database URL: {config.database.url}")
    print(f"Pool size: {config.database.pool_size}")
    print(f"Pool size type: {type(config.database.pool_size)}")

    print("Configuration test successful!")

except Exception as e:
    print(f"Configuration test failed: {e}")
    import traceback

    traceback.print_exc()
