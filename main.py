"""
Main entry point for the Crypto Trading Bot.
Handles command-line arguments and starts the appropriate bot mode.

Quick Start Examples:
    # Start dashboard (easiest way)
    python main.py --mode dashboard

    # Start dashboard on custom port
    python main.py --mode dashboard --port 8080

    # Paper trading
    python main.py --mode paper --strategy grid_dca

    # Live trading (be careful!)
    python main.py --mode live --strategy grid_dca
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.bot import TradingBot
from src.core.config import Config
from src.utils.logger import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Advanced Crypto Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start web dashboard (most common usage)
  python main.py --mode dashboard
  python main.py --mode dashboard --port 8080
  
  # Paper trading with strategies
  python main.py --mode paper --strategy ma_crossover --symbol BTC/USDT
  python main.py --mode paper --strategy grid_dca --symbol ETH/USDT

  # Live trading (use with caution!)
  python main.py --mode live --strategy rsi_strategy --symbol ETH/USDT --exchange binance

  # Run backtest
  python main.py --mode backtest --strategy grid_dca

  # Custom config
  python main.py --config config/custom_config.yaml --mode dashboard
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["paper", "live", "backtest", "dashboard"],
        default="paper",
        help="Trading mode (default: paper)",
    )

    parser.add_argument(
        "--strategy",
        choices=["ma_crossover", "rsi_strategy", "ml_strategy", "grid_dca"],
        default="grid_dca",
        help="Trading strategy to use (default: grid_dca)",
    )

    parser.add_argument(
        "--symbol", default="BTC/USDT", help="Trading symbol (default: BTC/USDT)"
    )

    parser.add_argument(
        "--exchange",
        choices=["binance", "coinbase", "kraken"],
        default="binance",
        help="Exchange to use (default: binance)",
    )

    parser.add_argument(
        "--timeframe",
        choices=["1m", "5m", "15m", "1h", "4h", "1d"],
        default="1h",
        help="Timeframe for analysis (default: 1h)",
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no actual trades)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--port", type=int, default=8002, help="Port for dashboard mode (default: 8002)"
    )

    return parser.parse_args()


def run_dashboard_mode(args):
    """Run dashboard mode outside async context to avoid event loop issues."""
    # Setup logging for dashboard
    setup_logging(level=args.log_level, verbose=args.verbose)
    logger = logging.getLogger(__name__)

    print("🚀 Starting Crypto Trading Bot Dashboard...")
    logger.info("Starting dashboard web interface...")

    try:
        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            print("Please create a configuration file first.")
            return

        config = Config(args.config)
        config.trading.mode = args.mode
        config.validate()
        print("✅ Configuration loaded")

        # Create trading bot instance for dashboard
        trading_bot = None
        try:
            trading_bot = TradingBot(config)
            print("✅ Trading bot created")
        except Exception as e:
            print(f"⚠️  Trading bot creation failed: {e}")
            print("Dashboard will run without bot connection")

        from src.dashboard.main import DashboardApp
        import uvicorn

        dashboard = DashboardApp(config, trading_bot)
        app = dashboard.app  # Get the FastAPI app from the dashboard instance
        print("✅ Dashboard app created")

        if trading_bot:
            print("✅ Trading bot connected to dashboard")

        print(f"\n🌐 Dashboard starting at http://127.0.0.1:{args.port}")
        print(f"📊 Access your trading dashboard in your web browser")
        print("🛑 Press Ctrl+C to stop the dashboard\n")

        logger.info(f"Dashboard starting on http://localhost:{args.port}")
        logger.info(f"Access the web interface at: http://localhost:{args.port}")

        # Run the FastAPI server (this will block)
        uvicorn.run(
            app, host="127.0.0.1", port=args.port, log_level="info", reload=False
        )
    except ImportError as e:
        print(f"❌ Dashboard dependencies not available: {e}")
        print("Please install: pip install fastapi uvicorn jinja2")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        import traceback

        traceback.print_exc()
        logger.error(f"Dashboard error: {e}", exc_info=True)
        sys.exit(1)


async def main():
    """Main function to start the trading bot."""

    # Parse command line arguments
    args = parse_arguments()

    try:
        # Setup logging
        setup_logging(level=args.log_level, verbose=args.verbose)

        logger = logging.getLogger(__name__)
        logger.info("Starting Crypto Trading Bot...")
        logger.info(f"Mode: {args.mode}")
        logger.info(f"Strategy: {args.strategy}")
        logger.info(f"Symbol: {args.symbol}")
        logger.info(f"Exchange: {args.exchange}")
        logger.info(f"Timeframe: {args.timeframe}")

        # Load configuration
        config = Config(args.config)

        # Override config with command line arguments
        config.trading.mode = args.mode
        config.trading.strategy = args.strategy
        config.trading.symbol = args.symbol
        config.trading.exchange = args.exchange
        config.trading.timeframe = args.timeframe
        config.trading.dry_run = args.dry_run

        # Validate configuration
        config.validate()

        # Create and start the trading bot for other modes
        bot = TradingBot(config)

        if args.mode == "backtest":
            # Run backtest mode
            logger.info("Running in backtest mode...")
            await bot.run_backtest()
        else:
            # Run live or paper trading
            logger.info(f"Running in {args.mode} mode...")
            await bot.start()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
        if "bot" in locals():
            await bot.stop()
        logger.info("Bot stopped successfully.")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Parse arguments first to check mode
    args = parse_arguments()

    if args.mode == "dashboard":
        # Run dashboard mode directly (not in async context)
        try:
            run_dashboard_mode(args)
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped by user")
        except Exception as e:
            print(f"❌ Dashboard fatal error: {e}")
            sys.exit(1)
    else:
        # Run other modes in async context
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nShutdown requested... exiting gracefully")
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)
