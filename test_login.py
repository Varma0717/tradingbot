#!/usr/bin/env py        # Test each user with updated credentials
        test_users = [
            ("admin@trademantra.com", "password123"),
            ("trader@trademantra.com", "password123"), 
            ("test@trading.com", "password123")
        ]
"""
Test script to verify login functionality and test credentials
"""

from app import create_app, db
from app.models import User
from werkzeug.security import check_password_hash


def test_credentials():
    """Test if our enhanced user credentials work"""
    app = create_app()

    with app.app_context():
        print("=== Testing Enhanced User Credentials ===\n")

        # Test each user
        test_users = [
            ("alice.pro@example.com", "protrader123"),
            ("bob.premium@example.com", "premium456"),
            ("charlie.basic@example.com", "basic789"),
        ]

        for email, password in test_users:
            print(f"Testing: {email}")
            user = User.query.filter_by(email=email).first()

            if user:
                password_valid = user.check_password(password)
                print(f"  User found: ✓")
                print(f"  Password valid: {'✓' if password_valid else '✗'}")
                print(f"  Subscription: {user.subscription_tier}")
                print(f"  AI Enabled: {user.ai_enabled}")
                print()
            else:
                print(f"  User not found: ✗")
                print()

        print("=== Testing CSRF Token Generation ===")
        from flask_wtf.csrf import generate_csrf

        try:
            with app.test_request_context():
                token = generate_csrf()
                print(f"CSRF token generated: ✓ (length: {len(token)})")
        except Exception as e:
            print(f"CSRF token generation failed: ✗ ({e})")


if __name__ == "__main__":
    test_credentials()
