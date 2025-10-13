"""
Blog Database Management for Heart Portal
Handles blog posts, user authoring, and moderation workflow
Uses shared database module for SQLite/PostgreSQL support
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.database import create_db_config

# Initialize database configuration for blog
_db_config = create_db_config(
    app_name='blog',
    db_name='heart_portal_staging_blog',
    sqlite_path=os.path.join(os.path.dirname(__file__), 'database', 'blog.db')
)

# Convenience wrappers
def get_db_connection():
    """Get database connection"""
    return _db_config.get_connection()

def release_connection(conn):
    """Release database connection"""
    _db_config.release_connection(conn)

def dict_cursor(conn):
    """Get dictionary cursor"""
    return _db_config.dict_cursor(conn)

def normalize_row(row):
    """Normalize row data"""
    return _db_config.normalize_row(row)


def init_blog_database():
    """Initialize the blog database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table creation with database-appropriate syntax
    autoincrement = _db_config.get_autoincrement_syntax()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id {autoincrement},
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            visibility TEXT DEFAULT 'private',
            slug TEXT UNIQUE,
            excerpt TEXT,
            featured_image TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP,
            reviewer_id INTEGER,
            review_notes TEXT
        )
    ''')

    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_status ON blog_posts (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_visibility ON blog_posts (visibility)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_author ON blog_posts (author_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_published ON blog_posts (published_at)')

    release_connection(conn)


def create_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    import re
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:100]  # Limit length


def get_published_posts(limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get published public posts for public blog view"""
    conn = get_db_connection()

    query = '''
        SELECT id, title, excerpt, author_name, published_at, slug, tags
        FROM blog_posts
        WHERE status = ? AND visibility = ?
        ORDER BY published_at DESC
        LIMIT ? OFFSET ?
    '''

    cursor = _db_config.execute_query(conn, query, ('published', 'public', limit, offset))
    posts = [normalize_row(row) for row in cursor.fetchall()]
    release_connection(conn)
    return posts


def get_post_by_slug(slug: str) -> Optional[Dict]:
    """Get a specific published public post by slug"""
    conn = get_db_connection()

    query = '''
        SELECT * FROM blog_posts
        WHERE slug = ? AND status = ? AND visibility = ?
    '''

    cursor = _db_config.execute_query(conn, query, (slug, 'published', 'public'))
    post = cursor.fetchone()
    release_connection(conn)
    return normalize_row(post) if post else None


def get_user_posts(author_id: int, limit: int = 50) -> List[Dict]:
    """Get all posts by a specific user (private and public)"""
    conn = get_db_connection()

    query = '''
        SELECT id, title, status, visibility, excerpt, content, tags, review_notes, created_at, updated_at, slug
        FROM blog_posts
        WHERE author_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
    '''

    cursor = _db_config.execute_query(conn, query, (author_id, limit))
    posts = [normalize_row(row) for row in cursor.fetchall()]
    release_connection(conn)
    return posts


def get_pending_posts() -> List[Dict]:
    """Get posts pending review for admin interface"""
    conn = get_db_connection()

    query = '''
        SELECT id, title, author_name, excerpt, content, tags, created_at, updated_at, slug
        FROM blog_posts
        WHERE status = ? AND visibility = ?
        ORDER BY updated_at ASC
    '''

    cursor = _db_config.execute_query(conn, query, ('pending_review', 'public'))
    posts = [normalize_row(row) for row in cursor.fetchall()]
    release_connection(conn)
    return posts


def create_post(title: str, content: str, author_id: int, author_name: str,
               excerpt: str = '', visibility: str = 'private', tags: str = '') -> int:
    """Create a new blog post"""
    conn = get_db_connection()
    slug = create_slug(title)

    query = '''
        INSERT INTO blog_posts (title, content, author_id, author_name, excerpt, visibility, tags, slug, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    '''

    cursor = _db_config.execute_query(
        conn, query,
        (title, content, author_id, author_name, excerpt, visibility, tags, slug),
        use_dict_cursor=False
    )

    if _db_config.is_postgresql():
        cursor.execute('SELECT lastval()')
        post_id = cursor.fetchone()[0]
    else:
        post_id = cursor.lastrowid

    release_connection(conn)
    return post_id


def update_post(post_id: int, title: str = None, content: str = None,
               excerpt: str = None, visibility: str = None, tags: str = None) -> bool:
    """Update an existing blog post"""
    conn = get_db_connection()

    updates = []
    params = []

    if title is not None:
        updates.append('title = ?')
        params.append(title)
        updates.append('slug = ?')
        params.append(create_slug(title))
    if content is not None:
        updates.append('content = ?')
        params.append(content)
    if excerpt is not None:
        updates.append('excerpt = ?')
        params.append(excerpt)
    if visibility is not None:
        updates.append('visibility = ?')
        params.append(visibility)
    if tags is not None:
        updates.append('tags = ?')
        params.append(tags)

    if not updates:
        release_connection(conn)
        return False

    updates.append('updated_at = CURRENT_TIMESTAMP')
    params.append(post_id)

    query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ?"
    cursor = _db_config.execute_query(conn, query, tuple(params), use_dict_cursor=False)

    success = cursor.rowcount > 0
    release_connection(conn)
    return success


def approve_post(post_id: int, reviewer_id: int, review_notes: str = '') -> bool:
    """Approve a post for publication"""
    conn = get_db_connection()

    query = '''
        UPDATE blog_posts
        SET status = ?, reviewer_id = ?, review_notes = ?, published_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = ?
    '''

    cursor = _db_config.execute_query(
        conn, query,
        ('published', reviewer_id, review_notes, post_id, 'pending_review'),
        use_dict_cursor=False
    )

    success = cursor.rowcount > 0
    release_connection(conn)
    return success


def reject_post(post_id: int, reviewer_id: int, review_notes: str = '') -> bool:
    """Reject a post"""
    conn = get_db_connection()

    query = '''
        UPDATE blog_posts
        SET status = ?, reviewer_id = ?, review_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = ?
    '''

    cursor = _db_config.execute_query(
        conn, query,
        ('rejected', reviewer_id, review_notes, post_id, 'pending_review'),
        use_dict_cursor=False
    )

    success = cursor.rowcount > 0
    release_connection(conn)
    return success


def delete_post(post_id: int, author_id: int = None) -> bool:
    """Delete a post (author can delete their own, admin can delete any)"""
    conn = get_db_connection()

    if author_id:
        query = 'DELETE FROM blog_posts WHERE id = ? AND author_id = ?'
        params = (post_id, author_id)
    else:
        query = 'DELETE FROM blog_posts WHERE id = ?'
        params = (post_id,)

    cursor = _db_config.execute_query(conn, query, params, use_dict_cursor=False)
    success = cursor.rowcount > 0
    release_connection(conn)
    return success


def migrate_sample_posts():
    """Add sample blog posts for testing"""
    conn = get_db_connection()
    cursor = dict_cursor(conn)

    # Check if posts already exist
    cursor.execute('SELECT COUNT(*) as count FROM blog_posts')
    result = cursor.fetchone()
    count = result['count'] if isinstance(result, dict) else result[0]

    if count > 0:
        release_connection(conn)
        return  # Posts already exist

    sample_posts = [
        {
            'title': 'Understanding Heart Failure and Nutrition: Your Complete Guide',
            'excerpt': 'Learn how proper nutrition plays a crucial role in managing heart failure and improving quality of life.',
            'content': '''Heart failure is a chronic condition that requires careful management, and nutrition plays a vital role in this process. Understanding how different foods affect your heart can empower you to make better dietary choices.

**Key Nutritional Considerations:**

1. **Sodium Management**: Limiting sodium intake is crucial for managing fluid retention and blood pressure.
2. **Fluid Balance**: Monitoring fluid intake helps prevent fluid overload.
3. **Nutrient-Dense Foods**: Focus on foods rich in potassium, magnesium, and heart-healthy fats.

This portal provides tools to help you track and manage these important nutritional factors.''',
            'author_id': 1,
            'author_name': 'Dr. Heart Health',
            'status': 'published',
            'visibility': 'public',
            'tags': 'heart failure, nutrition, health',
            'slug': 'understanding-heart-failure-and-nutrition-your-complete-guide'
        },
        {
            'title': 'The USDA Database: A Powerful Tool for Heart-Healthy Living',
            'excerpt': 'Discover how to use the USDA Food Data Central database to make informed nutritional choices.',
            'content': '''The USDA Food Data Central database is an invaluable resource for anyone managing their heart health through nutrition. This comprehensive database contains detailed nutritional information for thousands of foods.

**How to Use This Tool:**

1. **Search by Food Name**: Find nutritional information for any food item
2. **Compare Foods**: See how different foods compare in sodium, potassium, and other nutrients
3. **Plan Meals**: Use the data to create heart-healthy meal plans

The Nutrition Database tool on this portal makes it easy to access and use this information in your daily life.''',
            'author_id': 1,
            'author_name': 'Dr. Heart Health',
            'status': 'published',
            'visibility': 'public',
            'tags': 'usda, database, nutrition, tools',
            'slug': 'the-usda-database-a-powerful-tool-for-heart-healthy-living'
        }
    ]

    for post in sample_posts:
        query = '''
            INSERT INTO blog_posts
            (title, content, author_id, author_name, excerpt, visibility, tags, slug, status, published_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        '''

        _db_config.execute_query(
            conn, query,
            (post['title'], post['content'], post['author_id'], post['author_name'],
             post['excerpt'], post['visibility'], post['tags'], post['slug'], post['status']),
            use_dict_cursor=False
        )

    release_connection(conn)
