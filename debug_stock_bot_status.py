#!/usr/bin/env python3
"""
Debug script to check stock bot status and positions
"""
import sys
import os

sys.path.insert(0, os.path.abspath("."))

try:
    from app import create_app
    from app.automation.bot_manager import BotManager

    app = create_app()

    with app.app_context():
        print("🔍 Checking Stock Bot Status...")

        # Get stock bot for user 2
        stock_bot = BotManager.get_bot(2, "stock")

        print(f"Stock bot instance: {type(stock_bot).__name__}")
        print(f"Stock bot is_running: {stock_bot.is_running}")

        if hasattr(stock_bot, "get_status"):
            status = stock_bot.get_status()
            print(f"\n📊 Stock Bot Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")

            print(f"\n🎯 Positions details:")
            positions = status.get("positions", {})
            print(f"  Number of positions: {len(positions)}")

            for symbol, pos in positions.items():
                print(f"  {symbol}: {pos}")

            if not positions:
                print("  ❌ No positions found - this is why no sessions show!")
                print("  💡 Sessions API only shows bots with active positions")

        # Check current positions directly
        print(f"\n🏠 Direct position check:")
        print(f"  current_positions: {stock_bot.current_positions}")
        print(f"  strategies: {stock_bot.strategies}")
        print(f"  total_trades: {stock_bot.total_trades}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
