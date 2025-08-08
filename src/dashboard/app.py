"""Main FastAPI application for the trading bot dashboard."""

import logging
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Crypto Trading Bot Dashboard",
    description="Web dashboard for monitoring and controlling the trading bot",
    version="1.0.0",
)

# Import and include routers
try:
    from .routes import dashboard_routes, api_routes, websocket_routes

    app.include_router(dashboard_routes.router, tags=["dashboard"])
    app.include_router(api_routes.router, prefix="/api", tags=["api"])
    app.include_router(websocket_routes.router, prefix="/ws", tags=["websocket"])

    logger.info("All routes loaded successfully")
except Exception as e:
    logger.error(f"Error loading routes: {e}")

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Static files mounted from {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Trading Bot Dashboard started")

    # Initialize real trading integration
    try:
        from .real_trading_integration import real_trading_integrator

        await real_trading_integrator.initialize_real_trading()
        logger.info("✅ Real trading integration initialized")
    except Exception as e:
        logger.warning(f"⚠️ Real trading not available: {e}")
        logger.info("📊 Dashboard will use paper trading only")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Trading Bot Dashboard stopped")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
