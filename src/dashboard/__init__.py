"""
Web Dashboard for Crypto Trading Bot
FastAPI-based dashboard for real-time monitoring and control
"""

from .main import create_app
from .routes import dashboard_routes, api_routes, websocket_routes

__all__ = ["create_app", "dashboard_routes", "api_routes", "websocket_routes"]
