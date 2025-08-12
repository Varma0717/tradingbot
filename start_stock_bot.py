#!/usr/bin/env python3
"""
Script to manually start stock bot and test sessions
"""
import sys
import os

sys.path.insert(0, os.path.abspath("."))

try:
    from app import create_app
    from app.automation.bot_manager import BotManager

    app = create_app()

    with app.app_context():
        print("🔍 Manually starting stock bot...")

        # Get stock bot for user 2
        stock_bot = BotManager.get_bot(2, "stock")
        print(f"Stock bot instance: {type(stock_bot).__name__}")
        print(f"Stock bot running status: {stock_bot.is_running}")

        # Try to start it
        if not stock_bot.is_running:
            print("Starting stock bot...")
            result = stock_bot.start_automated_trading()
            print(f"Start result: {result}")

            # Check status after starting
            print(f"Stock bot running status after start: {stock_bot.is_running}")
            status = stock_bot.get_status()
            print(f"Stock bot status: {status}")
        else:
            print("Stock bot is already running")
            status = stock_bot.get_status()
            print(f"Stock bot status: {status}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
