#!/usr/bin/env python3
"""
Script to update user trading mode to 'live' so they can see real Binance data
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import UserPreferences

app = create_app()

with app.app_context():
    print("=== Updating User Trading Mode to LIVE ===")

    # Find user 2 (the test user)
    preferences = UserPreferences.query.filter_by(user_id=2).first()

    if not preferences:
        print("Creating new preferences for user 2...")
        preferences = UserPreferences(
            user_id=2,
            trading_mode="live",
            default_exchange_type="crypto",
            theme="dark",
        )
        db.session.add(preferences)
    else:
        print(f"Found existing preferences: {preferences.trading_mode}")
        preferences.trading_mode = "live"
        preferences.default_exchange_type = "crypto"  # Since they have Binance

    db.session.commit()

    print(f"✅ Updated user 2 trading mode to: {preferences.trading_mode}")
    print(f"✅ Updated default exchange type to: {preferences.default_exchange_type}")
    print("\nNow the portfolio will request live mode and show real Binance data!")
