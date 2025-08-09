"""
Security utilities and middleware for the Flask application.
"""

from flask import request, abort
import time
from functools import wraps


def add_security_headers(response):
    """Add security headers to all responses."""
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self';"
    )

    # X-Frame-Options
    response.headers["X-Frame-Options"] = "DENY"

    # X-Content-Type-Options
    response.headers["X-Content-Type-Options"] = "nosniff"

    # X-XSS-Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Strict-Transport-Security (only for HTTPS)
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )

    return response


def validate_user_agent(f):
    """Decorator to validate user agent and block suspicious requests."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_agent = request.headers.get("User-Agent", "").lower()

        # Block common bot/scanner patterns
        suspicious_patterns = [
            "sqlmap",
            "nikto",
            "nessus",
            "openvas",
            "burp",
            "zap",
            "masscan",
            "nmap",
            "dirb",
            "dirbuster",
            "gobuster",
            "wfuzz",
            "hydra",
            "metasploit",
        ]

        for pattern in suspicious_patterns:
            if pattern in user_agent:
                abort(403)  # Forbidden

        # Require a user agent header
        if not request.headers.get("User-Agent"):
            abort(400)  # Bad Request

        return f(*args, **kwargs)

    return decorated_function


def require_api_key(f):
    """Decorator to require API key for API endpoints (future use)."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, just check if user is authenticated
        # In production, implement proper API key validation
        if not request.headers.get("Authorization") and "/api/" in request.path:
            # For authenticated users, allow access
            pass
        return f(*args, **kwargs)

    return decorated_function


class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded."""

    pass


def log_security_event(event_type, details):
    """Log security-related events."""
    from flask import current_app

    current_app.logger.warning(f"Security Event - {event_type}: {details}")


def validate_input_length(max_length=1000):
    """Decorator to validate input length for forms."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ["POST", "PUT", "PATCH"]:
                # Check if any form field exceeds max length
                for key, value in request.form.items():
                    if isinstance(value, str) and len(value) > max_length:
                        log_security_event(
                            "INPUT_TOO_LONG", f"Field {key} length: {len(value)}"
                        )
                        abort(413)  # Payload Too Large

                # Check JSON payload size
                if request.is_json:
                    json_data = request.get_json()
                    if json_data:
                        json_str = str(json_data)
                        if len(json_str) > max_length * 2:  # Allow larger JSON
                            log_security_event(
                                "JSON_TOO_LARGE", f"JSON size: {len(json_str)}"
                            )
                            abort(413)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def check_honeypot():
    """Check for honeypot field in forms to catch bots."""
    honeypot = request.form.get("website")  # Hidden field that should remain empty
    if honeypot:
        log_security_event("HONEYPOT_TRIGGERED", f"Value: {honeypot}")
        time.sleep(2)  # Add delay for bots
        abort(403)
