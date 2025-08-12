"""
Grid Trading Integration for Flask Application
Connects Pionex-style grid engine with the main bot system
"""

import asyncio
import logging
from flask import Blueprint, jsonify, request
from datetime import datetime
from app.strategies.pionex_grid_engine import PionexGridEngine
import threading
import json

logger = logging.getLogger(__name__)


class GridTradingManager:
    """
    Manages grid trading bots for the Flask application
    """

    def __init__(self):
        self.grid_engine = None
        self.is_running = False
        self.engine_thread = None
        self.status_data = {
            "status": "stopped",
            "start_time": None,
            "total_profit": 0.0,
            "active_grids": 0,
            "total_cycles": 0,
            "daily_roi": 0.0,
            "symbols": [],
        }

        # Default trading symbols (similar to Pionex popular pairs)
        self.default_symbols = [
            "AAPL",  # Apple
            "TSLA",  # Tesla
            "MSFT",  # Microsoft
            "NVDA",  # NVIDIA
            "AMZN",  # Amazon
            "GOOGL",  # Google
        ]

        # Configuration
        self.config = {
            "initial_capital": 10000,  # $10k starting capital
            "symbols": self.default_symbols,
            "grid_count_per_symbol": 20,
            "price_range_pct": 0.3,  # 30% price range
            "investment_pct_per_symbol": 0.15,  # 15% per symbol
            "target_daily_return": 0.03,  # 3% daily target
        }

    def start_grid_trading(self, config_override=None):
        """
        Start the grid trading system
        """
        try:
            if self.is_running:
                return {"status": "error", "message": "Grid trading already running"}

            # Update config if provided
            if config_override:
                self.config.update(config_override)

            # Create new grid engine
            self.grid_engine = PionexGridEngine(
                initial_capital=self.config["initial_capital"]
            )

            # Start in background thread
            self.is_running = True
            self.engine_thread = threading.Thread(
                target=self._run_grid_engine, daemon=True
            )
            self.engine_thread.start()

            # Update status
            self.status_data.update(
                {
                    "status": "running",
                    "start_time": datetime.now().isoformat(),
                    "symbols": self.config["symbols"],
                }
            )

            logger.info("🚀 Grid Trading Started with Pionex-style strategy")
            logger.info(f"   Symbols: {', '.join(self.config['symbols'])}")
            logger.info(f"   Capital: ${self.config['initial_capital']:,}")
            logger.info(
                f"   Target Daily Return: {self.config['target_daily_return']*100:.1f}%"
            )

            return {
                "status": "success",
                "message": "Grid trading started successfully",
                "config": self.config,
                "expected_daily_return": f"{self.config['target_daily_return']*100:.1f}%",
            }

        except Exception as e:
            logger.error(f"❌ Failed to start grid trading: {e}")
            return {"status": "error", "message": str(e)}

    def _run_grid_engine(self):
        """
        Run the grid engine in async context
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Start the grid trading
            loop.run_until_complete(
                self.grid_engine.start_grid_trading(self.config["symbols"])
            )

        except Exception as e:
            logger.error(f"❌ Grid engine error: {e}")
            self.is_running = False
            self.status_data["status"] = "error"

    def stop_grid_trading(self):
        """
        Stop the grid trading system
        """
        try:
            if not self.is_running:
                return {"status": "error", "message": "Grid trading not running"}

            # Stop the engine
            if self.grid_engine:
                self.grid_engine.stop_all_grids()

            self.is_running = False

            # Update status
            self.status_data.update({"status": "stopped", "start_time": None})

            logger.info("🛑 Grid Trading Stopped")

            return {"status": "success", "message": "Grid trading stopped successfully"}

        except Exception as e:
            logger.error(f"❌ Failed to stop grid trading: {e}")
            return {"status": "error", "message": str(e)}

    def get_grid_status(self):
        """
        Get current grid trading status and performance
        """
        try:
            if self.grid_engine and self.is_running:
                # Get real-time statistics
                stats = self.grid_engine.get_grid_statistics()

                # Calculate daily return percentage
                if self.status_data.get("start_time"):
                    start_time = datetime.fromisoformat(self.status_data["start_time"])
                    hours_running = (datetime.now() - start_time).total_seconds() / 3600

                    if hours_running > 0:
                        daily_roi = (stats["roi_percentage"] / hours_running) * 24
                    else:
                        daily_roi = 0.0
                else:
                    daily_roi = 0.0

                # Update status with real data
                self.status_data.update(
                    {
                        "total_profit": stats["total_profit"],
                        "active_grids": stats["active_grids"],
                        "total_cycles": stats["total_cycles"],
                        "daily_roi": daily_roi,
                        "roi_percentage": stats["roi_percentage"],
                        "total_investment": stats["total_investment"],
                        "avg_profit_per_cycle": stats["average_profit_per_cycle"],
                        "daily_profit_target": stats["daily_profit_target"],
                        "grid_details": stats["grid_bots"],
                    }
                )

            return {"status": "success", "data": self.status_data}

        except Exception as e:
            logger.error(f"❌ Failed to get grid status: {e}")
            return {"status": "error", "message": str(e)}

    def get_grid_performance(self):
        """
        Get detailed grid performance analytics
        """
        try:
            if not self.grid_engine or not self.is_running:
                return {"status": "error", "message": "Grid trading not active"}

            stats = self.grid_engine.get_grid_statistics()

            # Calculate performance metrics
            performance = {
                "overview": {
                    "total_investment": stats["total_investment"],
                    "current_profit": stats["total_profit"],
                    "roi_percentage": stats["roi_percentage"],
                    "active_grids": stats["active_grids"],
                    "completed_cycles": stats["total_cycles"],
                    "average_profit_per_cycle": stats["average_profit_per_cycle"],
                },
                "targets": {
                    "daily_profit_target": stats["daily_profit_target"],
                    "target_roi": self.config["target_daily_return"] * 100,
                    "progress_to_target": min(
                        100,
                        (
                            stats["roi_percentage"]
                            / (self.config["target_daily_return"] * 100)
                        )
                        * 100,
                    ),
                },
                "grid_breakdown": [],
            }

            # Add individual grid performance
            for symbol, bot_stats in stats["grid_bots"].items():
                performance["grid_breakdown"].append(
                    {
                        "symbol": symbol,
                        "profit": bot_stats["profit"],
                        "cycles": bot_stats["cycles"],
                        "investment": bot_stats["investment"],
                        "roi": bot_stats["roi"],
                        "status": (
                            "Active" if bot_stats["cycles"] > 0 else "Initializing"
                        ),
                    }
                )

            return {"status": "success", "performance": performance}

        except Exception as e:
            logger.error(f"❌ Failed to get performance data: {e}")
            return {"status": "error", "message": str(e)}


# Global grid manager instance
grid_manager = GridTradingManager()

# Flask Blueprint for grid trading API
grid_bp = Blueprint("grid", __name__, url_prefix="/api/grid")


@grid_bp.route("/start", methods=["POST"])
def start_grid():
    """Start grid trading"""
    try:
        config_override = request.json if request.is_json else {}
        result = grid_manager.start_grid_trading(config_override)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@grid_bp.route("/stop", methods=["POST"])
def stop_grid():
    """Stop grid trading"""
    try:
        result = grid_manager.stop_grid_trading()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@grid_bp.route("/status", methods=["GET"])
def get_status():
    """Get grid trading status"""
    try:
        result = grid_manager.get_grid_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@grid_bp.route("/performance", methods=["GET"])
def get_performance():
    """Get detailed performance analytics"""
    try:
        result = grid_manager.get_grid_performance()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@grid_bp.route("/config", methods=["GET", "POST"])
def manage_config():
    """Get or update grid configuration"""
    try:
        if request.method == "GET":
            return jsonify({"status": "success", "config": grid_manager.config})
        else:
            # Update configuration
            new_config = request.json
            grid_manager.config.update(new_config)

            return jsonify(
                {
                    "status": "success",
                    "message": "Configuration updated",
                    "config": grid_manager.config,
                }
            )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
