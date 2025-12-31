-- Migration: Add indexes to blog_posts table for better query performance
-- Created: 2025-12-31
-- Applied to: heart_portal_blog, heart_portal_staging_blog

-- Index on slug for fast lookups by URL
CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);

-- Index on status for filtering drafts/published/pending
CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);

-- Index on author_id for user's post lookups
CREATE INDEX IF NOT EXISTS idx_blog_posts_author_id ON blog_posts(author_id);

-- Index on published_at for chronological sorting
CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at ON blog_posts(published_at);

-- Index on visibility for public/private filtering
CREATE INDEX IF NOT EXISTS idx_blog_posts_visibility ON blog_posts(visibility);

-- Composite index for common query pattern (status + visibility + published_at)
CREATE INDEX IF NOT EXISTS idx_blog_posts_public_published
ON blog_posts(status, visibility, published_at DESC)
WHERE status = 'published' AND visibility = 'public';
