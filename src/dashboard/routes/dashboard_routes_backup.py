"""
Dashboard routes for HTML page        # Get basic bot data (matching template expectations)
        bot_data = {
            "status": "running",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_trades": 0,
            "portfolio_value": 10000.0,
            "daily_pnl": 0.0,
            "uptime": "0:00:00",
            "mode": "paper",
            "portfolio": {
                "balance": 10000.0,
                "pnl": 0.0,
                "pnl_pct": 0.0,
                "positions": 0
            }
        }
from datetime import datetime
from typing import Optional
from pathlib import Path

try:
    from fastapi import APIRouter, Request, Form
    from fastapi.responses import HTMLResponse, RedirectResponse
    from fastapi.templating import Jinja2Templates
except ImportError:
    APIRouter = None

from ...core.bot import TradingBot
from ...utils.logger import get_logger

# Create router
if APIRouter:
    router = APIRouter()
else:
    router = None

logger = get_logger(__name__)

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard home page."""
    try:
        # Get basic bot data (matching template expectations)
        bot_data = {
            "status": "running",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_trades": 0,
            "portfolio_value": 10000.0,
            "daily_pnl": 0.0,
            "uptime": "0:00:00",
            "mode": "paper",
            "portfolio": {
                "balance": 10000.0,
                "pnl": 0.0,
                "pnl_pct": 0.0,
                "positions": 0
            }
        }

        # Get basic dashboard data
        dashboard_data = {
            "total_value": 10000.0,
            "daily_change": 0.0,
            "active_positions": 0,
            "pending_orders": 0,
        }

        return templates.TemplateResponse(
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
            "total_value": 10000.0,
            "available_balance": 5000.0,
            "positions": [],
            "daily_pnl": 0.0,
            "total_pnl": 0.0,
        }

        return templates.TemplateResponse(
            "portfolio.html",
            {
                "request": request,
                "title": "Portfolio Management",
                "portfolio_data": portfolio_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering portfolio page: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/trades", response_class=HTMLResponse)
async def trades_page(request: Request):
    """Trade history page."""
    try:
        trades_data = {
            "recent_trades": [],
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
        }

        return templates.TemplateResponse(
            "trades.html",
            {
                "request": request,
                "title": "Trade History",
                "trades_data": trades_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering trades page: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/strategies", response_class=HTMLResponse)
async def strategies_page(request: Request):
    """Strategy management page."""
    try:
        strategies_data = {
            "active_strategies": [],
            "available_strategies": ["MovingAverageCrossover", "RSIStrategy"],
            "performance": {},
        }

        return templates.TemplateResponse(
            "strategies.html",
            {
                "request": request,
                "title": "Strategy Management",
                "strategies_data": strategies_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering strategies page: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Bot settings and configuration page."""
    try:
        settings_data = {
            "bot_mode": "paper",
            "exchange": "binance",
            "risk_settings": {"max_position_size": 0.1, "stop_loss": 0.05},
        }

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "title": "Bot Settings",
                "settings_data": settings_data,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering settings page: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/favicon.ico")
async def favicon():
    from fastapi.responses import Response
    return Response(content="", media_type="image/x-icon")
