"""
API Blueprint Registration
"""
from flask import Blueprint
from .subscriptions import subscription_bp
from .marketplace import marketplace_bp
from .social import social_bp
from .analytics import analytics_bp

def register_api_blueprints(app):
    """Register all API blueprints with the Flask app"""
    app.register_blueprint(subscription_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(analytics_bp)
