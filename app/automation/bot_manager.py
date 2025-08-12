"""
Bot Manager Service
Handles persistent trading bot instances across page navigation
"""

import threading
import time
from datetime import datetime, timedelta
from flask import current_app
from ..models import TradingBotStatus, User, db
import logging

logger = logging.getLogger(__name__)


class BotManager:
    """Global bot manager to handle persistent trading bot instances"""

    _instances = {}  # {user_id: bot_instance}
    _lock = threading.Lock()

    @classmethod
    def get_bot(cls, user_id, bot_type="stock"):
        """Get or create bot instance for user"""
        with cls._lock:
            key = f"{user_id}_{bot_type}"

            if key not in cls._instances:
                # Check if bot should be running according to database
                try:
                    bot_status = TradingBotStatus.query.filter_by(
                        user_id=user_id, bot_type=bot_type
                    ).first()

                    # Create new bot instance
                    if bot_type == "crypto":
                        from ..strategies.crypto_engine import CryptoStrategyEngine

                        bot_instance = CryptoStrategyEngine(user_id=user_id)
                    else:
                        from .trading_bot import IndianStockTradingBot

                        bot_instance = IndianStockTradingBot(user_id)

                    # If database says bot should be running, restore its state
                    if bot_status and bot_status.is_running and bot_status.is_active:
                        logger.info(
                            f"Restoring running {bot_type} bot for user {user_id}"
                        )
                        try:
                            if bot_type == "crypto" and bot_status.strategies:
                                bot_instance.start_trading(
                                    user_id=user_id,
                                    strategy_names=bot_status.strategies,
                                    is_paper=True,
                                )
                            elif bot_type == "stock" and hasattr(
                                bot_instance, "start_automated_trading"
                            ):
                                bot_instance.start_automated_trading()
                        except Exception as e:
                            logger.error(f"Error restoring bot state: {e}")

                    cls._instances[key] = bot_instance
                    logger.info(
                        f"Created new {bot_type} bot instance for user {user_id}"
                    )

                except Exception as e:
                    # Fallback: create simple bot instance
                    logger.error(f"Error checking bot status from database: {e}")
                    if bot_type == "crypto":
                        from ..strategies.crypto_engine import CryptoStrategyEngine

                        bot_instance = CryptoStrategyEngine(user_id=user_id)
                    else:
                        from .trading_bot import IndianStockTradingBot

                        bot_instance = IndianStockTradingBot(user_id)

                    cls._instances[key] = bot_instance
                    logger.info(
                        f"Created fallback {bot_type} bot instance for user {user_id}"
                    )

            return cls._instances[key]

    @classmethod
    def remove_bot(cls, user_id, bot_type="stock"):
        """Remove bot instance when stopped"""
        with cls._lock:
            key = f"{user_id}_{bot_type}"
            if key in cls._instances:
                bot = cls._instances[key]
                # Ensure bot is properly stopped
                if hasattr(bot, "stop_trading"):
                    bot.stop_trading()
                del cls._instances[key]
                logger.info(f"Removed {bot_type} bot instance for user {user_id}")

    @classmethod
    def restore_active_bots(cls):
        """Restore all active bots from database on app startup"""
        try:
            with current_app.app_context():
                try:
                    # Find all active bots in database
                    active_bots = TradingBotStatus.query.filter_by(
                        is_running=True
                    ).all()

                    for bot_status in active_bots:
                        try:
                            # Check if heartbeat is recent (within 10 minutes)
                            if (
                                bot_status.last_heartbeat
                                and (
                                    datetime.utcnow() - bot_status.last_heartbeat
                                ).total_seconds()
                                < 600
                            ):

                                # Restore bot instance
                                bot = cls.get_bot(
                                    bot_status.user_id, bot_status.bot_type
                                )

                                # Restart bot with previous strategies
                                if bot_status.strategies:
                                    try:
                                        if bot_status.bot_type == "crypto":
                                            bot.start_trading(
                                                user_id=bot_status.user_id,
                                                strategy_names=bot_status.strategies,
                                                is_paper=True,  # Default to paper mode
                                            )
                                        else:
                                            # Stock bot uses start_automated_trading method
                                            bot.start_automated_trading()

                                        logger.info(
                                            f"Restored {bot_status.bot_type} bot for user {bot_status.user_id}"
                                        )
                                    except Exception as e:
                                        logger.error(
                                            f"Failed to restore bot for user {bot_status.user_id}: {e}"
                                        )
                                        # Mark as stopped in database with separate transaction
                                        try:
                                            bot_status.is_running = False
                                            bot_status.stopped_at = datetime.utcnow()
                                            db.session.commit()
                                        except Exception as db_e:
                                            logger.error(
                                                f"Failed to update bot status: {db_e}"
                                            )
                                            db.session.rollback()
                            else:
                                # Bot heartbeat is too old, mark as stopped
                                try:
                                    bot_status.is_running = False
                                    bot_status.stopped_at = datetime.utcnow()
                                    db.session.commit()
                                    logger.info(
                                        f"Marked stale bot as stopped for user {bot_status.user_id}"
                                    )
                                except Exception as db_e:
                                    logger.error(
                                        f"Failed to update stale bot status: {db_e}"
                                    )
                                    db.session.rollback()

                        except Exception as bot_e:
                            logger.error(
                                f"Error processing bot for user {bot_status.user_id if bot_status else 'unknown'}: {bot_e}"
                            )
                            # Continue with next bot instead of failing completely
                            continue

                except Exception as e:
                    logger.error(f"Error querying active bots: {e}")
                    # Ensure session is clean
                    try:
                        db.session.rollback()
                    except:
                        pass

        except Exception as e:
            logger.error(f"Critical error in restore_active_bots: {e}")
            # Don't let bot restoration failure prevent app startup

    @classmethod
    def get_active_bots(cls):
        """Get all currently active bot instances"""
        with cls._lock:
            return dict(cls._instances)

    @classmethod
    def update_bot_heartbeat(cls, user_id, bot_type="stock"):
        """Update bot heartbeat in database"""
        try:
            bot_status = TradingBotStatus.query.filter_by(
                user_id=user_id, bot_type=bot_type
            ).first()

            if bot_status:
                bot_status.last_heartbeat = datetime.utcnow()
                db.session.commit()

        except Exception as e:
            logger.error(f"Error updating bot heartbeat: {e}")


def start_heartbeat_monitor(app):
    """Start background thread to monitor bot heartbeats"""

    def heartbeat_monitor():
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds

                with app.app_context():
                    active_bots = BotManager.get_active_bots()

                    for key, bot in active_bots.items():
                        try:
                            user_id, bot_type = key.rsplit("_", 1)
                            user_id = int(user_id)

                            # Update heartbeat if bot is running
                            if hasattr(bot, "is_running") and bot.is_running:
                                BotManager.update_bot_heartbeat(user_id, bot_type)

                        except Exception as e:
                            logger.error(f"Error in heartbeat monitor for {key}: {e}")

            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")

    # Start heartbeat monitor in background thread
    monitor_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    monitor_thread.start()
    logger.info("Started bot heartbeat monitor")
