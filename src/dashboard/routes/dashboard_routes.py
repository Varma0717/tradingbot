"""Dashboard routes for the trading bot web interface with proper mode management."""

import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import trading mode manager
from ...core.trading_mode_manager import trading_mode_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Dashboard is running"}


@router.get("/", response_class=HTMLResponse)
async def dashboard_root(request: Request):
    """Root dashboard route - redirects to main dashboard."""
    return await dashboard_home(request)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_main(request: Request):
    """Main dashboard page."""
    return await dashboard_home(request)


async def dashboard_home(request: Request, templates_obj=None, trading_bot=None):
    """Main dashboard home page with proper mode management."""
    try:
        logger.info("Loading dashboard with proper trading mode management")

        # Use passed templates object if available, otherwise use module-level
        template_engine = templates_obj if templates_obj else templates

        # Get current trading mode status
        mode_status = trading_mode_manager.get_status()

        # Get active strategy manager based on current mode
        manager = trading_mode_manager.get_active_strategy_manager()

        # Initialize default values
        trades = []
        orders = []
        status = {}
        balance = mode_status.get("balance", 0)

        # Get data from active manager
        if manager:
            try:
                if hasattr(manager, "get_status"):
                    status = manager.get_status()
                if hasattr(manager, "get_trades"):
                    trades = manager.get_trades()
                    # Ensure trades is a list
                    if not isinstance(trades, list):
                        logger.warning(
                            f"trades is not a list, got {type(trades)}: {trades}"
                        )
                        trades = []
                if hasattr(manager, "get_active_orders"):
                    orders = manager.get_active_orders()
                    # Ensure orders is a list
                    if not isinstance(orders, list):
                        logger.warning(
                            f"orders is not a list, got {type(orders)}: {orders}"
                        )
                        orders = []
            except Exception as e:
                logger.error(f"Error getting data from manager: {e}")
                trades = []
                orders = []

        # Calculate metrics
        try:
            total_profit = sum(
                trade.get("profit", 0) for trade in trades if isinstance(trade, dict)
            )
            win_trades = [
                t for t in trades if isinstance(t, dict) and t.get("profit", 0) > 0
            ]
            win_rate = len(win_trades) / len(trades) * 100 if trades else 0
        except Exception as e:
            logger.error(
                f"Error calculating metrics - trades: {type(trades)}, orders: {type(orders)}: {e}"
            )
            total_profit = 0
            win_rate = 0
            trades = []
            orders = []

        # Create dashboard data object
        try:
            dashboard_data = {
                "balance": balance,
                "total_trades": len(trades) if isinstance(trades, list) else 0,
                "total_profit": total_profit,
                "win_rate": win_rate,
                "active_orders": len(orders) if isinstance(orders, list) else 0,
                "bot_status": status.get("status", "stopped"),
                "is_running": status.get("is_running", False),
                "recent_trades": (
                    trades[-5:] if isinstance(trades, list) and trades else []
                ),
                "active_orders_list": (
                    orders[:5] if isinstance(orders, list) and orders else []
                ),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "trading_mode": mode_status.get("mode", "paper"),
                "is_real_trading": mode_status.get("is_real_trading", False),
                "is_paper_trading": mode_status.get("is_paper_trading", True),
                "api_configured": mode_status.get("api_configured", False),
                "strategy_name": "Grid DCA",
                "mode": mode_status.get("mode", "paper"),
                "exchange_status": (
                    "live"
                    if mode_status.get("is_real_trading", False)
                    else "simulation"
                ),
            }
        except Exception as e:
            logger.error(f"Error creating dashboard data: {e}")
            # Fallback dashboard data
            dashboard_data = {
                "balance": balance,
                "total_trades": 0,
                "total_profit": 0,
                "win_rate": 0,
                "active_orders": 0,
                "bot_status": "stopped",
                "is_running": False,
                "recent_trades": [],
                "active_orders_list": [],
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "trading_mode": mode_status.get("mode", "paper"),
                "is_real_trading": False,
                "is_paper_trading": True,
                "api_configured": False,
                "strategy_name": "Grid DCA",
                "mode": mode_status.get("mode", "paper"),
                "exchange_status": (
                    "live"
                    if mode_status.get("is_real_trading", False)
                    else "simulation"
                ),
            }

        logger.info(
            f"Dashboard data prepared: {dashboard_data['trading_mode']} mode, Balance: ${balance:.2f}"
        )

        # Render template
        return template_engine.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "title": "Trading Bot Dashboard",
            },
        )

    except Exception as e:
        logger.error(f"Error loading dashboard data: {e}")

        # Return error template with default data
        error_data = {
            "balance": 0,
            "total_trades": 0,
            "total_profit": 0,
            "win_rate": 0,
            "active_orders": 0,
            "bot_status": "error",
            "is_running": False,
            "recent_trades": [],
            "active_orders_list": [],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trading_mode": "paper",
            "is_real_trading": False,
            "is_paper_trading": True,
            "api_configured": False,
            "error_message": str(e),
        }

        template_engine = templates_obj if templates_obj else templates
        return template_engine.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "dashboard_data": error_data,
                "title": "Trading Bot Dashboard - Error",
            },
        )


@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    """Portfolio management page."""
    try:
        mode_status = trading_mode_manager.get_status()
        manager = trading_mode_manager.get_active_strategy_manager()
        current_balance = trading_mode_manager.get_balance()

        # Get trades for profit calculation
        trades = []
        if manager and hasattr(manager, "get_trades"):
            trades = manager.get_trades()
            if not isinstance(trades, list):
                trades = []

        # Calculate portfolio metrics
        total_profit = sum(t.get("profit", 0) for t in trades if isinstance(t, dict))
        daily_change = total_profit  # Simplified for now
        daily_change_pct = (
            (total_profit / current_balance * 100) if current_balance > 0 else 0
        )

        dashboard_data = {
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "balance": current_balance,
        }

        # Get actual holdings from paper trading simulator
        holdings = []
        available_balance = current_balance
        locked_balance = 0.0
        btc_amount = 0.0
        btc_value = 0.0

        if manager and hasattr(manager, "paper_simulator"):
            simulator = manager.paper_simulator
            available_balance = getattr(simulator, "current_balance", current_balance)
            locked_balance = getattr(simulator, "locked_balance", 0.0)
            btc_amount = getattr(simulator, "btc_holdings", 0.0)
            btc_price = getattr(simulator, "current_btc_price", 43000.0)
            btc_value = btc_amount * btc_price

            # Create holdings list
            if btc_amount > 0:
                holdings.append(
                    {
                        "symbol": "BTC",
                        "asset": "BTC",
                        "amount": btc_amount,
                        "value": btc_value,
                        "price": btc_price,
                        "percentage": (
                            (btc_value / current_balance * 100)
                            if current_balance > 0
                            else 0
                        ),
                    }
                )

            if available_balance > 0:
                holdings.append(
                    {
                        "symbol": "USDT",
                        "asset": "USDT",
                        "amount": available_balance,
                        "value": available_balance,
                        "price": 1.0,
                        "percentage": (
                            (available_balance / current_balance * 100)
                            if current_balance > 0
                            else 0
                        ),
                    }
                )

        # Portfolio data for template
        portfolio_data = {
            "total_balance": current_balance,
            "available_balance": available_balance,
            "locked_balance": locked_balance,
            "unrealized_pnl": total_profit,
            "realized_pnl": total_profit,
            "daily_change": daily_change,
            "daily_change_pct": daily_change_pct,
            "holdings": holdings,  # Use actual holdings
            "positions": [],  # No positions for grid trading
            "assets": [
                {
                    "symbol": "USDT",
                    "amount": available_balance,
                    "value": available_balance,
                },
                {"symbol": "BTC", "amount": btc_amount, "value": btc_value},
            ],
        }

        return templates.TemplateResponse(
            "portfolio.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "portfolio_data": portfolio_data,
                "title": "Portfolio Management",
            },
        )
    except Exception as e:
        logger.error(f"Error loading portfolio page: 'portfolio_data' is undefined")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": str(e),
                "title": "Portfolio Error",
            },
        )


@router.get("/trades", response_class=HTMLResponse)
async def trades_page(request: Request):
    """Trading history page."""
    try:
        mode_status = trading_mode_manager.get_status()
        manager = trading_mode_manager.get_active_strategy_manager()

        # Get trades from strategy manager and fix timestamp formatting
        trades = []
        analytics = {
            "total_trades": 0,
            "winning_trades": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "total_volume": 0.0,
            "active_orders_count": 0,
        }

        if manager:
            # Get analytics if available
            if hasattr(manager, "get_analytics"):
                analytics = manager.get_analytics()

            # Get trades
            if hasattr(manager, "get_trades"):
                raw_trades = manager.get_trades()
                if isinstance(raw_trades, list):
                    for trade in raw_trades:
                        if isinstance(trade, dict):
                            # Fix timestamp formatting issue
                            timestamp = trade.get(
                                "timestamp", datetime.now().isoformat()
                            )
                            if isinstance(timestamp, str):
                                try:
                                    # Parse ISO format string to datetime for display
                                    if "T" in timestamp:
                                        dt = datetime.fromisoformat(
                                            timestamp.replace("Z", "+00:00")
                                        )
                                        trade["timestamp"] = dt
                                    else:
                                        trade["timestamp"] = datetime.now()
                                except:
                                    trade["timestamp"] = datetime.now()
                            elif hasattr(timestamp, "strftime"):
                                trade["timestamp"] = timestamp
                            else:
                                trade["timestamp"] = datetime.now()

                            # Ensure required fields exist with proper mapping
                            trade.setdefault("symbol", "BTCUSDT")
                            trade.setdefault("profit", 0.0)
                            trade.setdefault("status", "completed")

                            # Map side to type for template compatibility
                            if "side" in trade and "type" not in trade:
                                trade["type"] = trade["side"].lower()

                            # Calculate USD amount if not present
                            if "cost" in trade:
                                trade["usd_amount"] = trade["cost"]
                            elif "amount" in trade and "price" in trade:
                                trade["usd_amount"] = trade["amount"] * trade["price"]
                            else:
                                trade["usd_amount"] = 0.0

                            trades.append(trade)

        dashboard_data = {
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "trades": trades,
        }

        # Use analytics data for template
        trades_data = {
            "total_trades": analytics.get("total_trades", 0),
            "winning_trades": analytics.get("winning_trades", 0),
            "win_rate": analytics.get("win_rate", 0.0),
            "total_profit": analytics.get("total_profit", 0.0),
            "total_volume": analytics.get("total_volume", 0.0),
            "active_orders_count": analytics.get("active_orders_count", 0),
            "recent_trades": trades[-20:] if trades else [],  # Last 20 trades
        }

        return templates.TemplateResponse(
            "trades.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "trades_data": trades_data,
                "title": "Trading History",
            },
        )
    except Exception as e:
        logger.error(f"Error loading trades page: {str(e)}")
        # Return a valid trades page with empty data instead of error
        dashboard_data = {
            "balance": 10000.0,
            "total_profit": 0.0,
            "win_rate": 0.0,
            "active_orders": [],
            "recent_trades": [],
            "trading_mode": "paper",
            "is_real_trading": False,
        }
        trades_data = {
            "total_trades": 0,
            "winning_trades": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "recent_trades": [],
        }
        return templates.TemplateResponse(
            "trades.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "trades_data": trades_data,
                "title": "Trading History",
            },
        )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings and configuration page."""
    try:
        mode_status = trading_mode_manager.get_status()

        dashboard_data = {
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "api_configured": mode_status.get("api_configured", False),
        }

        # Settings data for template
        settings_data = {
            "paper_balance": 10000,
            "api_key": (
                "***configured***" if mode_status.get("api_configured", False) else ""
            ),
            "api_secret": (
                "***configured***" if mode_status.get("api_configured", False) else ""
            ),
            "api_key_configured": mode_status.get("api_configured", False),
            "api_secret_configured": mode_status.get("api_configured", False),
            "trading_pair": "BTC/USDT",
            "balance_allocation": 10,
            "risk_level": "medium",
        }

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "settings_data": settings_data,
                "mode_status": mode_status,
                "title": "Settings & Configuration",
            },
        )
    except Exception as e:
        logger.error(f"Error loading settings page: 'settings_data' is undefined")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": str(e),
                "title": "Settings Error",
            },
        )


@router.get("/grid-dca", response_class=HTMLResponse)
async def grid_dca_page(request: Request):
    """Grid DCA strategy page."""
    try:
        mode_status = trading_mode_manager.get_status()
        manager = trading_mode_manager.get_active_strategy_manager()

        status = {}
        trades = []
        orders = []

        if manager:
            if hasattr(manager, "get_status"):
                status = manager.get_status()
            if hasattr(manager, "get_trades"):
                trades = manager.get_trades()
                if not isinstance(trades, list):
                    trades = []
            if hasattr(manager, "get_active_orders"):
                orders = manager.get_active_orders()
                if not isinstance(orders, list):
                    orders = []

        dashboard_data = {
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "strategy_status": status,
            "bot_status": status.get("status", "stopped"),
            "is_running": status.get("is_running", False),
            "trades": trades,
            "active_orders": orders,
            "balance": trading_mode_manager.get_balance(),
        }

        return templates.TemplateResponse(
            "grid_dca.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "title": "Grid DCA Strategy",
            },
        )
    except Exception as e:
        logger.error(f"Error loading grid DCA page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": str(e),
                "title": "Grid DCA Error",
            },
        )
