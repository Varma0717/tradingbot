"""
New API routes with proper trading mode separation.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...core.trading_mode_manager import trading_mode_manager, TradingMode

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api")


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


@router.get("/dashboard-data")
async def get_dashboard_data():
    """Get comprehensive dashboard data based on current mode."""
    try:
        manager = trading_mode_manager.get_active_strategy_manager()
        mode_status = trading_mode_manager.get_status()
        current_balance = trading_mode_manager.get_balance()

        # Get data from active manager
        if manager:
            status = manager.get_status() if hasattr(manager, "get_status") else {}
            trades = manager.get_trades() if hasattr(manager, "get_trades") else []
            orders = (
                manager.get_active_orders()
                if hasattr(manager, "get_active_orders")
                else []
            )
        else:
            status = {}
            trades = []
            orders = []

        # For real trading, try to get real data
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
