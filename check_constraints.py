#!/usr/bin/env python3
from app import create_app, db

app = create_app()
with app.app_context():
    # Check indexes
    with db.engine.connect() as conn:
        result = conn.execute(db.text("SHOW INDEX FROM trading_bot_status"))
        indexes = [row[2] for row in result]
        print("Current indexes on trading_bot_status:")
        for idx in indexes:
            print(f"  - {idx}")

        # Check for the constraint we want
        has_old_constraint = "user_id" in indexes
        has_new_constraint = "uq_user_bot_type" in indexes

        print(f"\nConstraint status:")
        print(
            f"  Old user_id unique constraint: {'YES' if has_old_constraint else 'NO'}"
        )
        print(
            f"  New (user_id, bot_type) constraint: {'YES' if has_new_constraint else 'NO'}"
        )

        # Check current data
        records = conn.execute(
            db.text("SELECT user_id, bot_type, is_running FROM trading_bot_status")
        ).fetchall()
        print(f"\nCurrent records ({len(records)}):")
        for r in records:
            print(f"  user_id={r[0]}, bot_type={r[1]}, is_running={r[2]}")

        if has_old_constraint and not has_new_constraint:
            print("\n❌ PROBLEM: Still has old constraint - migration needed!")
        elif not has_old_constraint and has_new_constraint:
            print("\n✅ GOOD: Constraints are correct!")
        else:
            print("\n⚠️  MIXED: Constraint state is unclear")
