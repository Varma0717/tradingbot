#!/usr/bin/env python
"""Fix subscriptions table - Add created_at column without default"""

from app import create_app, db
from datetime import datetime
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add created_at column to subscriptions table without default
        with db.engine.connect() as conn:
            conn.execute(
                text("ALTER TABLE subscriptions ADD COLUMN created_at DATETIME")
            )
            conn.commit()
        print("✅ Added subscriptions.created_at column")
    except Exception as e:
        if (
            "duplicate column name" in str(e).lower()
            or "already exists" in str(e).lower()
        ):
            print("ℹ️ subscriptions.created_at column already exists")
        else:
            print(f"❌ Error adding subscriptions.created_at: {e}")

    try:
        # Update all existing subscriptions to have created_at = start_date
        with db.engine.connect() as conn:
            conn.execute(
                text(
                    "UPDATE subscriptions SET created_at = start_date WHERE created_at IS NULL"
                )
            )
            conn.commit()
        print("✅ Updated existing subscriptions with created_at values")
    except Exception as e:
        print(f"❌ Error updating subscriptions: {e}")

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
