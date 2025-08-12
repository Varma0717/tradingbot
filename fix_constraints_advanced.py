#!/usr/bin/env python3
"""
Advanced constraint fix that handles foreign keys properly.
"""

from app import create_app, db


def fix_constraints_advanced():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            print("=" * 60)
            print("ADVANCED TRADING BOT STATUS CONSTRAINT FIX")
            print("=" * 60)

            # Check foreign key constraints
            print("Checking foreign key constraints...")
            fk_result = conn.execute(
                db.text(
                    """
                SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'trading_bot_status' 
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """
                )
            ).fetchall()

            print("Foreign keys on trading_bot_status:")
            for fk in fk_result:
                print(f"  {fk[0]}: {fk[1]} -> {fk[2]}.{fk[3]}")

            # Check all indexes
            result = conn.execute(db.text("SHOW INDEX FROM trading_bot_status"))
            indexes = []
            for row in result:
                indexes.append(
                    {"name": row[2], "column": row[4], "unique": row[1] == 0}
                )

            print(f"\nCurrent indexes:")
            for idx in indexes:
                unique_str = "(UNIQUE)" if idx["unique"] else ""
                print(f"  {idx['name']}: {idx['column']} {unique_str}")

            # The solution: Add composite unique constraint without touching the FK index
            has_composite = any(idx["name"] == "uq_user_bot_type" for idx in indexes)

            if not has_composite:
                print("\nAdding composite unique constraint (user_id, bot_type)...")
                try:
                    conn.execute(
                        db.text(
                            """
                        ALTER TABLE trading_bot_status 
                        ADD UNIQUE INDEX uq_user_bot_type (user_id, bot_type)
                    """
                        )
                    )
                    conn.commit()
                    print("✓ Added composite constraint")

                    # Verify
                    result = conn.execute(db.text("SHOW INDEX FROM trading_bot_status"))
                    new_indexes = [row[2] for row in result]
                    print(f"New indexes: {new_indexes}")

                    if "uq_user_bot_type" in new_indexes:
                        print("\n✅ SUCCESS!")
                        print(
                            "The composite unique constraint allows multiple bot types per user."
                        )
                        print("The old user_id index remains for foreign key purposes.")
                        print("You can now start both stock and crypto bots!")
                        return True

                except Exception as e:
                    print(f"❌ Error adding constraint: {e}")
                    # Check if constraint already exists with different name
                    print("Checking if constraint already exists...")
                    return False
            else:
                print("✅ Composite constraint already exists!")
                return True


if __name__ == "__main__":
    success = fix_constraints_advanced()
    if not success:
        print("\n💡 Alternative: The constraint might already work!")
        print("Try starting both bots to see if the issue is resolved.")
