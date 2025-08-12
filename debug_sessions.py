#!/usr/bin/env python3
"""
Debug automation sessions - check what sessions exist and why they might not be showing
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import TradingBotStatus, Order, Trade, User

app = create_app()

with app.app_context():
    print("=== Debugging Automation Sessions ===")

    # Check users
    users = User.query.all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"  User {user.id}: {user.email}")

    print("\n=== Trading Bot Status Records ===")
    bot_statuses = TradingBotStatus.query.all()
    print(f"Total bot status records: {len(bot_statuses)}")

    for status in bot_statuses:
        print(
            f"  User {status.user_id}, Bot Type: {status.bot_type}, Running: {status.is_running}"
        )
        print(f"    Strategies: {status.strategies}")
        print(f"    Started: {status.started_at}")
        print(f"    Last Heartbeat: {status.last_heartbeat}")
        print(f"    Is Active: {status.is_active}")
        print(f"    Created: {status.created_at}")
        print(f"    Updated: {status.updated_at}")
        print()

    # Check recent orders
    print("=== Recent Orders (last 10) ===")
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    for order in recent_orders:
        print(
            f"  {order.symbol} - {order.side} - {order.status} - User {order.user_id}"
        )

    # Check recent trades
    print("\n=== Recent Trades (last 10) ===")
    recent_trades = Trade.query.order_by(Trade.timestamp.desc()).limit(10).all()
    for trade in recent_trades:
        print(
            f"  {trade.symbol} - {trade.side} - {trade.quantity} @ {trade.price} - User {trade.user_id}"
        )

    print("\n=== Analysis ===")
    user_2_bots = TradingBotStatus.query.filter_by(user_id=2).all()
    print(f"User 2 has {len(user_2_bots)} bot status records")

    running_bots = TradingBotStatus.query.filter_by(user_id=2, is_running=True).all()
    print(f"User 2 has {len(running_bots)} running bots")
