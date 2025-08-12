# Trading Bot Status Migration

This migration fixes the database constraint issue that prevents running both stock and crypto bots simultaneously.

## Problem

The `trading_bot_status` table had a unique constraint on `user_id` only, which meant each user could only have one bot status record. This caused "Duplicate entry for key 'user_id'" errors when trying to start both stock and crypto bots.

## Solution

The migration:

1. **Data Cleanup**: Identifies duplicate `user_id` entries and assigns proper `bot_type` values
2. **Constraint Update**: Removes old unique constraint on `user_id`
3. **New Constraint**: Adds composite unique constraint on `(user_id, bot_type)`

This allows each user to have separate status records for stock and crypto bots.

## Running the Migration

### Option 1: Interactive Script (Recommended)

```bash
cd C:\xampp\htdocs\application
python run_migration.py
```

### Option 2: Flask-Migrate Command

```bash
cd C:\xampp\htdocs\application
python -m flask db upgrade
```

### Option 3: Manual SQL (Advanced)

```sql
-- Backup first!
-- Check existing constraints
SHOW INDEX FROM trading_bot_status;

-- Fix duplicate data (if any)
-- [Script handles this automatically]

-- Drop old constraint
ALTER TABLE trading_bot_status DROP INDEX user_id;

-- Add new composite constraint  
ALTER TABLE trading_bot_status ADD UNIQUE INDEX uq_user_bot_type (user_id, bot_type);
```

## Verification

After migration, verify with:

```sql
SHOW INDEX FROM trading_bot_status;
SELECT user_id, bot_type, is_running FROM trading_bot_status ORDER BY user_id, bot_type;
```

Expected results:

- Index `uq_user_bot_type` should exist
- Old `user_id` index should be gone  
- Each user can have up to 2 records (one for 'stock', one for 'crypto')

## Rollback

If needed, rollback with:

```bash
python -m flask db downgrade
```

**Warning**: Rollback may fail if you now have multiple bot types per user (which is the intended behavior after this migration).

## Testing

After migration:

1. Start stock bot → Should create/update record with `bot_type='stock'`
2. Start crypto bot → Should create/update record with `bot_type='crypto'`  
3. Both bots should run simultaneously without constraint errors

## Files Modified

- `migrations/versions/f78437e7525c_fix_trading_bot_status_unique_constraint.py` - Migration script
- `run_migration.py` - Interactive migration runner
- Database schema: `trading_bot_status` table constraints
