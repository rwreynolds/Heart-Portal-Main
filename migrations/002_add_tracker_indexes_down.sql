-- Rollback: Remove indexes from tracker tables
-- Created: 2025-12-31

-- Sodium Tracker indexes
DROP INDEX IF EXISTS idx_sodium_entries_user_date;
DROP INDEX IF EXISTS idx_sodium_entries_date;

-- Fluid Tracker indexes
DROP INDEX IF EXISTS idx_fluid_entries_user_date;
DROP INDEX IF EXISTS idx_fluid_entries_date;

-- Weight Tracker indexes
DROP INDEX IF EXISTS idx_weight_entries_user_date;
DROP INDEX IF EXISTS idx_weight_entries_date;

-- BP Monitor indexes
DROP INDEX IF EXISTS idx_bp_entries_user_date;
DROP INDEX IF EXISTS idx_bp_entries_date;

-- User settings indexes
DROP INDEX IF EXISTS idx_user_settings_user_id;
