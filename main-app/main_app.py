"""
Main Flask Application for Heart Failure Portal
Serves landing page, blog, about pages
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Sample blog posts data (you'll want to use a database later)
BLOG_POSTS = [
    {
        'id': 1,
        'title': 'Understanding Heart Failure and Nutrition',
        'content': 'Heart failure affects millions of people worldwide. Proper nutrition plays a crucial role in managing symptoms and improving quality of life...',
        'date': datetime(2025, 1, 15),
        'author': 'Your Name',
        'excerpt': 'Learn how nutrition impacts heart failure management and daily living.'
    },
    {
        'id': 2,
        'title': 'The USDA Database: A Powerful Tool for Heart Health',
        'content': 'The USDA Food Data Central provides comprehensive nutritional information that can help heart failure patients make informed dietary choices...',
        'date': datetime(2025, 1, 10),
        'author': 'Your Name',
        'excerpt': 'Discover how to use nutritional data to support heart-healthy eating.'
    }
]

@app.route('/')
def landing_page():
    """Main landing page"""
    return render_template('landing.html')

@app.route('/blog')
def blog_list():
    """Blog post listing page"""
    return render_template('blog.html', posts=BLOG_POSTS)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    """Individual blog post page"""
    post = next((p for p in BLOG_POSTS if p['id'] == post_id), None)
    if not post:
        return render_template('404.html'), 404
    return render_template('blog_post.html', post=post)

@app.route('/about')
def about_portal():
    """About the portal page"""
    return render_template('about.html')

@app.route('/creator')
def about_creator():
    """About the creator page"""
    return render_template('creator.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form (optional)"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # You'd typically save this to a database or send an email
        # For now, just return a success response
        return jsonify({'success': True, 'message': 'Thank you for your message!'})
    
    return render_template('contact.html')

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000, host='0.0.0.0')
