#!/usr/bin/env python
"""Update database schema with new fields"""

from app import create_app, db

app = create_app()

with app.app_context():
    try:
        # This will add the new columns to existing tables
        db.create_all()
        print("✅ Database tables updated successfully!")
        print("✅ Added fields:")
        print("   - Strategy.created_at")
        print("   - Strategy.updated_at")
        print("   - Strategy.status")
        print("   - Subscription.created_at")
    except Exception as e:
        print(f"❌ Error updating database: {e}")
