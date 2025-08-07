"""Dashboard routes for the trading bot web interface."""

import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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
    """Main dashboard home page."""
    try:
        logger.info("Dashboard route hit - starting")
        logger.info(f"Templates directory: {templates_dir}")
        logger.info(f"Templates directory exists: {templates_dir.exists()}")

        # Use passed templates object if available, otherwise use module-level
        template_engine = templates_obj if templates_obj else templates

        # Minimal static data - JavaScript will load real-time data via API
        bot_data = {
            "status": "loading",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "portfolio": {
                "balance": 0,
                "pnl": 0.0,
                "pnl_pct": 0.0,
                "positions": 0,
            },
            "orders": {
                "active": 0,
                "pending": 0,
                "completed": 0,
                "cancelled": 0,
            },
            "strategies": {
                "strategies": [
                    {
                        "name": "Grid Trading + DCA",
                        "enabled": True,
                        "signals_count": 0,
                        "type": "grid_dca",
                        "description": "Grid trading with Dollar Cost Averaging",
                    }
                ]
            },
            "mode": "live",
            "current_price": 0.0,
            "exchange_status": "loading",
        }

        # Get basic dashboard data
        dashboard_data = {
            "total_value": bot_data["portfolio"]["balance"],
            "daily_change": bot_data["portfolio"]["pnl"],
            "active_positions": bot_data["portfolio"]["positions"],
            "pending_orders": bot_data["orders"]["pending"],
        }

        return template_engine.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "Trading Dashboard",
                "bot_data": bot_data,
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
        portfolio_data = {
            "total_balance": 10000.0,
            "available_balance": 8500.0,
            "unrealized_pnl": 150.0,
            "positions": [],
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
        trades_data = {
            "recent_trades": [],
            "total_trades": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
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


@router.get("/strategies", response_class=HTMLResponse)
async def strategies_page(request: Request):
    """Trading strategies page."""
    try:
        strategies_data = {
            "active_strategies": ["SMA Crossover"],
            "available_strategies": ["SMA Crossover", "RSI", "MACD"],
            "strategy_performance": {},
        }

        return templates.TemplateResponse(
            "strategies.html",
            {
                "request": request,
                "title": "Trading Strategies",
                "strategies_data": strategies_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering strategies page: {e}")
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Strategies Error</title></head>
                <body>
                    <h1>Strategies Error</h1>
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
    """Grid DCA strategy page."""
    try:
        return templates.TemplateResponse(
            "grid_dca.html",
            {"request": request, "title": "Grid DCA Strategy", "page": "grid-dca"},
        )
    except Exception as e:
        logger.error(f"Error rendering Grid DCA page: {e}")
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Grid DCA Error</title></head>
                <body>
                    <h1>Grid DCA Error</h1>
                    <p>Error: {str(e)}</p>
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
        # Get comprehensive settings data for the new modern settings page
        settings_data = {
            "bot_mode": "paper",
            "exchange": "binance",
            "api_keys": {"binance_key": "****", "binance_secret": "****"},
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
