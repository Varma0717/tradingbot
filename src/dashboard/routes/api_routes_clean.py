"""
New API routes with proper trading mode separation.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import time
from ...core.trading_mode_manager import trading_mode_manager, TradingMode

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api")

# Rate limiting for start requests
_last_start_request = 0
_start_request_cooldown = 5  # 5 seconds cooldown between start requests


class TradingModeRequest(BaseModel):
    mode: str  # "paper" or "real"


class TradingStartRequest(BaseModel):
    investment_amount: Optional[float] = 100.0


@router.get("/mode")
async def get_trading_mode():
    """Get current trading mode and status."""
    try:
        status = trading_mode_manager.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting trading mode: {e}")
        return {"success": False, "error": str(e)}


@router.post("/mode/switch")
async def switch_trading_mode(request: TradingModeRequest):
    """Switch between paper and real trading modes."""
    try:
        if request.mode not in ["paper", "real"]:
            return {"success": False, "error": "Invalid mode. Use 'paper' or 'real'"}

        if request.mode == "paper":
            success = trading_mode_manager.switch_to_paper()
            message = (
                "Switched to paper trading mode"
                if success
                else "Failed to switch to paper trading"
            )
        else:
            success = trading_mode_manager.switch_to_real()
            message = (
                "Switched to real trading mode"
                if success
                else "Failed to switch to real trading"
            )

        return {
            "success": success,
            "message": message,
            "current_mode": trading_mode_manager.current_mode.value,
        }
    except Exception as e:
        logger.error(f"Error switching trading mode: {e}")
        return {"success": False, "error": str(e)}


@router.get("/status")
async def get_strategy_status():
    """Get current strategy status based on active mode."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": False, "error": "No strategy manager available"}

        status = manager.get_status() if hasattr(manager, "get_status") else {}

        # Add mode information
        status.update(
            {
                "trading_mode": trading_mode_manager.current_mode.value,
                "is_paper_trading": trading_mode_manager.is_paper_trading,
                "is_real_trading": trading_mode_manager.is_real_trading,
            }
        )

        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting strategy status: {e}")
        return {"success": False, "error": str(e), "data": {"status": "error"}}


@router.get("/balance")
async def get_balance():
    """Get balance based on current trading mode."""
    try:
        balance = trading_mode_manager.get_balance()
        return {
            "success": True,
            "data": {
                "total": balance,
                "available": balance * 0.8,
                "in_orders": balance * 0.2,
                "currency": "USDT",
                "mode": trading_mode_manager.current_mode.value,
                "is_paper": trading_mode_manager.is_paper_trading,
            },
        }
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return {"success": False, "error": str(e)}


@router.post("/start")
async def start_strategy(request: Optional[TradingStartRequest] = None):
    """Start trading strategy based on current mode."""
    try:
        global _last_start_request
        current_time = time.time()

        # Rate limiting: prevent rapid successive start requests
        if current_time - _last_start_request < _start_request_cooldown:
            remaining_time = _start_request_cooldown - (
                current_time - _last_start_request
            )
            logger.warning(
                f"Start request rate limited. Try again in {remaining_time:.1f} seconds"
            )
            return {
                "success": False,
                "error": f"Please wait {remaining_time:.1f} seconds before trying again",
                "rate_limited": True,
            }

        _last_start_request = current_time

        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": False, "error": "No strategy manager available"}

        # Start trading
        if hasattr(manager, "start_trading"):
            success = manager.start_trading()
        else:
            success = False

        mode = trading_mode_manager.current_mode.value
        message = (
            f"{'Real' if trading_mode_manager.is_real_trading else 'Paper'} trading started"
            if success
            else f"Failed to start {mode} trading"
        )

        return {"success": success, "message": message, "mode": mode}
    except Exception as e:
        logger.error(f"Error starting strategy: {e}")
        return {"success": False, "error": str(e)}


@router.post("/stop")
async def stop_strategy():
    """Stop trading strategy based on current mode."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": False, "error": "No strategy manager available"}

        # Stop trading
        if hasattr(manager, "stop_trading"):
            success = manager.stop_trading()
        else:
            success = False

        mode = trading_mode_manager.current_mode.value
        message = (
            f"{'Real' if trading_mode_manager.is_real_trading else 'Paper'} trading stopped"
            if success
            else f"Failed to stop {mode} trading"
        )

        return {"success": success, "message": message, "mode": mode}
    except Exception as e:
        logger.error(f"Error stopping strategy: {e}")
        return {"success": False, "error": str(e)}


@router.post("/restart")
async def restart_strategy():
    """Restart trading strategy (stop all orders and start fresh)"""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": False, "error": "No strategy manager available"}

        # Restart trading with fresh setup
        if hasattr(manager, "restart_trading"):
            success = manager.restart_trading()
        else:
            # Fallback: stop then start
            if hasattr(manager, "stop_trading"):
                manager.stop_trading()
            if hasattr(manager, "start_trading"):
                success = manager.start_trading()
            else:
                success = False

        mode = trading_mode_manager.current_mode.value
        message = (
            f"{'Real' if trading_mode_manager.is_real_trading else 'Paper'} trading restarted"
            if success
            else f"Failed to restart {mode} trading"
        )

        return {"success": success, "message": message, "mode": mode}
    except Exception as e:
        logger.error(f"Error restarting strategy: {e}")
        return {"success": False, "error": str(e)}


@router.get("/trades")
async def get_trades():
    """Get trades based on current mode."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": True, "data": []}

        trades = manager.get_trades() if hasattr(manager, "get_trades") else []
        return {
            "success": True,
            "data": trades,
            "mode": trading_mode_manager.current_mode.value,
        }
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.get("/orders")
async def get_active_orders():
    """Get active orders based on current mode."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": True, "data": []}

        orders = (
            manager.get_active_orders() if hasattr(manager, "get_active_orders") else []
        )
        return {
            "success": True,
            "data": orders,
            "mode": trading_mode_manager.current_mode.value,
        }
    except Exception as e:
        logger.error(f"Error getting active orders: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.post("/orders/cancel")
async def cancel_order(request_data: dict):
    """Cancel a specific order."""
    try:
        order_id = request_data.get("order_id")
        if not order_id:
            return {"success": False, "error": "order_id is required"}

        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": False, "error": "No active strategy manager"}

        # For real trading, cancel through the strategy manager
        if trading_mode_manager.is_real_trading:
            # Try to get any strategy to cancel the order
            for strategy in manager.strategies.values():
                if hasattr(strategy, "exchange"):
                    # Get all active orders to find the symbol for this order
                    try:
                        all_orders = strategy.exchange.client.get_open_orders()
                        order_to_cancel = None

                        for order in all_orders:
                            if str(order["orderId"]) == str(order_id):
                                order_to_cancel = order
                                break

                        if order_to_cancel:
                            symbol = order_to_cancel["symbol"]
                            # Cancel the order through Binance
                            result = strategy.exchange.cancel_order(symbol, order_id)
                            if result["success"]:
                                # Remove from strategy tracking if it exists
                                if hasattr(strategy, "open_orders"):
                                    strategy.open_orders.pop(str(order_id), None)
                                logger.info(f"Order {order_id} cancelled successfully")
                                return {
                                    "success": True,
                                    "message": f"Order {order_id} cancelled",
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": result.get(
                                        "error", "Failed to cancel order"
                                    ),
                                }
                    except Exception as e:
                        logger.error(f"Error cancelling order {order_id}: {e}")
                        continue

            return {"success": False, "error": "Order not found or already cancelled"}
        else:
            # For paper trading, cancel through the manager
            if hasattr(manager, "cancel_order"):
                result = manager.cancel_order(order_id)
                return {
                    "success": result,
                    "message": (
                        f"Order {order_id} cancelled"
                        if result
                        else "Failed to cancel order"
                    ),
                }
            else:
                return {
                    "success": False,
                    "error": "Cancel order not supported for this mode",
                }

    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        return {"success": False, "error": str(e)}


@router.post("/orders/cancel-all")
async def cancel_all_orders():
    """Cancel all open orders."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {"success": False, "error": "No active strategy manager"}

        cancelled_count = 0

        if trading_mode_manager.is_real_trading:
            # For real trading, cancel all orders through strategies
            for strategy in manager.strategies.values():
                if hasattr(strategy, "open_orders"):
                    for order_id in list(strategy.open_orders.keys()):
                        try:
                            result = strategy.exchange.cancel_order(
                                strategy.trading_pair, order_id
                            )
                            if result["success"]:
                                strategy.open_orders.pop(order_id, None)
                                cancelled_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to cancel order {order_id}: {e}")
        else:
            # For paper trading
            if hasattr(manager, "cancel_all_orders"):
                cancelled_count = manager.cancel_all_orders()

        return {"success": True, "message": f"Cancelled {cancelled_count} orders"}

    except Exception as e:
        logger.error(f"Error cancelling all orders: {e}")
        return {"success": False, "error": str(e)}


@router.get("/analytics")
async def get_analytics():
    """Get trading analytics including win rate, profit/loss, etc."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        if not manager:
            return {
                "success": True,
                "data": {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "total_profit": 0.0,
                    "total_volume": 0.0,
                    "average_profit_per_trade": 0.0,
                    "active_orders_count": 0,
                },
            }

        # Get analytics from strategy manager
        analytics = manager.get_analytics() if hasattr(manager, "get_analytics") else {}

        return {
            "success": True,
            "data": analytics,
            "mode": trading_mode_manager.current_mode.value,
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return {"success": False, "error": str(e), "data": {}}


@router.get("/dashboard-data")
async def get_dashboard_data():
    """Get comprehensive dashboard data based on current mode."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        mode_status = trading_mode_manager.get_status()
        current_balance = trading_mode_manager.get_balance()

        # Update simulation for paper trading
        if (
            trading_mode_manager.is_paper_trading
            and manager
            and hasattr(manager, "update_simulation")
        ):
            manager.update_simulation()

        # Get data from active manager
        if manager:
            status = manager.get_status() if hasattr(manager, "get_status") else {}
            trades = manager.get_trades() if hasattr(manager, "get_trades") else []
            orders = (
                manager.get_active_orders()
                if hasattr(manager, "get_active_orders")
                else []
            )

            # Ensure data types are correct
            if not isinstance(trades, list):
                logger.warning(f"API: trades is not a list, got {type(trades)}")
                trades = []
            if not isinstance(orders, list):
                logger.warning(f"API: orders is not a list, got {type(orders)}")
                orders = []
        else:
            status = {}
            trades = []
            orders = []

        # For real trading, try to get real data (but reduce frequency)
        if trading_mode_manager.is_real_trading and hasattr(manager, "get_real_trades"):
            trades = manager.get_real_trades()
            orders = (
                manager.get_real_orders() if hasattr(manager, "get_real_orders") else []
            )

        # Calculate summary stats
        total_profit = sum(trade.get("profit", 0) for trade in trades)
        win_trades = [t for t in trades if t.get("profit", 0) > 0]
        win_rate = len(win_trades) / len(trades) * 100 if trades else 0

        # Ensure balance is correctly set
        mode_status["balance"] = current_balance
        status["balance"] = current_balance
        status["total_balance"] = current_balance

        return {
            "success": True,
            "data": {
                "mode": mode_status,
                "status": status,
                "balance": current_balance,
                "trades": {
                    "total": len(trades),
                    "recent": trades[-10:] if trades else [],
                    "total_profit": total_profit,
                    "win_rate": win_rate,
                },
                "orders": {"active": len(orders), "list": orders},
                "summary": {
                    "balance": current_balance,
                    "profit": total_profit,
                    "trades_count": len(trades),
                    "active_orders": len(orders),
                    "win_rate": win_rate,
                    "strategy_name": f"Grid DCA ({mode_status.get('mode', 'unknown')} mode)",
                },
            },
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "mode": {"mode": "error"},
                "status": {"status": "error"},
                "trades": {"total": 0, "recent": [], "total_profit": 0, "win_rate": 0},
                "orders": {"active": 0, "list": []},
                "summary": {
                    "balance": 0,
                    "profit": 0,
                    "trades_count": 0,
                    "active_orders": 0,
                    "win_rate": 0,
                },
            },
        }


@router.get("/real-trading/status")
async def get_real_trading_status():
    """Get real trading status and availability."""
    try:
        # Check if we're in real trading mode
        is_real_trading = trading_mode_manager.is_real_trading
        current_mode = trading_mode_manager.current_mode.value

        # Get real trading manager if available
        real_manager = None
        if hasattr(trading_mode_manager, "real_strategy_manager"):
            real_manager = trading_mode_manager.real_strategy_manager

        # Check if real trading is properly configured
        real_trading_available = False
        configuration_status = "Not configured"

        try:
            # Basic check for real trading availability
            if real_manager:
                real_trading_available = True
                configuration_status = "Configured"
            else:
                configuration_status = "Real trading manager not available"
        except Exception as e:
            configuration_status = f"Configuration error: {str(e)}"

        return {
            "success": True,
            "data": {
                "available": real_trading_available,
                "active": is_real_trading,
                "current_mode": current_mode,
                "configuration_status": configuration_status,
                "can_switch_to_real": real_trading_available,
            },
        }
    except Exception as e:
        logger.error(f"Error getting real trading status: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "available": False,
                "active": False,
                "current_mode": "unknown",
                "configuration_status": "Error checking status",
                "can_switch_to_real": False,
            },
        }


# Legacy endpoints for dashboard compatibility
@router.get("/portfolio/summary")
async def get_portfolio_summary():
    """Portfolio summary for dashboard."""
    try:
        balance = trading_mode_manager.get_balance()
        manager = trading_mode_manager.get_active_strategy_manager()
        trades = (
            manager.get_trades() if manager and hasattr(manager, "get_trades") else []
        )

        total_profit = sum(trade.get("profit", 0) for trade in trades)

        return {
            "success": True,
            "data": {
                "total_value": balance,
                "unrealized_pnl": total_profit,
                "realized_pnl": total_profit,
                "daily_change": total_profit,
                "daily_change_pct": (
                    (total_profit / balance * 100) if balance > 0 else 0
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return {"success": False, "error": str(e), "data": {}}


@router.post("/settings/save")
async def save_settings(settings: dict):
    """Save bot settings."""
    try:
        logger.info(f"Settings received: {settings}")

        # Map settings page fields to strategy manager settings
        strategy_settings = {}

        # Handle trading pair
        if "trading_pair" in settings:
            trading_pair = settings["trading_pair"].upper()
            if trading_pair.endswith("USDT"):
                strategy_settings["trading_pair"] = trading_pair
                logger.info(f"✅ Updated trading pair: {trading_pair}")
            else:
                logger.warning(f"Invalid trading pair: {settings['trading_pair']}")

        # Handle order size
        if "order_size" in settings:
            try:
                order_size = float(settings["order_size"])
                if 1 <= order_size <= 1000:
                    strategy_settings["order_size"] = order_size
                    logger.info(f"✅ Updated order size: ${order_size}")
                else:
                    logger.warning(f"Order size out of range: {order_size}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid order size: {settings['order_size']}")

        # Handle grid levels
        if "grid_levels" in settings:
            try:
                grid_levels = int(settings["grid_levels"])
                if 1 <= grid_levels <= 20:
                    strategy_settings["grid_levels"] = grid_levels
                    logger.info(f"✅ Updated grid levels: {grid_levels}")
                else:
                    logger.warning(f"Grid levels out of range: {grid_levels}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid grid levels: {settings['grid_levels']}")

        # Handle grid spacing
        if "grid_spacing" in settings:
            try:
                grid_spacing = float(settings["grid_spacing"])
                if 0.1 <= grid_spacing <= 10.0:
                    strategy_settings["grid_spacing"] = grid_spacing / 100.0  # Convert percentage to decimal
                    logger.info(f"✅ Updated grid spacing: {grid_spacing}%")
                else:
                    logger.warning(f"Grid spacing out of range: {grid_spacing}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid grid spacing: {settings['grid_spacing']}")

        # Handle max open orders
        if "max_open_orders" in settings:
            try:
                max_orders = int(settings["max_open_orders"])
                if 1 <= max_orders <= 50:
                    strategy_settings["max_open_orders"] = max_orders
                    logger.info(f"✅ Updated max open orders: {max_orders}")
                else:
                    logger.warning(f"Max open orders out of range: {max_orders}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid max open orders: {settings['max_open_orders']}")

        # Handle take profit
        if "take_profit" in settings:
            try:
                take_profit = float(settings["take_profit"])
                if 0.1 <= take_profit <= 10.0:
                    strategy_settings["take_profit"] = take_profit / 100.0
                    logger.info(f"✅ Updated take profit: {take_profit}%")
            except (ValueError, TypeError):
                logger.warning(f"Invalid take profit: {settings['take_profit']}")

        # Handle stop loss
        if "stop_loss" in settings:
            try:
                stop_loss = float(settings["stop_loss"])
                if 1.0 <= stop_loss <= 20.0:
                    strategy_settings["stop_loss"] = stop_loss / 100.0
                    logger.info(f"✅ Updated stop loss: {stop_loss}%")
            except (ValueError, TypeError):
                logger.warning(f"Invalid stop loss: {settings['stop_loss']}")

        # Handle boolean settings
        boolean_settings = {
            "auto_restart": "auto_restart",
            "enable_notifications": "enable_notifications"
        }
        
        for key, setting_key in boolean_settings.items():
            if key in settings:
                strategy_settings[setting_key] = settings[key] in ["true", True, 1, "1"]
                logger.info(f"✅ Updated {setting_key}: {strategy_settings[setting_key]}")

        # Update strategy manager settings if we have any valid settings
        if strategy_settings:
            logger.info(f"Updating strategy settings: {strategy_settings}")

            # Get current strategy manager and update settings
            manager = trading_mode_manager.get_active_strategy_manager()
            if manager and hasattr(manager, "update_settings"):
                manager.update_settings(strategy_settings)
                logger.info("Strategy settings updated successfully")
                
                # If trading pair changed, also update the real strategy
                if "trading_pair" in strategy_settings:
                    real_strategy = manager.get_real_strategy()
                    if real_strategy and hasattr(real_strategy, "set_trading_pair"):
                        real_strategy.set_trading_pair(strategy_settings["trading_pair"])
                        logger.info(f"Real strategy trading pair updated to: {strategy_settings['trading_pair']}")
                    
            else:
                logger.warning("No active strategy manager or update_settings method not available")

        return {
            "success": True,
            "message": f"Settings saved successfully! Updated: {', '.join(strategy_settings.keys())}",
            "settings_saved": list(strategy_settings.keys()),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return {"success": False, "error": str(e)}

