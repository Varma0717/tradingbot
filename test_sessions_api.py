#!/usr/bin/env python3
"""
Test what the automation sessions API is actually returning
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.user.routes import get_trading_sessions
from flask import Flask
from flask_login import login_user
from app.models import User

app = create_app()

with app.app_context():
    with app.test_request_context():
        print("=== Testing Automation Sessions API ===")

        # Simulate login as user 2
        user = User.query.filter_by(email="trader@trademantra.com").first()
        if user:
            login_user(user)
            print(f"Logged in as user: {user.email}")

            # Call the sessions endpoint directly
            try:
                response = get_trading_sessions()
                print(
                    f"Response status: {response.status_code if hasattr(response, 'status_code') else 'No status'}"
                )
                print(
                    f"Response data: {response.get_json() if hasattr(response, 'get_json') else response}"
                )
            except Exception as e:
                print(f"Error calling sessions endpoint: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("User not found!")
