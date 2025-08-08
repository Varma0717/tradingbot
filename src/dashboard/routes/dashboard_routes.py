"""Dashboard routes for the trading bot web interface."""

import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import real trading integration
from ..real_trading_integration import real_trading_integrator

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
    """Main dashboard home page with real-time universal strategy data."""
    try:
        logger.info("Dashboard route hit - loading real universal strategy data")
        logger.info(f"Templates directory: {templates_dir}")
        logger.info(f"Templates directory exists: {templates_dir.exists()}")

        # Use passed templates object if available, otherwise use module-level
        template_engine = templates_obj if templates_obj else templates

        # Initialize default values
        trades = []
        orders = []
        status = {}
        total_profit = 0

        # Get real data from universal strategy using the SAME instance that's running
        try:
            # First check for real trading data
            real_trading_status = (
                await real_trading_integrator.get_real_trading_status()
            )

            if (
                real_trading_status.get("available", False)
                and real_trading_status.get("mode") == "real"
            ):
                # Use real trading data
                logger.info("📊 Using REAL trading data")

                status = real_trading_status.get("strategy", {})
                trades = real_trading_integrator.get_real_trades()
                orders = real_trading_integrator.get_real_orders()
                account_info = real_trading_status.get("account", {})

                # Real trading metrics
                total_profit = sum(trade.get("profit_usdt", 0) for trade in trades)
                balance = account_info.get("usdt_balance", 0)
                is_real_trading = True

            else:
                # Fallback to paper trading data
                logger.info("📊 Using PAPER trading data")

                # Import the global strategy manager function from api_routes
                from .api_routes import get_strategy_manager

                strategy_manager = await get_strategy_manager()

                # Get real strategy data from the RUNNING instance
                status = strategy_manager.get_strategy_status()
                trades = strategy_manager.get_trades()
                orders = strategy_manager.get_active_orders()

                total_profit = sum(trade.get("profit", 0) for trade in trades)
                balance = status.get("balance", 0)
                is_real_trading = False
            # Calculate metrics
            win_trades = [t for t in trades if t.get("profit", 0) > 0]
            win_rate = len(win_trades) / len(trades) * 100 if trades else 0

            bot_data = {
                "status": "active" if status.get("status") == "active" else "stopped",
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "portfolio": {
                    "balance": balance,
                    "pnl": total_profit,
                    "pnl_pct": ((total_profit / balance) * 100 if balance > 0 else 0),
                    "positions": len(orders),
                },
                "orders": {
                    "active": len(orders),
                    "pending": len(orders),
                    "completed": len(trades),
                    "cancelled": 0,
                },
                "strategies": {
                    "strategies": [
                        {
                            "name": status.get("strategy", "Universal Grid DCA"),
                            "enabled": status.get("status") == "active",
                            "signals_count": len(trades),
                            "type": "universal_grid_dca",
                            "description": f"Universal Grid DCA - {status.get('grid_levels', 0)} levels, {status.get('grid_spacing', '0%')} spacing",
                        }
                    ]
                },
                "mode": "real" if is_real_trading else "paper",
                "current_price": 67500.0,  # Will get from real exchange
                "exchange_status": "live" if is_real_trading else "simulation",
                "universal_strategy": {
                    "status": status,
                    "trades": trades[-5:] if trades else [],  # Last 5 trades
                    "orders": orders[:10] if orders else [],  # First 10 orders
                    "metrics": {
                        "total_trades": len(trades),
                        "total_profit": total_profit,
                        "win_rate": win_rate,
                        "active_orders": len(orders),
                    },
                },
            }

            logger.info(
                f"✅ Real strategy data loaded: {len(trades)} trades, {len(orders)} orders, ${total_profit:.2f} profit"
            )
            logger.info(f"📊 Balance from strategy: ${status.get('balance', 0):.2f}")
            logger.info(
                f"📊 Bot status from strategy: {status.get('status', 'unknown')}"
            )
            logger.info(
                f"📊 Dashboard data balance: ${bot_data['portfolio']['balance']:.2f}"
            )
            logger.info(f"📊 Dashboard bot status: {bot_data['status']}")

        except Exception as e:
            logger.error(f"❌ Error loading universal strategy data: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Fallback to minimal data
            bot_data = {
                "status": "error",
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "portfolio": {"balance": 0, "pnl": 0.0, "pnl_pct": 0.0, "positions": 0},
                "orders": {"active": 0, "pending": 0, "completed": 0, "cancelled": 0},
                "strategies": {
                    "strategies": [
                        {
                            "name": "Universal Grid DCA",
                            "enabled": False,
                            "signals_count": 0,
                            "type": "universal_grid_dca",
                            "description": "Universal Grid DCA strategy",
                        }
                    ]
                },
                "mode": "live",
                "current_price": 67500.0,
                "exchange_status": "error",
                "error": str(e),
            }

        # Get basic dashboard data
        dashboard_data = {
            "balance": balance,  # Current balance (includes profits)
            "bot_status": bot_data["status"],
            "total_value": balance,  # Total value is the current balance
            "daily_change": bot_data["portfolio"]["pnl"],
            "total_profit": total_profit,  # Show accumulated profit separately
            "active_orders": bot_data["orders"]["active"],
            "active_positions": bot_data["portfolio"]["positions"],
            "pending_orders": bot_data["orders"]["pending"],
            "recent_trades": (
                trades[-5:] if trades else []
            ),  # Use the initialized trades variable
            "strategy": {
                "status": status.get("status", "inactive"),
                "symbol": status.get("symbol", "BTC/USDT"),
                "investment": balance,
                "grid_levels": status.get("grid_levels", 0),
                "take_profit": status.get("take_profit", "2%"),  # Keep as string with %
                "stop_loss": status.get("stop_loss", "8%"),  # Keep as string with %
                "win_rate": status.get("win_rate", 89.5),
                "order_size": status.get("order_size", 0),
                "grid_spacing": status.get("grid_spacing", "1%"),  # Add grid spacing
                "trading_mode": (
                    "REAL TRADING (Live)"
                    if is_real_trading
                    else "PAPER TRADING (Simulation)"
                ),
                "mode_notice": (
                    "Real money trading is active. All profits and losses affect your actual Binance account."
                    if is_real_trading
                    else "All profits and trades are simulated. No real money is being traded."
                ),
            },
            "is_real_trading": is_real_trading,  # Add flag for templates
        }

        # Debug logging to see what data is being passed to templates
        logger.info(f"🔍 Template Data Debug:")
        logger.info(f"   dashboard_data.balance: ${dashboard_data['balance']}")
        logger.info(f"   dashboard_data.bot_status: {dashboard_data['bot_status']}")
        logger.info(
            f"   dashboard_data.total_profit: ${dashboard_data['total_profit']}"
        )
        logger.info(
            f"   dashboard_data.recent_trades count: {len(dashboard_data['recent_trades'])}"
        )
        logger.info(
            f"   dashboard_data.strategy.status: {dashboard_data['strategy']['status']}"
        )
        logger.info(f"   bot_data.status: {bot_data['status']}")
        logger.info(f"   Total trades passed: {len(trades)}")
        logger.info(f"   Total orders passed: {len(orders)}")
        logger.info(
            f"   Strategy take_profit: {dashboard_data['strategy']['take_profit']}"
        )
        logger.info(f"   Strategy stop_loss: {dashboard_data['strategy']['stop_loss']}")

        # Fix the data structure for template compatibility
        template_bot_data = {
            "portfolio": {
                "balance": bot_data["portfolio"]["balance"],
                "pnl": bot_data["portfolio"]["pnl"],
                "pnl_pct": bot_data["portfolio"]["pnl_pct"],
                "daily_change": bot_data["portfolio"]["pnl"],
                "daily_change_pct": bot_data["portfolio"]["pnl_pct"],
                "positions": bot_data["portfolio"]["positions"],  # Add positions count
            },
            "orders": {
                "active": bot_data["orders"]["active"],  # Use the existing structure
                "pending": bot_data["orders"]["pending"],
                "completed": bot_data["orders"]["completed"],
                "cancelled": bot_data["orders"]["cancelled"],
            },
            "positions": bot_data.get("universal_strategy", {}).get("orders", [])[
                :5
            ],  # Use orders as positions
            "status": bot_data["status"],
            "strategies": bot_data.get(
                "strategies", {"strategies": []}
            ),  # Include strategies data
        }

        return template_engine.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "Trading Dashboard",
                "bot_data": template_bot_data,  # Use the corrected data structure
                "dashboard_data": dashboard_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return a simple error response instead of trying to use error.html
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content="""
            <html>
                <head><title>Dashboard Error</title></head>
                <body>
                    <h1>Dashboard Error</h1>
                    <p>An error occurred loading the dashboard.</p>
                    <a href="/">Try Again</a>
                </body>
            </html>
            """,
            status_code=500,
        )


@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    """Portfolio management page."""
    try:
        # Get real portfolio data from the strategy
        from .api_routes import get_strategy_manager

        strategy_manager = await get_strategy_manager()
        status = strategy_manager.get_strategy_status()
        trades = strategy_manager.get_trades()

        # Calculate portfolio metrics
        total_profit = sum(trade.get("profit", 0) for trade in trades)
        balance = status.get("balance", 0)

        portfolio_data = {
            "total_balance": balance + total_profit,
            "available_balance": balance,
            "locked_balance": 0.0,  # Would calculate from active orders
            "unrealized_pnl": total_profit,
            "total_trades": len(trades),
            "win_trades": len([t for t in trades if t.get("profit", 0) > 0]),
            "positions": (
                [
                    {
                        "symbol": "BTC/USDT",
                        "amount": balance / 67500.0,  # Simulated BTC amount
                        "value_usd": balance,
                        "allocation": 100.0,
                        "change_24h": (
                            (total_profit / balance * 100) if balance > 0 else 0
                        ),
                        "name": "Bitcoin",
                    }
                ]
                if balance > 0
                else []
            ),
        }

        return templates.TemplateResponse(
            "portfolio.html",
            {
                "request": request,
                "title": "Portfolio",
                "portfolio_data": portfolio_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering portfolio page: {e}")
        # Use simple HTML response for errors to avoid template loading issues
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Portfolio Error</title></head>
                <body>
                    <h1>Portfolio Error</h1>
                    <p>Error: {str(e)}</p>
                    <a href="/">Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=500,
        )


@router.get("/trades", response_class=HTMLResponse)
async def trades_page(request: Request):
    """Trading history page."""
    try:
        # Get real trades data from the strategy
        from .api_routes import get_strategy_manager

        strategy_manager = await get_strategy_manager()
        trades = strategy_manager.get_trades()

        # Calculate trading metrics
        total_profit = sum(trade.get("profit", 0) for trade in trades)
        win_trades = [t for t in trades if t.get("profit", 0) > 0]
        win_rate = (len(win_trades) / len(trades) * 100) if trades else 0

        trades_data = {
            "recent_trades": trades[-20:] if trades else [],  # Last 20 trades
            "total_trades": len(trades),
            "win_rate": win_rate,
            "total_profit": total_profit,
            "winning_trades": len(win_trades),
            "losing_trades": len(trades) - len(win_trades),
            "avg_profit": total_profit / len(trades) if trades else 0,
        }

        return templates.TemplateResponse(
            "trades.html",
            {
                "request": request,
                "title": "Trading History",
                "trades_data": trades_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering trades page: {e}")
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Trades Error</title></head>
                <body>
                    <h1>Trades Error</h1>
                    <p>Error: {str(e)}</p>
                    <a href="/">Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=500,
        )


@router.get("/strategies/grid-dca", response_class=HTMLResponse)
async def strategies_grid_dca(request: Request):
    """Grid DCA strategy page."""
    try:
        context = {
            "request": request,
            "title": "Grid DCA Strategy",
            "strategy_name": "Grid DCA",
        }
        return templates.TemplateResponse("grid_dca.html", context)
    except Exception as e:
        logger.error(f"Error rendering strategies/grid-dca page: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/grid-dca", response_class=HTMLResponse)
async def grid_dca_page(request: Request):
    """Grid DCA strategy page with real-time data."""
    try:
        # Import and get the SAME universal strategy instance that's running
        from .api_routes import get_strategy_manager

        # Get real strategy data from the RUNNING instance
        strategy_manager = await get_strategy_manager()

        # Get current status and data
        status = strategy_manager.get_strategy_status()
        trades = strategy_manager.get_trades()
        orders = strategy_manager.get_active_orders()

        # Prepare context with real data
        context = {
            "request": request,
            "title": "Grid DCA Strategy",
            "page": "grid-dca",
            "strategy_data": {
                "status": status,
                "trades": trades,
                "orders": orders,
                "summary": {
                    "total_trades": len(trades),
                    "active_orders": len(orders),
                    "total_profit": sum(trade.get("profit", 0) for trade in trades),
                    "win_rate": status.get("win_rate", 0),
                    "balance": status.get("balance", 0),
                },
            },
        }

        return templates.TemplateResponse("grid_dca.html", context)

    except Exception as e:
        logger.error(f"Error rendering Grid DCA page: {e}")
        import traceback

        traceback.print_exc()

        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Grid DCA Error</title></head>
                <body>
                    <h1>Grid DCA Error</h1>
                    <p>Error: {str(e)}</p>
                    <p>This usually means the universal strategy needs to be initialized.</p>
                    <a href="/">Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=500,
        )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Bot settings and configuration page."""
    try:
        # Import config to read .env values
        from src.core.config import Config

        config = Config()

        # Load API keys from .env (show as configured/not configured)
        api_key_configured = bool(config.binance_api_key)
        api_secret_configured = bool(config.binance_api_secret)

        # Get comprehensive settings data for the new modern settings page
        settings_data = {
            "api_key_configured": api_key_configured,
            "api_secret_configured": api_secret_configured,
            "api_key": "••••••••••••••••" if api_key_configured else "",
            "api_secret": "••••••••••••••••" if api_secret_configured else "",
            "exchange": "binance",
            "bot_mode": "paper",  # Always paper mode (simulation)
            "trading_pair": "BTC/USDT",
            "balance_allocation": 10,
            "risk_level": "medium",
            "auto_compound": False,
            "stop_loss_enabled": True,
            "notifications_enabled": False,
            "paper_trading_notice": "You are in PAPER TRADING mode. All trades and profits are simulated and do not affect your real Binance account.",
            "trading_settings": {
                "max_pairs": 5,
                "base_currency": "USDT",
                "enabled_strategies": ["grid_dca"],
                "auto_trading": False,
            },
            "risk_settings": {
                "max_position_size": 0.1,
                "stop_loss": 0.05,
                "max_daily_loss": 0.02,
                "risk_per_trade": 0.01,
            },
            "grid_dca_settings": {
                "grid_count": 10,
                "grid_spacing": 1.0,
                "dca_intervals": 24,
                "min_order_size": 10.0,
                "take_profit": 2.0,
            },
            "notifications": {
                "email_enabled": False,
                "telegram_enabled": False,
                "discord_enabled": False,
            },
            "advanced": {
                "logging_level": "INFO",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 1200,
            },
        }

        return templates.TemplateResponse(
            "settings_new.html",
            {
                "request": request,
                "title": "Bot Settings",
                "settings_data": settings_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering settings page: {e}")
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Settings Error</title></head>
                <body>
                    <h1>Settings Error</h1>
                    <p>Error: {str(e)}</p>
                    <a href="/">Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=500,
        )


@router.get("/favicon.ico")
async def favicon():
    from fastapi.responses import Response

    return Response(content="", media_type="image/x-icon")
