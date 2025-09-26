"""
Blog Database Management for Heart Portal
Handles blog posts, user authoring, and moderation workflow
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'blog.db')

def init_blog_database():
    """Initialize the blog database with required tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Blog posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    conn.commit()
    conn.close()

def create_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    import re
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:100]  # Limit length

def get_published_posts(limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get published public posts for public blog view"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, excerpt, author_name, published_at, slug, tags
        FROM blog_posts
        WHERE status = 'published' AND visibility = 'public'
        ORDER BY published_at DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts

def get_post_by_slug(slug: str) -> Optional[Dict]:
    """Get a specific published public post by slug"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM blog_posts
        WHERE slug = ? AND status = 'published' AND visibility = 'public'
    ''', (slug,))

    post = cursor.fetchone()
    conn.close()
    return dict(post) if post else None

def get_user_posts(author_id: int, limit: int = 50) -> List[Dict]:
    """Get all posts by a specific user (private and public)"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, status, visibility, excerpt, created_at, updated_at, slug
        FROM blog_posts
        WHERE author_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
    ''', (author_id, limit))

    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts

def get_pending_posts() -> List[Dict]:
    """Get posts pending review for admin interface"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, author_name, excerpt, created_at, updated_at, slug
        FROM blog_posts
        WHERE status = 'pending_review' AND visibility = 'public'
        ORDER BY updated_at ASC
    ''')

    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts

def create_post(title: str, content: str, author_id: int, author_name: str,
               excerpt: str = '', visibility: str = 'private', tags: str = '') -> int:
    """Create a new blog post"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    slug = create_slug(title)
    now = datetime.now().isoformat()

    # Ensure unique slug
    base_slug = slug
    counter = 1
    while True:
        cursor.execute('SELECT COUNT(*) FROM blog_posts WHERE slug = ?', (slug,))
        if cursor.fetchone()[0] == 0:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    status = 'pending_review' if visibility == 'public' else 'draft'

    cursor.execute('''
        INSERT INTO blog_posts
        (title, content, author_id, author_name, status, visibility, slug, excerpt, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, content, author_id, author_name, status, visibility, slug, excerpt, tags, now, now))

    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def update_post(post_id: int, title: str = None, content: str = None,
               excerpt: str = None, visibility: str = None, tags: str = None) -> bool:
    """Update an existing post"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Build update query dynamically
    updates = []
    params = []

    if title is not None:
        updates.append('title = ?')
        params.append(title)
        # Update slug if title changes
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
        # If changing to public, set status to pending_review
        if visibility == 'public':
            updates.append('status = ?')
            params.append('pending_review')

    if tags is not None:
        updates.append('tags = ?')
        params.append(tags)

    if updates:
        updates.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.append(post_id)

        query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    conn.close()
    return False

def approve_post(post_id: int, reviewer_id: int, review_notes: str = '') -> bool:
    """Approve a pending post (admin function)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute('''
        UPDATE blog_posts
        SET status = 'published', published_at = ?, reviewer_id = ?, review_notes = ?
        WHERE id = ? AND status = 'pending_review'
    ''', (now, reviewer_id, review_notes, post_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def reject_post(post_id: int, reviewer_id: int, review_notes: str = '') -> bool:
    """Reject a pending post (admin function)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE blog_posts
        SET status = 'rejected', reviewer_id = ?, review_notes = ?
        WHERE id = ? AND status = 'pending_review'
    ''', (reviewer_id, review_notes, post_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def delete_post(post_id: int, author_id: int = None) -> bool:
    """Delete a post (only by author or admin)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if author_id:
        # Only allow author to delete their own posts
        cursor.execute('DELETE FROM blog_posts WHERE id = ? AND author_id = ?', (post_id, author_id))
    else:
        # Admin can delete any post
        cursor.execute('DELETE FROM blog_posts WHERE id = ?', (post_id,))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def migrate_sample_posts():
    """Migrate existing sample posts to database (one-time migration)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check if we already have posts
    cursor.execute('SELECT COUNT(*) FROM blog_posts')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Sample posts from the original app.py
    sample_posts = [
        {
            'title': 'Understanding Heart Failure and Nutrition: Your Complete Guide',
            'content': '''<h2>What is Heart Failure?</h2>
<p>Heart failure affects over 6 million Americans and occurs when your heart muscle doesn't pump blood as well as it should. This doesn't mean your heart has stopped working, but rather that it's working less efficiently than normal.</p>

<h2>The Critical Role of Nutrition</h2>
<p>Proper nutrition plays a crucial role in managing heart failure symptoms and improving your quality of life. The foods you eat directly impact:</p>
<ul>
    <li><strong>Fluid retention:</strong> High sodium foods can cause your body to retain water, making your heart work harder</li>
    <li><strong>Energy levels:</strong> Balanced nutrition helps maintain steady energy throughout the day</li>
    <li><strong>Weight management:</strong> Maintaining a healthy weight reduces strain on your heart</li>
    <li><strong>Overall cardiovascular health:</strong> Heart-healthy foods support better circulation and heart function</li>
</ul>

<h2>Key Dietary Guidelines for Heart Failure</h2>
<h3>1. Sodium Restriction</h3>
<p>Most cardiologists recommend limiting sodium to 2,000-3,000mg per day. This helps prevent fluid buildup and reduces the workload on your heart.</p>

<h3>2. Fluid Management</h3>
<p>Your healthcare provider may recommend limiting fluids to 1.5-2 liters per day, depending on your condition severity.</p>

<h3>3. Heart-Healthy Foods</h3>
<p>Focus on foods rich in:</p>
<ul>
    <li>Potassium (bananas, oranges, spinach)</li>
    <li>Magnesium (nuts, seeds, whole grains)</li>
    <li>Omega-3 fatty acids (fish, flaxseeds)</li>
    <li>Fiber (vegetables, fruits, beans)</li>
</ul>

<blockquote>Remember: Always consult with your healthcare provider before making significant dietary changes. Every person's heart failure journey is unique.</blockquote>

<h2>Using Technology to Support Your Journey</h2>
<p>Our Heart Portal tools can help you track nutrition and make informed food choices. The USDA Nutrition Database provides detailed nutritional information, while the Food Storage feature helps you organize heart-healthy meal planning.</p>''',
            'author_name': 'Heart Portal Team',
            'excerpt': 'Learn how nutrition impacts heart failure management and discover practical strategies for heart-healthy eating.',
            'published_at': '2025-01-15T00:00:00'
        },
        {
            'title': 'The USDA Database: A Powerful Tool for Heart-Healthy Living',
            'content': '''<h2>Introduction to USDA Food Data Central</h2>
<p>The USDA Food Data Central is a comprehensive database containing nutritional information for thousands of foods. For heart failure patients, this resource is invaluable for making informed dietary choices.</p>

<h2>Why Nutritional Data Matters</h2>
<p>When managing heart failure, every milligram of sodium counts. The USDA database provides precise nutritional information that helps you:</p>
<ul>
    <li>Track daily sodium intake accurately</li>
    <li>Compare similar foods to make better choices</li>
    <li>Plan balanced meals that support heart health</li>
    <li>Understand portion sizes and their nutritional impact</li>
</ul>

<h2>How to Use Our Nutrition Database Tool</h2>
<h3>Step 1: Search for Foods</h3>
<p>Use our search feature to find specific foods or browse categories. The database includes everything from fresh produce to packaged foods.</p>

<h3>Step 2: Analyze Nutritional Content</h3>
<p>Pay special attention to:</p>
<ul>
    <li><strong>Sodium content:</strong> Keep daily intake under your recommended limit</li>
    <li><strong>Potassium levels:</strong> Important for heart rhythm and muscle function</li>
    <li><strong>Saturated fat:</strong> Limit to support overall cardiovascular health</li>
    <li><strong>Fiber content:</strong> Helps with cholesterol management</li>
</ul>

<h3>Step 3: Save Your Favorites</h3>
<p>Use our Food Storage feature to save heart-healthy foods you discover. This makes meal planning easier and helps you stick to your nutritional goals.</p>

<h2>Real-World Application</h2>
<p>For example, when comparing bread options:</p>
<ul>
    <li>Regular white bread: ~230mg sodium per slice</li>
    <li>Low-sodium whole grain: ~80mg sodium per slice</li>
    <li>Homemade bread (no salt): ~5mg sodium per slice</li>
</ul>
<p>This data helps you make choices that support your heart health goals while still enjoying the foods you love.</p>

<blockquote>Pro tip: Look for the "per 100g" nutritional data to easily compare different foods on an equal basis.</blockquote>

<h2>Getting Started</h2>
<p>Ready to explore? Access our Nutrition Database through the Tools menu above. Start by searching for foods you commonly eat, and discover healthier alternatives that fit your dietary needs.</p>''',
            'author_name': 'Heart Portal Team',
            'excerpt': 'Discover how to use nutritional data to support heart-healthy eating and make informed food choices.',
            'published_at': '2025-01-10T00:00:00'
        }
    ]

    # Insert sample posts as published public content
    for post in sample_posts:
        slug = create_slug(post['title'])
        cursor.execute('''
            INSERT INTO blog_posts
            (title, content, author_id, author_name, status, visibility, slug, excerpt, tags,
             created_at, updated_at, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            post['title'],
            post['content'],
            1,  # Admin user ID
            post['author_name'],
            'published',
            'public',
            slug,
            post['excerpt'],
            'nutrition,heart-health',
            post['published_at'],
            post['published_at'],
            post['published_at']
        ))

    conn.commit()
    conn.close()