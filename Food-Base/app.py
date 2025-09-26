"""
Food-Base Component - Flask Application
Stores and manages food data captured from API-Manager
"""

from flask import Flask, request, jsonify, render_template, redirect
import os
import sys
from datetime import datetime
from jinja2 import ChoiceLoader, FileSystemLoader
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add shared directory to path for authentication module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from auth import get_current_user

# Import shared URL helpers
from url_helpers import (
    get_main_app_url, get_blog_url, get_nutrition_url, get_foodbase_url,
    get_sodium_url, get_fluid_url, get_weight_url
)

# Import database components
from database import init_database, create_tables, get_database_info
from food_storage import FoodStorageService

app = Flask(__name__)

# Shared secret key for cross-application session compatibility
app.secret_key = os.environ.get('SECRET_KEY', 'heart-portal-shared-secret-key-2025')

# Configure session cookies for reverse proxy setup
app.config['SESSION_COOKIE_DOMAIN'] = '.heartfailureportal.com'  # Share cookies across all subdomains
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-site requests

# Configure Jinja2 to use shared templates
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'shared', 'templates'))
])

# URL helpers are now imported from shared module

# Make functions available in templates
@app.context_processor
def utility_processor():
    return dict(
        get_main_app_url=get_main_app_url,
        get_blog_url=get_blog_url,
        get_nutrition_url=get_nutrition_url,
        get_foodbase_url=get_foodbase_url,
        get_sodium_url=get_sodium_url,
        get_fluid_url=get_fluid_url,
        get_weight_url=get_weight_url
    )

# Register template global functions
app.jinja_env.globals.update(
    get_main_app_url=get_main_app_url,
    get_blog_url=get_blog_url,
    get_nutrition_url=get_nutrition_url,
    get_foodbase_url=get_foodbase_url,
    get_sodium_url=get_sodium_url,
    get_fluid_url=get_fluid_url,
    get_weight_url=get_weight_url,
    get_current_user=get_current_user
)

# Initialize database
db = init_database(app)

# Initialize storage service
storage_service = FoodStorageService()

@app.route('/')
def index():
    """Main Food-Base interface - requires login"""
    current_user = get_current_user()
    if not current_user:
        main_app_url = get_main_app_url()
        return redirect(f"{main_app_url}/login?next={request.url}")

    # Get current food count for display
    stats = storage_service.get_database_stats()
    return render_template('index.html', food_count=stats['total_foods'])

@app.route('/api/foods', methods=['GET'])
def get_stored_foods():
    """Get all stored foods with optional filtering"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search')
        category = request.args.get('category')
        
        # Apply filters
        if search:
            foods = storage_service.search_foods(search, limit=limit)
        elif category:
            foods = storage_service.get_foods_by_category(category, limit=limit)
        else:
            foods = storage_service.get_all_foods(limit=limit, offset=offset)
        
        return jsonify({
            'foods': foods,
            'count': len(foods)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve foods: {str(e)}'}), 500

@app.route('/api/foods', methods=['POST'])
def save_food():
    """Save a food item from API-Manager"""
    try:
        food_data = request.get_json()
        if not food_data:
            return jsonify({'error': 'No food data provided'}), 400
        
        # Get client IP for logging
        ip_address = request.remote_addr
        
        # Save using storage service
        result = storage_service.save_food_from_api(food_data, ip_address)
        
        if 'error' in result:
            return jsonify(result), 400
        
        # Return appropriate status code
        status_code = 200 if result.get('duplicate') else 201
        
        return jsonify({
            'message': result['message'],
            'food': result['food'],
            'duplicate': result.get('duplicate', False)
        }), status_code
        
    except Exception as e:
        return jsonify({'error': f'Failed to save food: {str(e)}'}), 500

@app.route('/api/foods/<int:food_id>', methods=['GET'])
def get_food_details(food_id):
    """Get detailed information for a specific saved food"""
    try:
        food = storage_service.get_food_by_id(food_id)
        if not food:
            return jsonify({'error': 'Food not found'}), 404
        
        return jsonify(food)
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve food: {str(e)}'}), 500

@app.route('/api/foods/fdc/<int:fdc_id>', methods=['GET'])
def get_food_by_fdc_id(fdc_id):
    """Get food by FDC ID"""
    try:
        food = storage_service.get_food_by_fdc_id(fdc_id)
        if not food:
            return jsonify({'error': 'Food not found'}), 404
        
        return jsonify(food)
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve food: {str(e)}'}), 500

@app.route('/api/foods/<int:food_id>', methods=['PUT'])
def update_food(food_id):
    """Update a saved food"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        result = storage_service.update_food(food_id, data)
        
        if 'error' in result:
            return jsonify(result), 404 if 'not found' in result['error'].lower() else 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to update food: {str(e)}'}), 500

@app.route('/api/foods/<int:food_id>', methods=['DELETE'])
def delete_food(food_id):
    """Delete a saved food"""
    try:
        result = storage_service.delete_food(food_id)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete food: {str(e)}'}), 500

@app.route('/api/search', methods=['GET'])
def search_foods():
    """Search foods by query"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 50, type=int)
        
        foods = storage_service.search_foods(query, limit=limit)
        
        return jsonify({
            'foods': foods,
            'count': len(foods),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/categories/<category>', methods=['GET'])
def get_foods_by_category(category):
    """Get foods by data type category"""
    try:
        limit = request.args.get('limit', 50, type=int)
        foods = storage_service.get_foods_by_category(category, limit=limit)
        
        return jsonify({
            'foods': foods,
            'count': len(foods),
            'category': category
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get foods by category: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        stats = storage_service.get_database_stats()
        db_info = get_database_info()
        
        return jsonify({
            **stats,
            'database': db_info
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        stats = storage_service.get_database_stats()
        db_info = get_database_info()
        
        return jsonify({
            'status': 'healthy',
            'component': 'Food-Base',
            'database_connected': db_info['exists'],
            'foods_stored': stats['total_foods'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'component': 'Food-Base',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Redirect routes for inter-component navigation
@app.route('/redirect/nutrition')
def redirect_to_nutrition():
    """Redirect to Nutrition Database - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/nutrition-database/')
    return redirect('http://localhost:5000')

@app.route('/redirect/foodbase')
def redirect_to_foodbase():
    """Redirect to Food-Base - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/food-base/')
    return redirect('http://localhost:5001')

@app.route('/redirect/sodium')
def redirect_to_sodium():
    """Redirect to Sodium Tracker - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/sodium-tracker/')
    return redirect('http://localhost:5003')

@app.route('/redirect/fluid')
def redirect_to_fluid():
    """Redirect to Fluid Tracker - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/fluid-tracker/')
    return redirect('http://localhost:5004')

@app.route('/redirect/weight')
def redirect_to_weight():
    """Redirect to Weight Tracker - environment-aware"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/weight-tracker/')
    return redirect('http://localhost:5005')

if __name__ == '__main__':
    print("🍎 Starting Food-Base Component on port 5001")
    print("📊 Food storage and management system with SQLite database")
    
    # Create database tables on startup
    try:
        create_tables(app)
        db_info = get_database_info()
        print(f"💾 Database: {db_info['path']}")
        print(f"📈 Database size: {db_info['size']} bytes")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    app.run(debug=True, port=5001)