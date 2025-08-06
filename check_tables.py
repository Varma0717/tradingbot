"""
Simple database table checker
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from src.data.database import (
    DatabaseManager,
    MarketData,
    TradeHistory,
    Portfolio,
    BotSettings,
)
from src.core.config import Config


def check_tables():
    try:
        dm = DatabaseManager(Config())
        session = dm.session_factory()

        print("Checking database tables...")

        # Check each table
        market_count = session.query(MarketData).count()
        print(f"MarketData records: {market_count}")

        trade_count = session.query(TradeHistory).count()
        print(f"TradeHistory records: {trade_count}")

        portfolio_count = session.query(Portfolio).count()
        print(f"Portfolio records: {portfolio_count}")

        settings_count = session.query(BotSettings).count()
        print(f"BotSettings records: {settings_count}")

        session.close()
        return True

    except Exception as e:
        print(f"Error checking tables: {e}")
        return False


if __name__ == "__main__":
    check_tables()
