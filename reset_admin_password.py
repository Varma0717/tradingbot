#!/usr/bin/env python3
"""
Script to reset admin password to a known value
"""

from app import create_app, db
from app.models import User


def reset_admin_password():
    app = create_app()
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(email="admin@trademantra.com").first()

        if admin:
            # Set password to admin123
            admin.set_password("admin123")
            db.session.commit()
            print(f"✅ Admin password reset successfully!")
            print(f"📧 Email: admin@trademantra.com")
            print(f"🔑 Password: admin123")
        else:
            print("❌ Admin user not found")

        # Also reset user password
        user = User.query.filter_by(email="user@trademantra.com").first()
        if user:
            user.set_password("user123")
            db.session.commit()
            print(f"✅ Regular user password reset successfully!")
            print(f"📧 Email: user@trademantra.com")
            print(f"🔑 Password: user123")


if __name__ == "__main__":
    reset_admin_password()
