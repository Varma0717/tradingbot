"""
Main FastAPI application for the trading bot dashboard.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    import uvicorn
except ImportError:
    FastAPI = None

from ..core.config import Config
from ..core.bot import TradingBot
from ..utils.logger import get_logger


class DashboardApp:
    """
    Main dashboard application class.
    """

    def __init__(self, config: Config, trading_bot: Optional[TradingBot] = None):
        """
        Initialize dashboard application.

        Args:
            config: Configuration object
            trading_bot: Trading bot instance (optional)
        """
        self.config = config
        self.trading_bot = trading_bot
        self.logger = get_logger(__name__)

        # WebSocket connections
        self.websocket_connections = set()

        # Initialize FastAPI app
        if FastAPI is None:
            raise ImportError("FastAPI is required for dashboard")

        self.app = self._create_app()

        # Setup templates and static files
        self._setup_templates()
        self._setup_routes()

        # If trading bot is provided, set it up for API routes
        if trading_bot:
            self.set_trading_bot(trading_bot)

    def _create_app(self) -> FastAPI:
        """Create FastAPI application."""
        app = FastAPI(
            title="Crypto Trading Bot Dashboard",
            description="Real-time monitoring and control dashboard for the crypto trading bot",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return app

    def _setup_templates(self):
        """Setup Jinja2 templates and static files."""
        try:
            # Create templates directory
            templates_dir = Path(__file__).parent / "templates"
            templates_dir.mkdir(exist_ok=True)

            # Create static directory
            static_dir = Path(__file__).parent / "static"
            static_dir.mkdir(exist_ok=True)

            # Setup Jinja2 templates
            self.templates = Jinja2Templates(directory=str(templates_dir))

            # Mount static files
            self.app.mount(
                "/static", StaticFiles(directory=str(static_dir)), name="static"
            )

            self.logger.info("Templates and static files setup complete")

        except Exception as e:
            self.logger.error(f"Error setting up templates: {e}")

    def _setup_routes(self):
        """Setup application routes."""
        try:
            # Import route modules
            from .routes import dashboard_routes, api_routes, websocket_routes

            # Include routers
            self.app.include_router(
                dashboard_routes.router, prefix="", tags=["dashboard"]
            )
            self.app.include_router(api_routes.router, tags=["api"])
            self.app.include_router(
                websocket_routes.router, prefix="/ws", tags=["websocket"]
            )

            # Add root route
            @self.app.get("/", response_class=HTMLResponse)
            async def root(request: Request):
                return await dashboard_routes.dashboard_home(
                    request, self.templates, self.trading_bot
                )

            # Add health check
            @self.app.get("/health")
            async def health_check():
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "bot_status": "running" if self.trading_bot else "not_connected",
                }

            self.logger.info("Routes setup complete")

        except Exception as e:
            self.logger.error(f"Error setting up routes: {e}")

    def set_trading_bot(self, trading_bot: TradingBot):
        """Set the trading bot instance."""
        self.trading_bot = trading_bot

        # Set bot for WebSocket routes
        try:
            from .routes import websocket_routes

            websocket_routes.set_trading_bot(trading_bot)
        except Exception as e:
            self.logger.error(f"Error setting bot for WebSocket routes: {e}")

        # Set bot for API routes - our universal strategy doesn't need this
        # The API routes handle their own strategy manager initialization
        self.logger.info("API routes configured for universal strategy")

        self.logger.info("Trading bot instance connected to dashboard")

    async def broadcast_update(self, message: dict):
        """
        Broadcast update to all connected WebSocket clients.

        Args:
            message: Message to broadcast
        """
        if not self.websocket_connections:
            return

        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.discard(websocket)

    def add_websocket_connection(self, websocket: WebSocket):
        """Add WebSocket connection."""
        self.websocket_connections.add(websocket)
        self.logger.info(
            f"WebSocket connection added. Total: {len(self.websocket_connections)}"
        )

    def remove_websocket_connection(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.websocket_connections.discard(websocket)
        self.logger.info(
            f"WebSocket connection removed. Total: {len(self.websocket_connections)}"
        )

    async def start_background_tasks(self):
        """Start background tasks for real-time updates."""
        try:
            # Start periodic updates
            asyncio.create_task(self._periodic_updates())
            self.logger.info("Background tasks started")

        except Exception as e:
            self.logger.error(f"Error starting background tasks: {e}")

    async def _periodic_updates(self):
        """Send periodic updates to connected clients."""
        while True:
            try:
                if self.trading_bot and self.websocket_connections:
                    # Get bot status
                    status_data = await self._get_bot_status()

                    # Broadcast status update
                    await self.broadcast_update(
                        {
                            "type": "status_update",
                            "data": status_data,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                # Wait 5 seconds before next update
                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"Error in periodic updates: {e}")
                await asyncio.sleep(10)

    async def _get_bot_status(self) -> dict:
        """Get current bot status data."""
        try:
            if not self.trading_bot:
                return {"status": "disconnected"}

            # Get portfolio data
            portfolio_data = {}
            if hasattr(self.trading_bot, "portfolio_manager"):
                portfolio_performance = (
                    self.trading_bot.portfolio_manager.get_portfolio_performance()
                )
                portfolio_data = {
                    "balance": portfolio_performance.get("current_balance", 0),
                    "pnl": portfolio_performance.get("total_pnl", 0),
                    "pnl_pct": portfolio_performance.get("total_return_pct", 0),
                    "positions": portfolio_performance.get("active_positions", 0),
                }

            # Get order data
            order_data = {}
            if hasattr(self.trading_bot, "order_manager"):
                order_stats = self.trading_bot.order_manager.get_order_stats()
                order_data = {
                    "active_orders": order_stats.get("active_orders", 0),
                    "total_orders": order_stats.get("total_orders", 0),
                    "fill_rate": order_stats.get("fill_rate", 0),
                }

            return {
                "status": "running",
                "portfolio": portfolio_data,
                "orders": order_data,
                "strategies": len(getattr(self.trading_bot, "strategies", [])),
                "last_update": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting bot status: {e}")
            return {"status": "error", "error": str(e)}

    def run(self, host: str = "127.0.0.1", port: int = 8000, debug: bool = True):
        """
        Run the dashboard application.

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        try:
            self.logger.info(f"Starting dashboard on http://{host}:{port}")

            # Run the application without reload to avoid the warning
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="info",
            )

        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            raise

    async def run_async(
        self, host: str = "127.0.0.1", port: int = 8000, debug: bool = True
    ):
        """
        Run the dashboard application asynchronously.

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        try:
            import uvicorn
            from uvicorn import Config, Server

            self.logger.info(f"Starting dashboard on http://{host}:{port}")

            # Create config and server for async operation
            config = Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
            )
            server = Server(config)

            # Start the server asynchronously
            await server.serve()

        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            raise


def create_app(
    config: Config, trading_bot: Optional[TradingBot] = None
) -> DashboardApp:
    """
    Create dashboard application.

    Args:
        config: Configuration object
        trading_bot: Trading bot instance (optional)

    Returns:
        Dashboard application instance
    """
    return DashboardApp(config, trading_bot)


# Create app instance for uvicorn
config = Config()
dashboard_app = create_app(config)
app = dashboard_app.app
