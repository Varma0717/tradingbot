#!/usr/bin/env python3
"""
Check users in database
"""

from app import create_app, db
from app.models import User


def check_users():
    """Check all users in database"""

    app = create_app()

    with app.app_context():
        users = User.query.all()
        print(f"Total users: {len(users)}")

        for user in users:
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Password hash: {user.password_hash[:20]}...")
            print("---")


if __name__ == "__main__":
    check_users()
