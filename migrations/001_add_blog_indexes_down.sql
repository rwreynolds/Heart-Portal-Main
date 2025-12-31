-- Rollback: Remove indexes from blog_posts table
-- Created: 2025-12-31

DROP INDEX IF EXISTS idx_blog_posts_slug;
DROP INDEX IF EXISTS idx_blog_posts_status;
DROP INDEX IF EXISTS idx_blog_posts_author_id;
DROP INDEX IF EXISTS idx_blog_posts_published_at;
DROP INDEX IF EXISTS idx_blog_posts_visibility;
DROP INDEX IF EXISTS idx_blog_posts_public_published;
