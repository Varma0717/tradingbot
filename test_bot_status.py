#!/usr/bin/env python3
"""
Test what the crypto bot's get_trading_status method returns
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.automation.bot_manager import BotManager

app = create_app()

with app.app_context():
    print("=== Testing Crypto Bot Status ===")

    # Get the crypto bot instance
    crypto_bot = BotManager.get_bot(2, bot_type="crypto")

    if crypto_bot:
        print(f"Crypto bot found: {type(crypto_bot)}")
        print(f"Is running: {getattr(crypto_bot, 'is_running', 'N/A')}")

        # Check what methods the bot has
        print(
            f"Bot methods: {[method for method in dir(crypto_bot) if not method.startswith('_')]}"
        )

        # Try to get trading status
        try:
            if hasattr(crypto_bot, "get_trading_status"):
                status = crypto_bot.get_trading_status()
                print(f"Trading status: {status}")
            else:
                print("Bot doesn't have get_trading_status method")

            # Try alternative methods
            if hasattr(crypto_bot, "get_status"):
                status = crypto_bot.get_status()
                print(f"General status: {status}")

            # Check if bot has recent activity
            if hasattr(crypto_bot, "last_execution_time"):
                print(f"Last execution: {crypto_bot.last_execution_time}")

        except Exception as e:
            print(f"Error getting status: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("No crypto bot found")

    # Also check stock bot
    stock_bot = BotManager.get_bot(2, bot_type="stock")
    if stock_bot:
        print(f"\nStock bot found: {type(stock_bot)}")
        print(f"Is running: {getattr(stock_bot, 'is_running', 'N/A')}")
    else:
        print("\nNo stock bot found")
