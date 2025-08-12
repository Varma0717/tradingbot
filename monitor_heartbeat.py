#!/usr/bin/env python3
"""
Real-time monitoring of bot heartbeat status
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import TradingBotStatus

app = create_app()

with app.app_context():
    print("=== Real-time Bot Heartbeat Monitor ===")
    print("Monitoring crypto bot status every 10 seconds...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            crypto_status = TradingBotStatus.query.filter_by(
                user_id=2, bot_type="crypto"
            ).first()

            if crypto_status:
                now = datetime.utcnow()
                heartbeat_age = (
                    (now - crypto_status.last_heartbeat).total_seconds()
                    if crypto_status.last_heartbeat
                    else None
                )

                print(f"\n[{now.strftime('%H:%M:%S')}] Crypto Bot Status:")
                print(f"  Running: {crypto_status.is_running}")
                print(f"  Last Heartbeat: {crypto_status.last_heartbeat}")
                print(
                    f"  Heartbeat Age: {heartbeat_age:.0f} seconds"
                    if heartbeat_age
                    else "  Heartbeat Age: N/A"
                )
                print(f"  Is Active: {crypto_status.is_active}")
                print(f"  Updated: {crypto_status.updated_at}")
            else:
                print(
                    f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] No crypto bot status found"
                )

            time.sleep(10)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
