"""
Food-Base Component - Flask Application
Stores and manages food data captured from API-Manager
"""

from flask import Flask, request, jsonify, render_template, redirect, send_file, make_response
import os
import sys
from datetime import datetime
from jinja2 import ChoiceLoader, FileSystemLoader
from dotenv import load_dotenv
import csv
import json
import io

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add shared directory to path for authentication module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from auth import get_current_user

# Import shared URL helpers
from url_helpers import (
    get_main_app_url, get_blog_url, get_nutrition_url, get_foodbase_url,
    get_sodium_url, get_fluid_url, get_weight_url, get_bp_url
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
        get_weight_url=get_weight_url,
        get_bp_url=get_bp_url
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
    get_bp_url=get_bp_url,
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

# Export routes
@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    """Export selected foods to CSV format"""
    try:
        data = request.get_json()
        food_ids = data.get('food_ids', [])

        if not food_ids:
            return jsonify({'error': 'No food IDs provided'}), 400

        # Get foods data
        foods = []
        for food_id in food_ids:
            food = storage_service.get_food_by_id(food_id)
            if food:
                foods.append(food)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Food Name', 'Brand', 'FDC ID', 'Data Type',
            'Calories (kcal)', 'Protein (g)', 'Total Fat (g)',
            'Carbohydrates (g)', 'Fiber (g)', 'Sugars (g)',
            'Sodium (mg)', 'Calcium (mg)', 'Date Added'
        ])

        # Write data rows
        for food in foods:
            writer.writerow([
                food.get('name', 'N/A'),
                food.get('brand_owner', ''),
                food.get('fdc_id', ''),
                food.get('data_type', ''),
                food.get('calories', ''),
                food.get('protein', ''),
                food.get('total_fat', ''),
                food.get('carbohydrates', ''),
                food.get('fiber', ''),
                food.get('sugars', ''),
                food.get('sodium', ''),
                food.get('calcium', ''),
                food.get('date_added', '')
            ])

        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'food_storage_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/json', methods=['POST'])
def export_json():
    """Export selected foods to JSON format"""
    try:
        data = request.get_json()
        food_ids = data.get('food_ids', [])

        if not food_ids:
            return jsonify({'error': 'No food IDs provided'}), 400

        # Get foods data
        foods = []
        for food_id in food_ids:
            food = storage_service.get_food_by_id(food_id)
            if food:
                foods.append(food)

        # Create JSON structure
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_foods': len(foods),
            'foods': foods
        }

        # Create response
        json_str = json.dumps(export_data, indent=2)
        return send_file(
            io.BytesIO(json_str.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'food_storage_{datetime.now().strftime("%Y%m%d")}.json'
        )

    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    """Export selected foods to PDF format"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch

        data = request.get_json()
        food_ids = data.get('food_ids', [])

        if not food_ids:
            return jsonify({'error': 'No food IDs provided'}), 400

        # Get foods data
        foods = []
        for food_id in food_ids:
            food = storage_service.get_food_by_id(food_id)
            if food:
                foods.append(food)

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []

        # Styles
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph('<b>Food Storage Export</b>', styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))

        # Export info
        info_text = f'Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}<br/>Total Foods: {len(foods)}'
        info = Paragraph(info_text, styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.3*inch))

        # Table data
        table_data = [[
            'Food Name', 'Brand', 'Calories', 'Protein (g)',
            'Fat (g)', 'Carbs (g)', 'Sodium (mg)'
        ]]

        for food in foods:
            table_data.append([
                food.get('name', 'N/A')[:30],  # Truncate long names
                food.get('brand_owner', '')[:20],
                food.get('calories', 'N/A'),
                food.get('protein', 'N/A'),
                food.get('total_fat', 'N/A'),
                food.get('carbohydrates', 'N/A'),
                food.get('sodium', 'N/A')
            ])

        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'food_storage_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

    except ImportError:
        return jsonify({
            'error': 'PDF export requires reportlab library. Install with: pip install reportlab'
        }), 500
    except Exception as e:
        return jsonify({'error': f'PDF export failed: {str(e)}'}), 500

# Redirect routes for inter-component navigation
@app.route('/redirect/nutrition')
def redirect_to_nutrition():
    """Redirect to Nutrition Database - environment-aware"""
    return redirect(get_nutrition_url())

@app.route('/redirect/foodbase')
def redirect_to_foodbase():
    """Redirect to Food-Base - environment-aware"""
    return redirect(get_foodbase_url())

@app.route('/redirect/sodium')
def redirect_to_sodium():
    """Redirect to Sodium Tracker - environment-aware"""
    return redirect(get_sodium_url())

@app.route('/redirect/fluid')
def redirect_to_fluid():
    """Redirect to Fluid Tracker - environment-aware"""
    return redirect(get_fluid_url())

@app.route('/redirect/weight')
def redirect_to_weight():
    """Redirect to Weight Tracker - environment-aware"""
    return redirect(get_weight_url())

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

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
    
    # Read port from environment variable (for staging) or use default
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, port=port)