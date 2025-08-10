#!/usr/bin/env python3
"""
Create sample users for TradeMantra application
"""

from app import create_app, db
from app.models import User
from datetime import datetime


def create_sample_users():
    """Create sample admin and regular users"""

    app = create_app()

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if users already exist
        existing_admin = User.query.filter_by(username="admin").first()
        existing_user = User.query.filter_by(username="testuser").first()

        if existing_admin:
            print("Admin user already exists")
            # Update admin email if it's wrong
            if existing_admin.email != "admin@trademantra.com":
                existing_admin.email = "admin@trademantra.com"
                print("Updated admin email to admin@trademantra.com")
        else:
            # Create admin user
            admin = User(username="admin", email="admin@trademantra.com", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            print("Created admin user: admin@trademantra.com / admin123")

        if existing_user:
            print("Test user already exists")
        else:
            # Create regular user
            user = User(username="testuser", email="user@trademantra.com", role="user")
            user.set_password("user123")
            db.session.add(user)
            print("Created test user: user@trademantra.com / user123")

        # Create additional sample users
        sample_users = [
            {
                "username": "trader1",
                "email": "trader1@example.com",
                "password": "trader123",
                "role": "user",
            },
            {
                "username": "investor1",
                "email": "investor1@example.com",
                "password": "invest123",
                "role": "user",
            },
        ]

        for user_data in sample_users:
            existing = User.query.filter_by(username=user_data["username"]).first()
            if not existing:
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    role=user_data["role"],
                )
                new_user.set_password(user_data["password"])
                db.session.add(new_user)
                print(f"Created user: {user_data['email']} / {user_data['password']}")
            else:
                print(f"User {user_data['username']} already exists")

        try:
            db.session.commit()
            print("\n✅ All sample users created successfully!")
            print("\n📋 Login Credentials:")
            print("=" * 40)
            print("Admin User:")
            print("  Email: admin@trademantra.com")
            print("  Password: admin123")
            print("\nRegular User:")
            print("  Email: user@trademantra.com")
            print("  Password: user123")
            print("\nTrader User:")
            print("  Email: trader1@example.com")
            print("  Password: trader123")
            print("\nInvestor User:")
            print("  Email: investor1@example.com")
            print("  Password: invest123")
            print("=" * 40)

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating users: {e}")


if __name__ == "__main__":
    create_sample_users()
