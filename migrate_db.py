#!/usr/bin/env python
"""Add missing columns to existing database tables"""

from app import create_app, db
from datetime import datetime

app = create_app()

with app.app_context():
    try:
        # Add missing columns to strategies table
        db.engine.execute(
            'ALTER TABLE strategies ADD COLUMN status VARCHAR(20) DEFAULT "pending"'
        )
        print("✅ Added strategies.status column")
    except Exception as e:
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            print("ℹ️ strategies.status column already exists")
        else:
            print(f"❌ Error adding strategies.status: {e}")

    try:
        db.engine.execute(
            "ALTER TABLE strategies ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        )
        print("✅ Added strategies.created_at column")
    except Exception as e:
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            print("ℹ️ strategies.created_at column already exists")
        else:
            print(f"❌ Error adding strategies.created_at: {e}")

    try:
        db.engine.execute(
            "ALTER TABLE strategies ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        )
        print("✅ Added strategies.updated_at column")
    except Exception as e:
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            print("ℹ️ strategies.updated_at column already exists")
        else:
            print(f"❌ Error adding strategies.updated_at: {e}")

    try:
        # Add missing columns to subscriptions table
        db.engine.execute(
            "ALTER TABLE subscriptions ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        )
        print("✅ Added subscriptions.created_at column")
    except Exception as e:
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            print("ℹ️ subscriptions.created_at column already exists")
        else:
            print(f"❌ Error adding subscriptions.created_at: {e}")

    print("\n🔄 Testing database queries...")

    # Test the queries that were failing
    try:
        from app.models import Strategy, Subscription

        strategies = Strategy.query.order_by(Strategy.created_at.desc()).all()
        print(f"✅ Successfully queried {len(strategies)} strategies")

        subscriptions = Subscription.query.order_by(
            Subscription.created_at.desc()
        ).all()
        print(f"✅ Successfully queried {len(subscriptions)} subscriptions")

        print("\n🎉 Database migration completed successfully!")

    except Exception as e:
        print(f"❌ Error testing queries: {e}")
