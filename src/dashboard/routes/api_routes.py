"""
API routes for real-time trading data from the universal strategy.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.strategies.strategy_manager import StrategyManager
from ..real_trading_integration import real_trading_integrator

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api")

# Global strategy manager instance
strategy_manager = None


class RealTradingStartRequest(BaseModel):
    investment_amount: float = 100.0


async def get_strategy_manager():
    """Get or create the strategy manager instance."""
    global strategy_manager
    if strategy_manager is None:
        strategy_manager = StrategyManager()
        await strategy_manager.initialize()
    return strategy_manager


@router.get("/status")
async def get_strategy_status():
    """Get current strategy status."""
    try:
        sm = await get_strategy_manager()
        status = sm.get_strategy_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting strategy status: {e}")
        return {"success": False, "error": str(e), "data": {"status": "error"}}


@router.get("/trades")
async def get_trades():
    """Get all trades from the universal strategy."""
    try:
        sm = await get_strategy_manager()
        trades = sm.get_trades()
        return {"success": True, "data": trades}
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.get("/real-trading/status")
async def get_real_trading_status():
    """Get real trading status."""
    try:
        status = await real_trading_integrator.get_real_trading_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting real trading status: {e}")
        return {"success": False, "error": str(e)}


@router.post("/real-trading/start")
async def start_real_trading(request: RealTradingStartRequest):
    """Start real trading with specified investment amount."""
    try:
        logger.info(f"📊 Real trading start request: ${request.investment_amount:.2f}")

        # Initialize real trading if not already done
        if not real_trading_integrator.is_real_trading:
            logger.info("🔧 Initializing real trading...")
            init_success = await real_trading_integrator.initialize_real_trading()
            if not init_success:
                return {
                    "success": False,
                    "error": "Failed to initialize real trading connection. Check your Binance API keys in the .env file.",
                }

        # Start real trading
        logger.info("🚀 Starting real trading...")
        success = await real_trading_integrator.start_real_trading(
            request.investment_amount
        )

        if success:
            return {
                "success": True,
                "message": f"Real trading started with ${request.investment_amount:.2f}",
            }
        else:
            return {
                "success": False,
                "error": "Failed to start real trading. Check logs for details.",
            }

    except Exception as e:
        logger.error(f"Error starting real trading: {e}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
        return {"success": False, "error": str(e)}


@router.post("/real-trading/stop")
async def stop_real_trading():
    """Stop real trading and cancel all orders."""
    try:
        success = await real_trading_integrator.stop_real_trading()

        if success:
            return {
                "success": True,
                "message": "Real trading stopped and all orders cancelled",
            }
        else:
            return {"success": False, "error": "Failed to stop real trading"}

    except Exception as e:
        logger.error(f"Error stopping real trading: {e}")
        return {"success": False, "error": str(e)}


@router.get("/real-trading/trades")
async def get_real_trades():
    """Get real trading history."""
    try:
        trades = real_trading_integrator.get_real_trades()
        return {"success": True, "data": trades}
    except Exception as e:
        logger.error(f"Error getting real trades: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.get("/real-trading/orders")
async def get_real_orders():
    """Get real active orders."""
    try:
        orders = real_trading_integrator.get_real_orders()
        return {"success": True, "data": orders}
    except Exception as e:
        logger.error(f"Error getting real orders: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.get("/orders")
async def get_active_orders():
    """Get active orders from the universal strategy."""
    try:
        sm = await get_strategy_manager()
        orders = sm.get_active_orders()
        return {"success": True, "data": orders}
    except Exception as e:
        logger.error(f"Error getting active orders: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.post("/start")
async def start_strategy():
    """Start the real trading strategy."""
    try:
        # Use real trading integration instead of paper trading
        from ..real_trading_integration import real_trading_integrator

        # Initialize if needed
        if not real_trading_integrator.is_initialized:
            success = real_trading_integrator.initialize()
            if not success:
                return {"success": False, "error": "Failed to initialize real trading"}

        # Start real trading
        success = real_trading_integrator.start_trading()
        return {
            "success": success,
            "message": (
                "Real trading started" if success else "Failed to start real trading"
            ),
        }
    except Exception as e:
        logger.error(f"Error starting strategy: {e}")
        return {"success": False, "error": str(e)}


@router.post("/stop")
async def stop_strategy():
    """Stop the real trading strategy."""
    try:
        # Use real trading integration instead of paper trading
        from ..real_trading_integration import real_trading_integrator

        if not real_trading_integrator.is_initialized:
            return {"success": False, "error": "Real trading not initialized"}

        # Stop real trading
        success = real_trading_integrator.stop_trading()
        return {
            "success": success,
            "message": (
                "Real trading stopped" if success else "Failed to stop real trading"
            ),
        }
    except Exception as e:
        logger.error(f"Error stopping strategy: {e}")
        return {"success": False, "error": str(e)}


@router.get("/dashboard-data")
async def get_dashboard_data():
    """Get all dashboard data in one call."""
    try:
        sm = await get_strategy_manager()
        status = sm.get_strategy_status()
        trades = sm.get_trades()
        orders = sm.get_active_orders()

        # Calculate summary stats
        total_profit = sum(trade.get("profit", 0) for trade in trades)
        win_trades = [t for t in trades if t.get("profit", 0) > 0]
        win_rate = len(win_trades) / len(trades) * 100 if trades else 0

        return {
            "success": True,
            "data": {
                "status": status,
                "trades": {
                    "total": len(trades),
                    "recent": trades[-10:] if trades else [],  # Last 10 trades
                    "total_profit": total_profit,
                    "win_rate": win_rate,
                },
                "orders": {"active": len(orders), "list": orders},
                "summary": {
                    "balance": status.get("balance", 0),
                    "profit": total_profit,
                    "trades_count": len(trades),
                    "active_orders": len(orders),
                    "win_rate": win_rate,
                    "strategy_name": status.get("strategy", "Universal Grid DCA"),
                },
            },
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
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


# Legacy API endpoints for compatibility with old dashboard.js
@router.get("/portfolio/summary")
async def get_portfolio_summary():
    """Legacy portfolio summary endpoint."""
    try:
        sm = await get_strategy_manager()
        status = sm.get_strategy_status()
        trades = sm.get_trades()

        total_profit = sum(trade.get("profit", 0) for trade in trades)

        return {
            "success": True,
            "data": {
                "total_value": status.get("balance", 0),
                "unrealized_pnl": total_profit,
                "realized_pnl": total_profit,
                "daily_change": total_profit,
                "daily_change_pct": (
                    (total_profit / status.get("balance", 1)) * 100
                    if status.get("balance", 0) > 0
                    else 0
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return {"success": False, "error": str(e), "data": {}}


@router.get("/balance")
async def get_balance():
    """Legacy balance endpoint."""
    try:
        sm = await get_strategy_manager()
        status = sm.get_strategy_status()

        return {
            "success": True,
            "data": {
                "total": status.get("balance", 0),
                "available": status.get("balance", 0)
                * 0.8,  # 80% available for trading
                "in_orders": status.get("balance", 0) * 0.2,  # 20% in orders
                "currency": "USDT",
            },
        }
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return {"success": False, "error": str(e), "data": {}}


@router.get("/portfolio/positions")
async def get_positions():
    """Legacy positions endpoint."""
    try:
        sm = await get_strategy_manager()
        orders = sm.get_active_orders()

        # Convert orders to position-like format
        positions = []
        for order in orders[:5]:  # Show first 5 as positions
            positions.append(
                {
                    "symbol": "BTC/USDT",
                    "side": order.get("type", "buy"),
                    "size": order.get("amount", 0),
                    "entry_price": order.get("price", 0),
                    "current_price": order.get("price", 0) * 1.001,  # Slight variation
                    "pnl": order.get("usd_amount", 0) * 0.01,  # 1% profit simulation
                    "pnl_pct": 1.0,
                }
            )

        return {"success": True, "data": positions}
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.get("/strategies/summary")
async def get_strategies_summary():
    """Legacy strategies summary endpoint."""
    try:
        sm = await get_strategy_manager()
        status = sm.get_strategy_status()
        trades = sm.get_trades()

        return {
            "success": True,
            "data": {
                "active_strategies": 1 if status.get("status") == "active" else 0,
                "total_strategies": 1,
                "strategies": [
                    {
                        "name": status.get("strategy", "Universal Grid DCA"),
                        "type": "grid_dca",
                        "status": status.get("status", "stopped"),
                        "profit": sum(trade.get("profit", 0) for trade in trades),
                        "trades": len(trades),
                        "win_rate": status.get("win_rate", 0),
                    }
                ],
            },
        }
    except Exception as e:
        logger.error(f"Error getting strategies summary: {e}")
        return {"success": False, "error": str(e), "data": {}}


@router.get("/trades/orders/open")
async def get_open_orders():
    """Legacy open orders endpoint."""
    try:
        sm = await get_strategy_manager()
        orders = sm.get_active_orders()

        # Convert to legacy format
        open_orders = []
        for order in orders:
            open_orders.append(
                {
                    "id": order.get("id", ""),
                    "symbol": "BTC/USDT",
                    "side": order.get("type", "buy"),
                    "type": "limit",
                    "amount": order.get("amount", 0),
                    "price": order.get("price", 0),
                    "filled": 0,
                    "remaining": order.get("amount", 0),
                    "status": "open",
                    "created_at": order.get("created", ""),
                }
            )

        return {"success": True, "data": open_orders}
    except Exception as e:
        logger.error(f"Error getting open orders: {e}")
        return {"success": False, "error": str(e), "data": []}
