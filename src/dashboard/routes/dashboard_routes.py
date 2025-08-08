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
                if hasattr(manager, "get_active_orders"):
                    orders = manager.get_active_orders()
            except Exception as e:
                logger.error(f"Error getting data from manager: {e}")

        # Calculate metrics
        total_profit = sum(
            trade.get("profit", 0) for trade in trades if isinstance(trade, dict)
        )
        win_trades = [
            t for t in trades if isinstance(t, dict) and t.get("profit", 0) > 0
        ]
        win_rate = len(win_trades) / len(trades) * 100 if trades else 0

        # Create dashboard data object
        dashboard_data = {
            "balance": balance,
            "total_trades": len(trades),
            "total_profit": total_profit,
            "win_rate": win_rate,
            "active_orders": len(orders),
            "bot_status": status.get("status", "stopped"),
            "is_running": status.get("is_running", False),
            "recent_trades": trades[-5:] if trades else [],
            "active_orders_list": orders[:5] if orders else [],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "is_paper_trading": mode_status.get("is_paper_trading", True),
            "api_configured": mode_status.get("api_configured", False),
            "strategy_name": "Grid DCA",
            "mode": mode_status.get("mode", "paper"),
            "exchange_status": (
                "live" if mode_status.get("is_real_trading", False) else "simulation"
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

        dashboard_data = {
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "balance": mode_status.get("balance", 0),
        }

        return templates.TemplateResponse(
            "portfolio.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "title": "Portfolio Management",
            },
        )
    except Exception as e:
        logger.error(f"Error loading portfolio page: {e}")
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

        trades = []
        if manager and hasattr(manager, "get_trades"):
            trades = manager.get_trades()

        dashboard_data = {
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "trades": trades,
        }

        return templates.TemplateResponse(
            "trades.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "title": "Trading History",
            },
        )
    except Exception as e:
        logger.error(f"Error loading trades page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": str(e),
                "title": "Trades Error",
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

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "dashboard_data": dashboard_data,
                "title": "Settings & Configuration",
            },
        )
    except Exception as e:
        logger.error(f"Error loading settings page: {e}")
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
        if manager and hasattr(manager, "get_status"):
            status = manager.get_status()

        dashboard_data = {
            "trading_mode": mode_status.get("mode", "paper"),
            "is_real_trading": mode_status.get("is_real_trading", False),
            "strategy_status": status,
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
