import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from .config import config

# Enhanced Features Import
from .utils.enhanced_subscription_manager import EnhancedSubscriptionManager

from .strategies.ai_trading_engine import AITradingEngine
from .marketplace.strategy_marketplace import StrategyMarketplace
from .social.copy_trading_platform import SocialTradingPlatform
from .compliance.risk_management import RiskManager
from .analytics.reporting_engine import ReportGenerator

from .utils.logger import setup_logging

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
login_manager.login_view = (
    "auth.login"  # Redirect to login page if user is not authenticated
)


def create_app(config_name="default"):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    db.init_app(app)

    # Initialize enhanced feature managers
    app.subscription_manager = EnhancedSubscriptionManager()
    app.ai_engine = AITradingEngine()
    app.marketplace = StrategyMarketplace()
    app.copy_trading = SocialTradingPlatform()
    app.risk_manager = RiskManager()
    app.reporting_engine = ReportGenerator()

    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # Setup logging
    setup_logging(app)
    app.logger.info("Trading Bot application starting up...")

    # Add CSRF error handler
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.warning(f"CSRF error: {e.description}")
        from flask import flash, redirect, url_for, request

        flash("Your session has expired. Please try again.", "warning")
        # If it's a login attempt, redirect to login page
        if request.endpoint == "auth.login":
            return redirect(url_for("auth.login"))
        return redirect(url_for("pages.index"))

    # Add security headers middleware
    from .utils.security import add_security_headers

    @app.after_request
    def security_headers(response):
        return add_security_headers(response)

    # Register Blueprints
    from .auth.routes import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .user.routes import user as user_blueprint

    app.register_blueprint(user_blueprint, url_prefix="/user")

    from .admin.routes import admin as admin_blueprint

    app.register_blueprint(admin_blueprint, url_prefix="/admin")

    from .payments.routes import payments as payments_blueprint

    app.register_blueprint(payments_blueprint, url_prefix="/payments")

    from .pages.routes import pages as pages_blueprint

    app.register_blueprint(pages_blueprint)

    from .payments.razorpay_webhook import webhook as webhook_blueprint

    app.register_blueprint(webhook_blueprint, url_prefix="/webhook")

    # Register enhanced API blueprints
    from .api import register_api_blueprints

    register_api_blueprints(app)

    # Root route
    @app.route("/")
    def index():
        return render_template("index.html")

    # Scheduler setup
    if app.config.get("SCHEDULER_ENABLED", True):
        scheduler = BackgroundScheduler()
        # Add strategy execution job
        from .strategies.engine import run_all_strategies

        scheduler.add_job(
            func=run_all_strategies, trigger="interval", minutes=5, args=[app]
        )
        scheduler.start()
        app.logger.info("Scheduler started - strategies will run every 5 minutes.")

    # Initialize bot manager and restore active bots
    with app.app_context():
        from .automation.bot_manager import BotManager, start_heartbeat_monitor

        # Restore any active bots from database
        try:
            BotManager.restore_active_bots()
            app.logger.info("Bot manager initialized and active bots restored.")
        except Exception as e:
            app.logger.error(f"Failed to restore active bots during startup: {e}")
            app.logger.info("Bot manager initialized without restoring bots.")

        # Start heartbeat monitor with app context
        try:
            start_heartbeat_monitor(app)
        except Exception as e:
            app.logger.error(f"Failed to start heartbeat monitor: {e}")

        app.logger.info("Bot manager initialization completed.")

    return app
