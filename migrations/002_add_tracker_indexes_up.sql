-- Migration: Add indexes to tracker tables for better query performance
-- Created: 2025-12-31
-- Applied to: sodium, fluid, weight, bp databases

-- Sodium Tracker indexes
CREATE INDEX IF NOT EXISTS idx_sodium_entries_user_date ON sodium_entries(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_sodium_entries_date ON sodium_entries(date DESC);

-- Fluid Tracker indexes
CREATE INDEX IF NOT EXISTS idx_fluid_entries_user_date ON fluid_entries(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_fluid_entries_date ON fluid_entries(date DESC);

-- Weight Tracker indexes
CREATE INDEX IF NOT EXISTS idx_weight_entries_user_date ON weight_entries(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_weight_entries_date ON weight_entries(date DESC);

-- BP Monitor indexes
CREATE INDEX IF NOT EXISTS idx_bp_entries_user_date ON bp_entries(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_bp_entries_date ON bp_entries(date DESC);

-- User settings indexes (common across trackers)
-- Note: Apply to each tracker database separately
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
