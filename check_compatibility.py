#!/usr/bin/env python3
"""
Quick test script to check Flask-Login and Werkzeug compatibility
"""

try:
    from werkzeug.urls import url_decode

    print("✅ url_decode available in werkzeug.urls")
except ImportError:
    print("❌ url_decode not available in werkzeug.urls")
    try:
        from werkzeug.datastructures import url_decode

        print("✅ url_decode found in werkzeug.datastructures")
    except ImportError:
        print("❌ url_decode not found in werkzeug.datastructures either")

# Check Werkzeug version
import werkzeug

print(f"Werkzeug version: {werkzeug.__version__}")

# Check Flask-Login version
import flask_login

print(f"Flask-Login version: {flask_login.__version__}")

# Try importing Flask-Login
try:
    from flask_login import LoginManager

    print("✅ Flask-Login imports successfully")
except ImportError as e:
    print(f"❌ Flask-Login import error: {e}")
