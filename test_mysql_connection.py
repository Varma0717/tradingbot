#!/usr/bin/env python3
"""
Test script to verify MySQL database connection and Flask app integration
"""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from app import create_app, db
from app.models import User, Subscription, Strategy, Order, Trade, Payment


def test_database_connection():
    """Test database connection and basic operations"""

    print("🧪 Testing MySQL Database Connection")
    print("=" * 40)

    # Create Flask app
    app = create_app("default")

    with app.app_context():
        try:
            # Test basic connection
            from sqlalchemy import text

            db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful")

            # Test table access
            user_count = User.query.count()
            print(f"✅ Users table accessible - {user_count} users found")

            subscription_count = Subscription.query.count()
            print(
                f"✅ Subscriptions table accessible - {subscription_count} subscriptions found"
            )

            strategy_count = Strategy.query.count()
            print(f"✅ Strategies table accessible - {strategy_count} strategies found")

            order_count = Order.query.count()
            print(f"✅ Orders table accessible - {order_count} orders found")

            trade_count = Trade.query.count()
            print(f"✅ Trades table accessible - {trade_count} trades found")

            payment_count = Payment.query.count()
            print(f"✅ Payments table accessible - {payment_count} payments found")

            print("\n🎉 All database tests passed!")
            print("🚀 Your TradeMantra app is ready to use with MySQL!")

            return True

        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False


if __name__ == "__main__":
    if test_database_connection():
        print("\n📖 Next steps:")
        print("  1. Start your Flask app: python run.py")
        print("  2. Open browser: http://localhost:5000")
        print("  3. Login with admin/admin123 or trader/user123")
    else:
        print("\n❌ Please check your database setup and try again")
        sys.exit(1)
