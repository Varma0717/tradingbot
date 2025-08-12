"""
System Status Dashboard
Comprehensive overview of trading system health, connections, and operations.
"""

from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required, current_user
from ..utils.subscription_enforcer import SubscriptionEnforcer, get_plan_summary
from ..utils.portfolio_manager import PortfolioManager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

status = Blueprint("status", __name__)


@status.route("/system-health")
@login_required
def system_health():
    """Comprehensive system health dashboard"""

    try:
        # Get user plan and features
        plan_summary = get_plan_summary(current_user.id)

        # Check exchange connections
        exchange_status = _check_exchange_connections()

        # Check trading bot status
        bot_status = _check_trading_bot_status()

        # Check subscription status
        subscription_status = _check_subscription_status()

        # System performance metrics
        performance_metrics = _get_performance_metrics()

        return render_template(
            "user/system_health.html",
            title="System Health",
            plan_summary=plan_summary,
            exchange_status=exchange_status,
            bot_status=bot_status,
            subscription_status=subscription_status,
            performance_metrics=performance_metrics,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"System health dashboard error: {e}")
        return render_template(
            "user/system_health.html",
            title="System Health",
            error="Unable to load system status",
            timestamp=datetime.now(),
        )


@status.route("/api/system-status")
@login_required
def api_system_status():
    """JSON API for real-time system status"""

    try:
        status_data = {
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat(),
            "exchanges": _check_exchange_connections(),
            "trading_bots": _check_trading_bot_status(),
            "subscription": _check_subscription_status(),
            "performance": _get_performance_metrics(),
            "alerts": _get_system_alerts(),
        }

        return jsonify({"success": True, "status": status_data})

    except Exception as e:
        logger.error(f"System status API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def _check_exchange_connections():
    """Check status of all exchange connections"""

    try:
        from ..models import ExchangeConnection

        connections = ExchangeConnection.query.filter_by(user_id=current_user.id).all()

        exchange_status = {
            "total_connections": len(connections),
            "active_connections": 0,
            "failed_connections": 0,
            "details": [],
        }

        for conn in connections:
            try:
                # Test connection
                adapter = _get_adapter_for_connection(conn)

                if adapter and adapter.is_connected:
                    status = "connected"
                    exchange_status["active_connections"] += 1

                    # Get additional info
                    try:
                        account_info = adapter.get_account_info()
                        balances = adapter.get_balances()

                        connection_detail = {
                            "name": conn.get_display_name(),
                            "exchange": conn.exchange_name,
                            "status": status,
                            "account_id": account_info.get("user_id", "N/A"),
                            "balance_count": len(balances),
                            "last_checked": datetime.now().isoformat(),
                        }
                    except Exception as e:
                        connection_detail = {
                            "name": conn.get_display_name(),
                            "exchange": conn.exchange_name,
                            "status": "connected_with_errors",
                            "error": str(e),
                            "last_checked": datetime.now().isoformat(),
                        }
                else:
                    status = "disconnected"
                    exchange_status["failed_connections"] += 1
                    connection_detail = {
                        "name": conn.get_display_name(),
                        "exchange": conn.exchange_name,
                        "status": status,
                        "error": "Connection failed",
                        "last_checked": datetime.now().isoformat(),
                    }

                exchange_status["details"].append(connection_detail)

            except Exception as e:
                exchange_status["failed_connections"] += 1
                exchange_status["details"].append(
                    {
                        "name": conn.get_display_name(),
                        "exchange": conn.exchange_name,
                        "status": "error",
                        "error": str(e),
                        "last_checked": datetime.now().isoformat(),
                    }
                )

        return exchange_status

    except Exception as e:
        logger.error(f"Failed to check exchange connections: {e}")
        return {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "details": [],
            "error": str(e),
        }


def _check_trading_bot_status():
    """Check status of trading bots"""

    try:
        from ..models import TradingBotStatus

        bot_statuses = TradingBotStatus.query.filter_by(user_id=current_user.id).all()

        bot_status = {
            "total_bots": len(bot_statuses),
            "active_bots": 0,
            "inactive_bots": 0,
            "error_bots": 0,
            "details": [],
        }

        for bot in bot_statuses:
            try:
                bot_detail = {
                    "id": bot.id,
                    "exchange": bot.exchange,
                    "status": bot.status,
                    "strategies_active": bot.strategies_active,
                    "total_trades": bot.total_trades,
                    "daily_pnl": float(bot.daily_pnl),
                    "last_updated": (
                        bot.last_updated.isoformat() if bot.last_updated else None
                    ),
                    "uptime": _calculate_uptime(bot.created_at),
                    "health_score": _calculate_bot_health_score(bot),
                }

                if bot.status == "RUNNING":
                    bot_status["active_bots"] += 1
                elif bot.status in ["ERROR", "FAILED"]:
                    bot_status["error_bots"] += 1
                else:
                    bot_status["inactive_bots"] += 1

                bot_status["details"].append(bot_detail)

            except Exception as e:
                logger.error(f"Error processing bot {bot.id}: {e}")
                bot_status["error_bots"] += 1
                bot_status["details"].append(
                    {"id": bot.id, "status": "error", "error": str(e)}
                )

        return bot_status

    except Exception as e:
        logger.error(f"Failed to check trading bot status: {e}")
        return {
            "total_bots": 0,
            "active_bots": 0,
            "inactive_bots": 0,
            "error_bots": 0,
            "details": [],
            "error": str(e),
        }


def _check_subscription_status():
    """Check subscription and billing status"""

    try:
        plan_info = SubscriptionEnforcer.get_user_plan_info(current_user.id)
        limits = SubscriptionEnforcer.get_daily_limits(current_user.id)
        current_usage = {
            "orders_today": SubscriptionEnforcer.get_daily_order_count(current_user.id)
        }

        subscription_status = {
            "plan": plan_info["plan"],
            "active": plan_info["active"],
            "trading_mode": plan_info["trading_mode"],
            "days_remaining": plan_info.get("days_remaining"),
            "limits": limits,
            "current_usage": current_usage,
            "usage_percentage": {
                "orders": (current_usage["orders_today"] / limits["max_orders_per_day"])
                * 100
            },
        }

        # Add alerts for high usage or expiring subscription
        subscription_status["alerts"] = []

        if subscription_status["usage_percentage"]["orders"] > 80:
            subscription_status["alerts"].append(
                {
                    "type": "warning",
                    "message": f"Daily order limit {subscription_status['usage_percentage']['orders']:.0f}% used",
                }
            )

        if plan_info.get("days_remaining") and plan_info["days_remaining"] <= 7:
            subscription_status["alerts"].append(
                {
                    "type": "warning",
                    "message": f"Subscription expires in {plan_info['days_remaining']} days",
                }
            )

        return subscription_status

    except Exception as e:
        logger.error(f"Failed to check subscription status: {e}")
        return {"plan": "unknown", "active": False, "error": str(e)}


def _get_performance_metrics():
    """Get system performance metrics"""

    try:
        # Database performance
        db_metrics = _get_database_metrics()

        # Application performance
        app_metrics = _get_application_metrics()

        return {
            "database": db_metrics,
            "application": app_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return {
            "database": {"status": "unknown"},
            "application": {"status": "unknown"},
            "error": str(e),
        }


def _get_database_metrics():
    """Get database performance metrics"""

    try:
        from .. import db
        from ..models import Order, User, TradingBotStatus

        # Basic counts
        total_users = User.query.count()
        total_orders = Order.query.count()
        active_bots = TradingBotStatus.query.filter_by(status="RUNNING").count()

        # Recent activity
        recent_orders = Order.query.filter(
            Order.created_at >= datetime.now() - timedelta(hours=24)
        ).count()

        return {
            "status": "healthy",
            "total_users": total_users,
            "total_orders": total_orders,
            "active_bots": active_bots,
            "recent_orders_24h": recent_orders,
            "connection_pool": "active",
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


def _get_application_metrics():
    """Get application performance metrics"""

    import psutil
    import os

    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()

        return {
            "status": "healthy",
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "process_memory_mb": process_memory.rss / 1024 / 1024,
            "uptime_hours": (
                datetime.now() - datetime.fromtimestamp(process.create_time())
            ).total_seconds()
            / 3600,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


def _get_system_alerts():
    """Get system-wide alerts and warnings"""

    alerts = []

    try:
        # Check for recent errors in logs
        # This would typically read from log files or error tracking system

        # Check for maintenance windows
        # This would check scheduled maintenance

        # Check for performance issues
        perf_metrics = _get_performance_metrics()

        if perf_metrics["application"].get("cpu_usage", 0) > 80:
            alerts.append(
                {
                    "type": "warning",
                    "category": "performance",
                    "message": f"High CPU usage: {perf_metrics['application']['cpu_usage']:.1f}%",
                }
            )

        if perf_metrics["application"].get("memory_usage", 0) > 80:
            alerts.append(
                {
                    "type": "warning",
                    "category": "performance",
                    "message": f"High memory usage: {perf_metrics['application']['memory_usage']:.1f}%",
                }
            )

        return alerts

    except Exception as e:
        return [
            {
                "type": "error",
                "category": "system",
                "message": f"Failed to check system alerts: {e}",
            }
        ]


def _get_adapter_for_connection(connection):
    """Get appropriate adapter for exchange connection"""

    try:
        if connection.exchange_name in ["zerodha", "upstox", "angelbroking"]:
            from ..exchange_adapter.kite_adapter import ZerodhaKiteAdapter

            return ZerodhaKiteAdapter(current_user.id, paper_trading=False)
        elif connection.exchange_name in ["binance", "binance_testnet"]:
            from ..exchange_adapter.binance_adapter import BinanceAdapter

            return BinanceAdapter(current_user.id, force_paper_mode=False)
        else:
            return None

    except Exception as e:
        logger.error(f"Failed to get adapter for {connection.exchange_name}: {e}")
        return None


def _calculate_uptime(start_time):
    """Calculate uptime in human readable format"""

    if not start_time:
        return "Unknown"

    try:
        uptime_delta = datetime.now() - start_time
        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    except Exception:
        return "Unknown"


def _calculate_bot_health_score(bot):
    """Calculate a health score for trading bot (0-100)"""

    try:
        score = 100

        # Deduct points for various issues
        if bot.status != "RUNNING":
            score -= 50

        if (
            bot.last_updated and (datetime.now() - bot.last_updated).seconds > 300
        ):  # 5 minutes
            score -= 20

        if bot.daily_pnl < -1000:  # Large loss
            score -= 10

        if bot.strategies_active == 0:
            score -= 15

        return max(0, score)

    except Exception:
        return 0
