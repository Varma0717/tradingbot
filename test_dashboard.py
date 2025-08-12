#!/usr/bin/env python3
"""
Test dashboard components for debugging
"""

from app import create_app
from app.models import User


def test_dashboard_components():
    app = create_app()

    with app.app_context():
        user = User.query.filter_by(email="test@trading.com").first()
        print(f"Testing dashboard for user: {user.username}")

        # Test portfolio manager
        try:
            from app.utils.portfolio_manager import PortfolioManager

            pm = PortfolioManager(user.id)
            portfolio_data = pm.get_comprehensive_portfolio()
            print("✅ Portfolio Manager: OK")
            print(f"   Keys: {list(portfolio_data.keys())}")
        except Exception as e:
            print(f"❌ Portfolio Manager error: {e}")

        # Test subscription enforcer
        try:
            from app.utils.subscription_enforcer import get_plan_summary

            plan = get_plan_summary(user.id)
            print("✅ Subscription Enforcer: OK")
            print(f"   Plan: {plan}")
        except Exception as e:
            print(f"❌ Subscription Enforcer error: {e}")

        # Test template rendering
        try:
            from flask import render_template_string

            template = (
                "{{ current_user.subscription_tier }} - {{ current_user.ai_enabled }}"
            )

            with app.test_request_context():
                from flask_login import login_user

                login_user(user)
                result = render_template_string(template)
                print(f"✅ Template rendering: {result}")
        except Exception as e:
            print(f"❌ Template rendering error: {e}")


if __name__ == "__main__":
    test_dashboard_components()
