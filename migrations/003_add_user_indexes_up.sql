-- Migration: Add indexes to users and sessions tables
-- Created: 2025-12-31
-- Applied to: heart_portal_users, heart_portal_staging_users

-- User sessions indexes for faster session lookups
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- Composite index for active session lookups
CREATE INDEX IF NOT EXISTS idx_user_sessions_active
ON user_sessions(session_token, expires_at)
WHERE expires_at > NOW();
