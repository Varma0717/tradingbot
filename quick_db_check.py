#!/usr/bin/env python3
"""
Quick database check script
"""
import sys
import os

sys.path.insert(0, os.path.abspath("."))

try:
    from app import create_app
    from app.models import TradingBotStatus, ExchangeConnection, User

    app = create_app()

    with app.app_context():
        print("🔍 Database Check...")

        # Check exchange connections for user 2
        connections = ExchangeConnection.query.filter_by(user_id=2).all()
        print(f"Exchange connections for user 2: {len(connections)}")

        if not connections:
            print("❌ No exchange connections - this is why stock bot doesn't start!")

            # Create a mock exchange connection for testing
            from app.models import ExchangeConnection

            mock_conn = ExchangeConnection(
                user_id=2,
                exchange_name="mock_exchange",
                status="connected",
                api_key="test_key",
                api_secret="test_secret",
            )
            from app import db

            db.session.add(mock_conn)
            db.session.commit()
            print("✅ Created mock exchange connection for user 2")
        else:
            for conn in connections:
                print(f"  {conn.exchange_name}: {conn.status}")

        # Check bot status
        bots = TradingBotStatus.query.filter_by(user_id=2).all()
        print(f"Bot statuses for user 2: {len(bots)}")
        for bot in bots:
            print(f"  {bot.bot_type}: running={bot.is_running}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
