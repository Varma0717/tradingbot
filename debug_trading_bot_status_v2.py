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
            print("-" * 60)

            for status in statuses:
                user = User.query.get(status.user_id)
                print(
                    f"User ID: {status.user_id} ({user.email if user else 'Unknown'})"
                )
                print(f"  Bot Type: {status.bot_type}")
                print(f"  Is Running: {status.is_running}")
                print(f"  Created: {status.created_at}")
                print(f"  Updated: {status.updated_at}")

                # Parse status data
                try:
                    status_data = status.get_status()
                    print(f"  Status Data: {status_data}")
                except Exception as e:
                    print(f"  Error getting status data: {e}")
                print("-" * 60)

    except Exception as e:
        print(f"Error: {e}")
