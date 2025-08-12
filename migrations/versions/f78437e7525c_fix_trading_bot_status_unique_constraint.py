"""fix_trading_bot_status_unique_constraint

Fix TradingBotStatus table constraints:
- Drop old unique constraint on user_id
- Add composite unique constraint on (user_id, bot_type)
- Handle potential data conflicts by updating duplicate rows

Revision ID: f78437e7525c
Revises: 5d515913ef52
Create Date: 2025-08-11 09:58:47.927228

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "f78437e7525c"
down_revision = "5d515913ef52"
branch_labels = None
depends_on = None


def upgrade():
    """Apply the migration to fix trading_bot_status constraints."""
    connection = op.get_bind()

    # First, check what indexes exist on trading_bot_status
    print("Checking existing indexes on trading_bot_status table...")

    try:
        # Get existing indexes
        result = connection.execute(text("SHOW INDEX FROM trading_bot_status"))
        existing_indexes = {row[2] for row in result}  # Key_name is at index 2
        print(f"Existing indexes: {existing_indexes}")

        # Handle potential data conflicts before changing constraints
        print("Checking for duplicate user_id entries...")
        duplicates = connection.execute(
            text(
                """
            SELECT user_id, COUNT(*) as count 
            FROM trading_bot_status 
            GROUP BY user_id 
            HAVING COUNT(*) > 1
        """
            )
        ).fetchall()

        if duplicates:
            print(f"Found duplicate user_ids: {[row[0] for row in duplicates]}")

            # For each duplicate user_id, ensure we have separate records for stock and crypto
            for user_id, count in duplicates:
                print(f"Fixing duplicates for user_id {user_id}...")

                # Get all records for this user
                records = connection.execute(
                    text(
                        """
                    SELECT id, bot_type FROM trading_bot_status 
                    WHERE user_id = :user_id 
                    ORDER BY id
                """
                    ),
                    {"user_id": user_id},
                ).fetchall()

                if len(records) > 1:
                    # Keep the first record as 'stock', update others to 'crypto' or delete
                    stock_record = records[0]

                    # Update first record to be stock type if not already
                    connection.execute(
                        text(
                            """
                        UPDATE trading_bot_status 
                        SET bot_type = 'stock' 
                        WHERE id = :record_id
                    """
                        ),
                        {"record_id": stock_record[0]},
                    )

                    # For additional records, either convert to crypto or delete
                    for i, record in enumerate(records[1:], 1):
                        if i == 1:  # Second record becomes crypto
                            connection.execute(
                                text(
                                    """
                                UPDATE trading_bot_status 
                                SET bot_type = 'crypto' 
                                WHERE id = :record_id
                            """
                                ),
                                {"record_id": record[0]},
                            )
                        else:  # Delete any additional records
                            connection.execute(
                                text(
                                    """
                                DELETE FROM trading_bot_status 
                                WHERE id = :record_id
                            """
                                ),
                                {"record_id": record[0]},
                            )

        # Drop the old unique constraint on user_id if it exists
        if "user_id" in existing_indexes:
            print("Dropping old unique constraint on user_id...")
            connection.execute(
                text("ALTER TABLE trading_bot_status DROP INDEX user_id")
            )

        # Add the composite unique constraint if it doesn't exist
        if "uq_user_bot_type" not in existing_indexes:
            print("Adding composite unique constraint (user_id, bot_type)...")
            connection.execute(
                text(
                    """
                ALTER TABLE trading_bot_status 
                ADD UNIQUE INDEX uq_user_bot_type (user_id, bot_type)
            """
                )
            )

        # Verify the changes
        result = connection.execute(text("SHOW INDEX FROM trading_bot_status"))
        new_indexes = {row[2] for row in result}
        print(f"New indexes after migration: {new_indexes}")

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise


def downgrade():
    """Rollback the migration - restore original constraints."""
    connection = op.get_bind()

    print("Rolling back trading_bot_status constraint changes...")

    try:
        # Check existing indexes
        result = connection.execute(text("SHOW INDEX FROM trading_bot_status"))
        existing_indexes = {row[2] for row in result}

        # Drop the composite unique constraint if it exists
        if "uq_user_bot_type" in existing_indexes:
            print("Dropping composite unique constraint...")
            connection.execute(
                text("ALTER TABLE trading_bot_status DROP INDEX uq_user_bot_type")
            )

        # Add back the unique constraint on user_id if it doesn't exist
        if "user_id" not in existing_indexes:
            print("Adding back unique constraint on user_id...")
            # Note: This might fail if there are now multiple bot types per user
            # In that case, we'd need to manually clean up the data first
            try:
                connection.execute(
                    text(
                        """
                    ALTER TABLE trading_bot_status 
                    ADD UNIQUE INDEX user_id (user_id)
                """
                    )
                )
            except Exception as e:
                print(f"Warning: Could not restore user_id unique constraint: {e}")
                print(
                    "Manual cleanup may be required - multiple bot types per user exist"
                )

        print("Rollback completed!")

    except Exception as e:
        print(f"Rollback failed: {e}")
        raise
