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
import os
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Create necessary directories
def ensure_directories():
    """Ensure all necessary directories exist."""
    dirs = ["logs", "config", "data", "src/core", "src/dashboard", "src/utils"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

# Setup basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/main.log', mode='a', encoding='utf-8') if Path('logs').exists() else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

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
        default="dashboard",
        help="Trading mode (default: dashboard)",
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
        "--port", type=int, default=8000, help="Port for dashboard mode (default: 8000)"
    )

    parser.add_argument(
        "--host", default="127.0.0.1", help="Host for dashboard mode (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--no-browser", action="store_true", help="Don't open browser automatically"
    )

    return parser.parse_args()

def create_default_config(config_path: Path):
    """Create a default configuration file if it doesn't exist."""
    default_config = {
        'trading': {
            'mode': 'paper',
            'strategy': 'grid_dca',
            'symbol': 'BTC/USDT',
            'exchange': 'binance',
            'timeframe': '1h',
            'dry_run': True,
            'amount': 100.0,
            'risk_percentage': 1.0
        },
        'exchanges': {
            'binance': {
                'name': 'binance',
                'api_key': '',
                'secret_key': '',
                'sandbox': True,
                'rate_limit': 10,
                'timeout': 30
            }
        },
        'strategies': {
            'grid_dca': {
                'grid_levels': 10,
                'grid_spacing': 0.01,
                'base_order_size': 10.0,
                'safety_order_size': 20.0,
                'max_safety_orders': 5
            }
        },
        'risk_management': {
            'max_position_size': 1000.0,
            'stop_loss_percentage': 5.0,
            'take_profit_percentage': 10.0,
            'max_daily_loss': 100.0
        },
        'dashboard': {
            'port': 8000,
            'host': '127.0.0.1',
            'debug': False
        }
    }
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"✅ Created default configuration file: {config_path}")

def run_dashboard_mode(args):
    """Run dashboard mode outside async context to avoid event loop issues."""
    logger.info("🚀 Starting Crypto Trading Bot Dashboard...")
    
    if setup_logging:
        setup_logging(level=args.log_level, verbose=args.verbose)
    
    try:
        # Check if dashboard is available
        if DashboardApp is None:
            print("❌ Dashboard not available. Missing dependencies.")
            print("Please install: pip install fastapi uvicorn jinja2")
            return
        
        # Load or create configuration
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"⚠️ Configuration file not found: {config_path}")
            print("Creating default configuration...")
            create_default_config(config_path)
        
        config = None
        if Config:
            try:
                config = Config(args.config)
                config.trading.mode = args.mode
                if hasattr(config, 'validate'):
                    config.validate()
                print("✅ Configuration loaded successfully")
            except Exception as e:
                print(f"⚠️ Configuration validation failed: {e}")
                print("Using minimal configuration...")
        
        # Create trading bot instance for dashboard
        trading_bot = None
        if TradingBot and config:
            try:
                trading_bot = TradingBot(config)
                print("✅ Trading bot created and connected")
            except Exception as e:
                print(f"⚠️ Trading bot creation failed: {e}")
                print("Dashboard will run in view-only mode")
        
        # Create dashboard app
        dashboard = DashboardApp(config, trading_bot)
        app = dashboard.app
        print("✅ Dashboard application created")
        
        print(f"\n🌐 Dashboard starting at http://{args.host}:{args.port}")
        print(f"📊 Access your trading dashboard in your web browser")
        print(f"🔗 Direct link: http://{args.host}:{args.port}")
        print("🛑 Press Ctrl+C to stop the dashboard\n")
        
        # Import uvicorn here to avoid issues if not installed
        try:
            import uvicorn
            
            # Run the FastAPI server
            uvicorn.run(
                app, 
                host=args.host, 
                port=args.port, 
                log_level="info" if args.verbose else "warning",
                reload=False,
                access_log=args.verbose
            )
        except ImportError:
            print("❌ uvicorn not installed. Please install: pip install uvicorn")
            return
            
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return

async def main(args):
    """Main function to start the trading bot."""
    
    if setup_logging:
        setup_logging(level=args.log_level, verbose=args.verbose)
    
    logger.info("🤖 Starting Crypto Trading Bot...")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Strategy: {args.strategy}")
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Exchange: {args.exchange}")
    logger.info(f"Timeframe: {args.timeframe}")
    
    try:
        # Check if required components are available
        if Config is None:
            logger.error("❌ Configuration system not available")
            print("❌ Core configuration module not found")
            return
        
        if TradingBot is None:
            logger.error("❌ Trading bot not available")
            print("❌ Trading bot module not found")
            return
        
        # Load or create configuration
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"⚠️ Configuration file not found: {config_path}")
            print("Creating default configuration...")
            create_default_config(config_path)
        
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
        if hasattr(config, 'validate'):
            config.validate()
        
        print("✅ Configuration loaded and validated")
        
        # Create and start the trading bot
        bot = TradingBot(config)
        print("✅ Trading bot created")
        
        if args.mode == "backtest":
            logger.info("📊 Running in backtest mode...")
            print("📊 Starting backtest...")
            if hasattr(bot, 'run_backtest'):
                await bot.run_backtest()
            else:
                print("❌ Backtest mode not implemented")
        else:
            logger.info(f"🔄 Running in {args.mode} mode...")
            print(f"🔄 Starting {args.mode} trading...")
            await bot.start()
    
    except KeyboardInterrupt:
        logger.info("⏹️ Received shutdown signal...")
        print("\n⏹️ Shutting down bot...")
        if "bot" in locals() and hasattr(bot, 'stop'):
            await bot.stop()
        logger.info("✅ Bot stopped successfully")
        print("✅ Bot stopped successfully")
    
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

def main_entry_point():
    """Main entry point with comprehensive error handling."""
    
    # Ensure directories exist
    ensure_directories()
    
    # Import required modules
    safe_import_and_setup()
    
    # Parse arguments
    try:
        args = parse_arguments()
    except Exception as e:
        print(f"❌ Error parsing arguments: {e}")
        sys.exit(1)
    
    print("� Crypto Trading Bot Starting...")
    print(f"📋 Mode: {args.mode}")
    
    if args.mode == "dashboard":
        # Run dashboard mode directly (not in async context)
        run_dashboard_mode(args)
    else:
        # Run other modes in async context
        try:
            asyncio.run(main(args))
        except KeyboardInterrupt:
            print("\n⏹️ Shutdown requested... exiting gracefully")
        except Exception as e:
            print(f"💥 Fatal error: {e}")
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    main_entry_point()
