import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Trade, Order, User

# Create app and setup database context
app = create_app()

with app.app_context():
    try:
        # Query all trades for user 2 (the test user)
        user_id = 2
        trades = (
            Trade.query.filter_by(user_id=user_id)
            .order_by(Trade.timestamp.desc())
            .limit(20)
            .all()
        )

        print(f"Found {len(trades)} trades for user {user_id}:")
        print("-" * 80)

        for trade in trades:
            print(f"Trade ID: {trade.id}")
            print(f"  Order ID: {trade.order_id}")
            print(f"  Symbol: {trade.symbol}")
            print(f"  Exchange Type: {trade.exchange_type}")
            print(f"  Side: {trade.side}")
            print(f"  Quantity: {trade.quantity}")
            print(f"  Price: {trade.price}")
            print(f"  Fees: {trade.fees}")
            print(f"  Timestamp: {trade.timestamp}")
            print("-" * 40)

        # Also check orders
        orders = (
            Order.query.filter_by(user_id=user_id)
            .order_by(Order.created_at.desc())
            .limit(20)
            .all()
        )

        print(f"\nFound {len(orders)} orders for user {user_id}:")
        print("-" * 80)

        for order in orders:
            print(f"Order ID: {order.id}")
            print(f"  Symbol: {order.symbol}")
            print(f"  Exchange Type: {order.exchange_type}")
            print(f"  Side: {order.side}")
            print(f"  Quantity: {order.quantity}")
            print(f"  Status: {order.status}")
            print(f"  Price: {order.price}")
            print(f"  Filled Price: {order.filled_price}")
            print(f"  Filled Quantity: {order.filled_quantity}")
            print(f"  Is Paper: {order.is_paper}")
            print(f"  Created: {order.created_at}")
            print("-" * 40)

    except Exception as e:
        print(f"Error: {e}")
