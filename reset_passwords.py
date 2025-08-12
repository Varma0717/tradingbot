#!/usr/bin/env python3
"""
Reset user passwords with proper Werkzeug hashing
"""

from app import create_app, db
from app.models import User


def reset_passwords():
    """Reset all user passwords to 'password123' with proper hashing"""
    app = create_app()

    with app.app_context():
        print("=== Resetting User Passwords ===\n")

        users = User.query.all()

        for user in users:
            print(f"Resetting password for: {user.email}")
            user.set_password("password123")
            print(f"  New hash format: {user.password_hash[:30]}...")

        db.session.commit()
        print(f"\n✅ Successfully reset passwords for {len(users)} users!")

        # Test the passwords
        print("\n=== Testing New Passwords ===")
        for user in users:
            valid = user.check_password("password123")
            print(f"{user.email}: {'✓' if valid else '✗'}")


if __name__ == "__main__":
    reset_passwords()
