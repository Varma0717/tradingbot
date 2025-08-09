import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from .config import config
from .utils.logger import setup_logging

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Redirect to login page if user is not authenticated

def create_app(config_name='default'):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Setup logging
    setup_logging(app)
    app.logger.info("Trading Bot application starting up...")

    # Register Blueprints
    from .auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .user.routes import user as user_blueprint
    app.register_blueprint(user_blueprint)

    from .admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from .payments.routes import payments as payments_blueprint
    app.register_blueprint(payments_blueprint, url_prefix='/payments')

    from .payments.razorpay_webhook import webhook as webhook_blueprint
    app.register_blueprint(webhook_blueprint, url_prefix='/webhook')

    # Root route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Scheduler setup
    if app.config.get('SCHEDULER_ENABLED', True):
        scheduler = BackgroundScheduler()
        # TODO: Add jobs to the scheduler
        # from .strategies.engine import run_all_strategies
        # scheduler.add_job(func=run_all_strategies, trigger="interval", minutes=5, args=[app])
        scheduler.start()
        app.logger.info("Scheduler started.")

    return app