"""
Binance API Key Management Script
Run this to properly store your Binance API credentials in the database
"""

from app import create_app, db
from app.models import ExchangeConnection


def add_binance_credentials():
    app = create_app()
    with app.app_context():
        # Get user input
        user_id = int(input("Enter your user ID: "))
        api_key = input("Enter your Binance API Key: ").strip()
        api_secret = input("Enter your Binance API Secret: ").strip()

        use_testnet = input("Use Binance Testnet? (y/n): ").strip().lower() == "y"
        exchange_name = "binance_testnet" if use_testnet else "binance"

        # Check if connection already exists
        existing = ExchangeConnection.query.filter_by(
            user_id=user_id, exchange_name=exchange_name
        ).first()

        if existing:
            print(f"Updating existing {exchange_name} connection...")
            existing.api_key = api_key
            existing.api_secret = api_secret
            existing.status = "connected"
            existing.error_message = None
        else:
            print(f"Creating new {exchange_name} connection...")
            connection = ExchangeConnection(
                user_id=user_id,
                exchange_name=exchange_name,
                api_key=api_key,
                api_secret=api_secret,
                status="connected",
            )
            db.session.add(connection)

        db.session.commit()
        print(f"✅ Binance credentials saved successfully for user {user_id}")
        print(f"Exchange: {exchange_name}")
        print(f"API Key: {api_key[:8]}...")


if __name__ == "__main__":
    print("Binance API Key Management")
    print("=" * 30)
    add_binance_credentials()
