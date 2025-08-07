#!/usr/bin/env python3
"""
Cryptocurrency Trading Bot - Main Entry Point
"""

import asyncio
import argparse
import sys
import logging
import signal
from pathlib import Path
import yaml

# Setup basic logging first - no emojis to avoid Windows encoding issues
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        (
            logging.FileHandler("logs/main.log", mode="a", encoding="utf-8")
            if Path("logs").exists()
            else logging.NullHandler()
        ),
    ],
)

logger = logging.getLogger(__name__)

# Global variables for graceful imports
Config = None
TradingBot = None
setup_logging = None
DashboardApp = None


def safe_import_and_setup():
    """Safely import required modules and setup components."""
    global Config, TradingBot, setup_logging, DashboardApp

    try:
        from src.core.config import Config

        logger.info("Config module imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import Config: {e}")
        Config = None

    try:
        from src.core.bot import TradingBot

        logger.info("TradingBot module imported successfully")
    except ImportError as e:
        logger.warning(f"TradingBot not available: {e}")
        TradingBot = None

    try:
        from src.utils.logger import setup_logging

        logger.info("Logger setup imported successfully")
    except ImportError as e:
        logger.warning(f"Logger setup not available: {e}")
        setup_logging = None

    try:
        from src.dashboard.main import DashboardApp

        logger.info("Dashboard module imported successfully")
    except ImportError as e:
        logger.warning(f"Dashboard not available: {e}")
        DashboardApp = None


def create_directories():
    """Create necessary directories if they don't exist."""
    directories = ["logs", "data", "config"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")


def create_default_config():
    """Create default configuration file if it doesn't exist."""
    config_dir = Path("config")
    config_path = config_dir / "config.yaml"

    if config_path.exists():
        logger.info(f"Configuration file already exists: {config_path}")
        return config_path

    logger.info("Creating default configuration file...")

    # Create basic configuration structure
    default_config = {
        "exchange": {
            "name": "binance",
            "api_key": "your_api_key_here",
            "api_secret": "your_api_secret_here",
            "testnet": True,
            "rate_limit": True,
        },
        "trading": {
            "symbol": "BTCUSDT",
            "base_currency": "BTC",
            "quote_currency": "USDT",
            "initial_capital": 1000.0,
            "risk_per_trade": 0.02,
            "max_positions": 5,
            "stop_loss": 0.05,
            "take_profit": 0.1,
        },
        "strategies": {
            "grid_dca": {
                "enabled": True,
                "grid_levels": 10,
                "grid_spacing": 0.01,
                "dca_amount": 50.0,
                "max_positions": 5,
            }
        },
        "dashboard": {
            "host": "127.0.0.1",
            "port": 8000,
            "debug": True,
            "auto_reload": True,
        },
        "logging": {"level": "INFO", "file_logging": True, "console_logging": True},
    }

    try:
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)

        logger.info(f"Created default configuration file: {config_path}")
        logger.info("Please update the configuration with your exchange credentials")
        return config_path

    except Exception as e:
        logger.error(f"Failed to create config file: {e}")
        return None


async def run_dashboard_mode(args):
    """Run the application in dashboard mode."""
    logger.info("Starting dashboard mode...")

    if DashboardApp is None:
        print("Dashboard not available. Missing dependencies.")
        return

    try:
        # Load configuration
        config_path = args.config or "config/config.yaml"
        if not Path(config_path).exists():
            print(f"Configuration file not found: {config_path}")
            config_path = create_default_config()
            if not config_path:
                return

        # Initialize dashboard
        if Config:
            try:
                config = Config(config_path)
                print("Configuration loaded successfully")
            except Exception as e:
                print(f"Configuration validation failed: {e}")
                return
        else:
            config = None

        # Create trading bot if available
        bot = None
        if TradingBot and config:
            try:
                bot = TradingBot(config)
                print("Trading bot created and connected")
            except Exception as e:
                print(f"Trading bot creation failed: {e}")

        # Create dashboard app
        dashboard = DashboardApp(config=config, bot=bot)
        print("Dashboard application created")

        # Set up host and port
        host = args.host or (config.dashboard.host if config else "127.0.0.1")
        port = args.port or (config.dashboard.port if config else 8000)

        logger.info(f"Starting dashboard on {host}:{port}")
        print(f"Dashboard starting on http://{host}:{port}")

        # Start the dashboard
        try:
            import uvicorn

            await dashboard.start_async(host=host, port=port)
        except ImportError:
            print("uvicorn not installed. Please install: pip install uvicorn")
            return
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
            print("Dashboard stopped")
        except Exception as e:
            print(f"Error starting dashboard: {e}")
            logger.error(f"Dashboard error: {e}")

    except Exception as e:
        logger.error(f"Dashboard mode error: {e}")
        print(f"Dashboard error: {e}")


async def run_trading_mode(args):
    """Run the application in trading mode."""
    logger.info("Starting trading mode...")

    try:
        # Check if required modules are available
        if Config is None:
            logger.error("Configuration system not available")
            print("Core configuration module not found")
            return

        if TradingBot is None:
            logger.error("Trading bot not available")
            print("Trading bot module not found")
            return

        # Load configuration
        config_path = args.config or "config/config.yaml"
        if not Path(config_path).exists():
            print(f"Configuration file not found: {config_path}")
            config_path = create_default_config()
            if not config_path:
                return

        # Setup enhanced logging if available
        if setup_logging:
            setup_logging(config_path)

        # Initialize configuration
        try:
            config = Config(config_path)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            print(f"Configuration error: {e}")
            return

        # Validate configuration
        if not hasattr(config, "exchange") or not config.exchange.api_key:
            logger.error("Exchange configuration incomplete")
            print("Please configure exchange credentials in config.yaml")
            return

        print("Configuration loaded and validated")

        # Create and initialize trading bot
        bot = TradingBot(config)
        print("Trading bot created")

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Shutdown signal received")
            asyncio.create_task(bot.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start trading based on mode
        if args.mode == "live":
            logger.info("Starting live trading...")
            await bot.start_live_trading()
        elif args.mode == "paper":
            logger.info("Starting paper trading...")
            await bot.start_paper_trading()
        elif args.mode == "backtest":
            if args.start_date and args.end_date:
                logger.info(
                    f"Starting backtest from {args.start_date} to {args.end_date}"
                )
                await bot.start_backtest(args.start_date, args.end_date)
            else:
                print("Backtest mode not implemented")

    except KeyboardInterrupt:
        logger.info("Trading interrupted by user")
        print("Trading stopped by user")
    except Exception as e:
        logger.error(f"Trading mode error: {e}")
        print(f"Trading error: {e}")
    finally:
        # Graceful shutdown
        if "bot" in locals():
            await bot.stop()
        logger.info("Bot stopped successfully")
        print("Bot stopped successfully")


def setup_argument_parser():
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(description="Cryptocurrency Trading Bot")
    parser.add_argument(
        "--mode",
        choices=["live", "paper", "dashboard", "backtest"],
        default="dashboard",
        help="Operating mode",
    )
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Dashboard host")
    parser.add_argument("--port", type=int, default=8000, help="Dashboard port")
    parser.add_argument(
        "--start-date", type=str, help="Backtest start date (YYYY-MM-DD)"
    )
    parser.add_argument("--end-date", type=str, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    return parser


async def main(args):
    """Main async entry point."""
    try:
        # Create necessary directories
        create_directories()

        # Import all modules safely
        safe_import_and_setup()

        # Route to appropriate mode
        if args.mode == "dashboard":
            await run_dashboard_mode(args)
        else:
            await run_trading_mode(args)

    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Application error: {e}")


def main_entry_point():
    """Synchronous entry point for the application."""
    try:
        parser = setup_argument_parser()
        args = parser.parse_args()

        # Set logging level
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        # Run the async main function
        asyncio.run(main(args))

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        logger.error(f"Argument parsing error: {e}")


if __name__ == "__main__":
    main_entry_point()
