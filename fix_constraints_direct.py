#!/usr/bin/env python3
"""
Direct script to fix the trading_bot_status constraint issue.
This bypasses Alembic and applies the fix directly.
"""

from app import create_app, db


def fix_constraints():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            print("=" * 60)
            print("FIXING TRADING BOT STATUS CONSTRAINTS")
            print("=" * 60)

            # Check current state
            result = conn.execute(db.text("SHOW INDEX FROM trading_bot_status"))
            indexes = {row[2] for row in result}
            print(f"Current indexes: {indexes}")

            # Check for duplicate user records
            duplicates = conn.execute(
                db.text(
                    """
                SELECT user_id, COUNT(*) as count 
                FROM trading_bot_status 
                GROUP BY user_id 
                HAVING COUNT(*) > 1
            """
                )
            ).fetchall()

            if duplicates:
                print(
                    f"Found duplicates for user_ids: {[row[0] for row in duplicates]}"
                )
                for user_id, count in duplicates:
                    print(f"Fixing user_id {user_id} ({count} records)...")

                    # Get all records for this user
                    records = conn.execute(
                        db.text(
                            """
                        SELECT id, bot_type FROM trading_bot_status 
                        WHERE user_id = :user_id 
                        ORDER BY id
                    """
                        ),
                        {"user_id": user_id},
                    ).fetchall()

                    # Keep first as stock, second as crypto, delete rest
                    for i, record in enumerate(records):
                        if i == 0:
                            conn.execute(
                                db.text(
                                    """
                                UPDATE trading_bot_status 
                                SET bot_type = 'stock' 
                                WHERE id = :id
                            """
                                ),
                                {"id": record[0]},
                            )
                        elif i == 1:
                            conn.execute(
                                db.text(
                                    """
                                UPDATE trading_bot_status 
                                SET bot_type = 'crypto' 
                                WHERE id = :id
                            """
                                ),
                                {"id": record[0]},
                            )
                        else:
                            conn.execute(
                                db.text(
                                    """
                                DELETE FROM trading_bot_status 
                                WHERE id = :id
                            """
                                ),
                                {"id": record[0]},
                            )

                    conn.commit()

            # Drop old unique constraint if it exists
            if "user_id" in indexes:
                print("Dropping old user_id unique constraint...")
                conn.execute(
                    db.text("ALTER TABLE trading_bot_status DROP INDEX user_id")
                )
                conn.commit()
                print("✓ Dropped old constraint")

            # Add new composite constraint if it doesn't exist
            if "uq_user_bot_type" not in indexes:
                print("Adding composite unique constraint (user_id, bot_type)...")
                conn.execute(
                    db.text(
                        """
                    ALTER TABLE trading_bot_status 
                    ADD UNIQUE INDEX uq_user_bot_type (user_id, bot_type)
                """
                    )
                )
                conn.commit()
                print("✓ Added new constraint")

            # Verify results
            result = conn.execute(db.text("SHOW INDEX FROM trading_bot_status"))
            new_indexes = {row[2] for row in result}
            print(f"\nFinal indexes: {new_indexes}")

            # Show current records
            records = conn.execute(
                db.text(
                    """
                SELECT user_id, bot_type, is_running 
                FROM trading_bot_status 
                ORDER BY user_id, bot_type
            """
                )
            ).fetchall()

            print(f"\nCurrent records ({len(records)}):")
            for r in records:
                print(f"  user_id={r[0]}, bot_type={r[1]}, is_running={r[2]}")

            if "user_id" not in new_indexes and "uq_user_bot_type" in new_indexes:
                print("\n✅ SUCCESS: Constraints fixed!")
                print("You can now start both stock and crypto bots.")
                return True
            else:
                print("\n❌ ERROR: Constraints not properly fixed")
                return False


if __name__ == "__main__":
    success = fix_constraints()
    if success:
        print("\n🎉 Migration completed successfully!")
    else:
        print("\n💥 Migration failed!")
