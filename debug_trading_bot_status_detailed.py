import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import TradingBotStatus, User

# Create app and setup database context
app = create_app()

with app.app_context():
    try:
        # Query all TradingBotStatus records
        statuses = TradingBotStatus.query.all()

        if not statuses:
            print("No TradingBotStatus records found in database.")
        else:
            print(f"Found {len(statuses)} TradingBotStatus records:")
            print("-" * 80)

            for status in statuses:
                user = User.query.get(status.user_id)
                print(
                    f"User ID: {status.user_id} ({user.email if user else 'Unknown'})"
                )
                print(f"  Bot Type: {status.bot_type}")
                print(f"  Is Running: {status.is_running}")
                print(f"  Is Active: {status.is_active}")
                print(f"  Strategies Active: {status.strategies_active}")
                print(f"  Open Positions: {status.open_positions}")
                print(f"  Total Trades: {status.total_trades}")
                print(f"  Daily PnL: {status.daily_pnl}")
                print(f"  Win Rate: {status.win_rate}")
                print(f"  Last Heartbeat: {status.last_heartbeat}")
                print(f"  Started At: {status.started_at}")
                print(f"  Strategies: {status.strategies}")
                print("-" * 80)

    except Exception as e:
        print(f"Error: {e}")
