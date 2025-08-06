#!/usr/bin/env python3
"""Test script to verify all packages are working correctly"""


def test_imports():
    try:
        # Core trading libraries
        import ccxt

        print("✅ CCXT imported successfully")

        import pandas as pd

        print("✅ Pandas imported successfully")

        import numpy as np

        print("✅ NumPy imported successfully")

        # Web framework
        import fastapi

        print("✅ FastAPI imported successfully")

        import uvicorn

        print("✅ Uvicorn imported successfully")

        # Database
        import sqlalchemy

        print("✅ SQLAlchemy imported successfully")

        import pymysql

        print("✅ PyMySQL imported successfully")

        # Other utilities
        import requests

        print("✅ Requests imported successfully")

        import aiohttp

        print("✅ Aiohttp imported successfully")

        # Test simple operations
        df = pd.DataFrame({"test": [1, 2, 3]})
        print(f"✅ Pandas DataFrame created: {len(df)} rows")

        # Test CCXT exchanges
        exchanges = ccxt.exchanges
        print(f"✅ CCXT available exchanges: {len(exchanges)}")

        print("\n🎉 ALL PACKAGES WORKING CORRECTLY!")
        print("Your virtual environment is ready for the crypto trading bot!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_imports()
