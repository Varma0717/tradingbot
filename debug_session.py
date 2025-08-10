#!/usr/bin/env python3
"""
Check current session state
"""

from app import create_app
from flask import session

app = create_app()


@app.route("/debug/session")
def debug_session():
    """Debug current session state"""
    return {
        "session_data": dict(session),
        "user_id": session.get("_user_id", "Not logged in"),
        "is_authenticated": bool(session.get("_user_id")),
    }


if __name__ == "__main__":
    print("Visit http://127.0.0.1:5000/debug/session to check session state")
    app.run(debug=True, port=5001)
