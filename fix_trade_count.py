import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Trade, TradingBotStatus, db

# Create app and setup database context
app = create_app()

with app.app_context():
    try:
        # Query actual trade count for user 2 stock trades
        user_id = 2
        stock_trade_count = Trade.query.filter_by(
            user_id=user_id, exchange_type="stocks"
        ).count()

        print(
            f"Actual stock trades in database for user {user_id}: {stock_trade_count}"
        )

        # Get the current TradingBotStatus record for stock bot
        stock_status = TradingBotStatus.query.filter_by(
            user_id=user_id, bot_type="stock"
        ).first()

        if stock_status:
            print(f"Current TradingBotStatus total_trades: {stock_status.total_trades}")

            # Update the total_trades field to match actual count
            stock_status.total_trades = stock_trade_count
            db.session.commit()

            print(f"Updated TradingBotStatus total_trades to: {stock_trade_count}")
        else:
            print("No stock TradingBotStatus record found")

        # Also check crypto for comparison
        crypto_trade_count = Trade.query.filter_by(
            user_id=user_id, exchange_type="crypto"
        ).count()

        print(
            f"\nActual crypto trades in database for user {user_id}: {crypto_trade_count}"
        )

        crypto_status = TradingBotStatus.query.filter_by(
            user_id=user_id, bot_type="crypto"
        ).first()

        if crypto_status:
            print(
                f"Current crypto TradingBotStatus total_trades: {crypto_status.total_trades}"
            )

            # Update the total_trades field to match actual count
            crypto_status.total_trades = crypto_trade_count
            db.session.commit()

            print(
                f"Updated crypto TradingBotStatus total_trades to: {crypto_trade_count}"
            )

    except Exception as e:
        print(f"Error: {e}")
