"""
Enhanced Flask app with additional USDA API endpoints
Add this to your existing app.py
"""

from flask import Flask, request, jsonify, render_template
from nutrition_api_manager import (
    EnhancedUSDAFoodDataAPI, 
    EnhancedNutritionAPIManager,
    SearchCriteria,
    ListCriteria,
    DataType,
    SortBy,
    APIError
)
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Global manager instance with API key management
manager = EnhancedNutritionAPIManager()

# API Key management
def get_usda_api_key():
    """Get USDA API key from environment or return None"""
    return os.getenv('USDA_API_KEY')

def is_api_configured():
    """Check if USDA API key is configured"""
    api_key = get_usda_api_key()
    return api_key and api_key.strip() != '' and api_key != 'your_actual_usda_api_key_here'

def initialize_apis():
    """Initialize API instances if keys are available"""
    try:
        if is_api_configured():
            api_key = get_usda_api_key()
            if api_key:  # Additional type check to satisfy type checker
                manager.add_enhanced_usda_api(api_key)
                print(f"✅ USDA API initialized successfully")
                return True
            else:
                print("⚠️ USDA API key is None after configuration check")
                return False
        else:
            print("⚠️ USDA API key not configured. Please set USDA_API_KEY in .env file")
            return False
    except Exception as e:
        print(f"❌ Failed to initialize USDA API: {e}")
        return False

# Initialize APIs on startup
api_initialized = initialize_apis()

def require_api_key(f):
    """Decorator to check if API is configured before processing requests"""
    def wrapper(*args, **kwargs):
        if not is_api_configured():
            return jsonify({
                'error': 'USDA API key not configured',
                'message': 'Please configure your USDA API key in the .env file',
                'configured': False
            }), 503  # Service Unavailable
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get API configuration status"""
    return jsonify({
        'configured': is_api_configured(),
        'apis_available': ['USDA FoodData Central'] if is_api_configured() else [],
        'message': 'API is ready' if is_api_configured() else 'Please configure USDA API key in .env file'
    })

# Add these new routes to your existing app.py

@app.route('/api/advanced-search', methods=['POST'])
@require_api_key
def advanced_search():
    """Advanced search with filtering options"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        query = data.get('query', '')
        data_types_str = data.get('dataTypes', [])
        brand_owner = data.get('brandOwner')
        sort_by_str = data.get('sortBy')
        sort_order = data.get('sortOrder', 'asc')
        page_size = data.get('pageSize', 25)
        page_number = data.get('pageNumber', 1)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Convert string data types to enum
        data_types = []
        if data_types_str:
            type_mapping = {
                'Foundation': DataType.FOUNDATION,
                'SR Legacy': DataType.SR_LEGACY,
                'Survey (FNDDS)': DataType.SURVEY,
                'Branded': DataType.BRANDED,
                'Experimental': DataType.EXPERIMENTAL
            }
            data_types = [type_mapping[dt] for dt in data_types_str if dt in type_mapping]
        
        # Convert sort by string to enum
        sort_by = None
        if sort_by_str:
            sort_mapping = {
                'relevance': SortBy.RELEVANCE,
                'dataType': SortBy.DATA_TYPE,
                'description': SortBy.DESCRIPTION,
                'fdcId': SortBy.FDC_ID,
                'publishedDate': SortBy.PUBLISHED_DATE
            }
            sort_by = sort_mapping.get(sort_by_str)
        
        # Create search criteria
        criteria = SearchCriteria(
            query=query,
            data_type=data_types if data_types else None,
            brand_owner=brand_owner,
            sort_by=sort_by,
            sort_order=sort_order,
            page_size=page_size,
            page_number=page_number
        )
        
        # Get API and perform search
        if 'usda_enhanced' not in manager.apis:
            return jsonify({'error': 'Enhanced USDA API not configured'}), 400
            
        api = manager.apis['usda_enhanced']
        results = api.search_foods(criteria)
        
        # Format results for UI
        formatted_results = format_search_results(results)
        
        return jsonify({
            'results': formatted_results,
            'totalHits': results.get('totalHits', 0),
            'currentPage': results.get('currentPage', 1),
            'totalPages': results.get('totalPages', 1)
        })
        
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/foods-list', methods=['POST'])
@require_api_key
def get_foods_list():
    """Get paginated list of foods by category"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        data_types_str = data.get('dataTypes', [])
        sort_by_str = data.get('sortBy', 'description')
        sort_order = data.get('sortOrder', 'asc')
        page_size = data.get('pageSize', 20)
        page_number = data.get('pageNumber', 1)
        
        # Convert data types
        data_types = []
        if data_types_str:
            type_mapping = {
                'Foundation': DataType.FOUNDATION,
                'SR Legacy': DataType.SR_LEGACY,
                'Survey (FNDDS)': DataType.SURVEY,
                'Branded': DataType.BRANDED,
                'Experimental': DataType.EXPERIMENTAL
            }
            data_types = [type_mapping[dt] for dt in data_types_str if dt in type_mapping]
        
        # Convert sort by
        sort_mapping = {
            'relevance': SortBy.RELEVANCE,
            'dataType': SortBy.DATA_TYPE,
            'description': SortBy.DESCRIPTION,
            'fdcId': SortBy.FDC_ID,
            'publishedDate': SortBy.PUBLISHED_DATE
        }
        sort_by = sort_mapping.get(sort_by_str, SortBy.RELEVANCE)
        
        # Create list criteria
        criteria = ListCriteria(
            data_type=data_types if data_types else None,
            sort_by=sort_by,
            sort_order=sort_order,
            page_size=page_size,
            page_number=page_number
        )
        
        # Get API and perform request
        if 'usda_enhanced' not in manager.apis:
            return jsonify({'error': 'Enhanced USDA API not configured'}), 400
            
        api = manager.apis['usda_enhanced']
        results = api.get_foods_list(criteria)
        
        # Format results - handle different API response structure
        formatted_results = format_foods_list(results)
        
        # Handle different response structures from foods/list vs foods/search
        total_hits = results.get('totalHits', len(formatted_results)) if isinstance(results, dict) else len(formatted_results)
        current_page = results.get('currentPage', page_number) if isinstance(results, dict) else page_number
        total_pages = results.get('totalPages', 1) if isinstance(results, dict) else max(1, (total_hits + page_size - 1) // page_size)
        
        return jsonify({
            'foods': formatted_results,
            'totalHits': total_hits,
            'currentPage': current_page,
            'totalPages': total_pages
        })
        
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/compare-foods', methods=['POST'])
@require_api_key
def compare_foods():
    """Compare multiple foods by FDC IDs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        fdc_ids = data.get('fdcIds', [])
        nutrients = data.get('nutrients')  # Optional list of nutrient IDs
        
        if not fdc_ids:
            return jsonify({'error': 'FDC IDs are required'}), 400
        
        # Validate FDC IDs
        try:
            fdc_ids = [int(fdc_id) for fdc_id in fdc_ids]
        except ValueError:
            return jsonify({'error': 'Invalid FDC ID format'}), 400
        
        if len(fdc_ids) > 20:
            return jsonify({'error': 'Maximum 20 foods can be compared at once'}), 400
        
        # Get API and perform comparison
        if 'usda_enhanced' not in manager.apis:
            return jsonify({'error': 'Enhanced USDA API not configured'}), 400
            
        api = manager.apis['usda_enhanced']
        results = api.get_multiple_foods(fdc_ids, nutrients)
        
        # Format results for comparison
        comparison_data = format_food_comparison(results)
        
        return jsonify({
            'foods': comparison_data,
            'count': len(comparison_data)
        })
        
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/data-types', methods=['GET'])
@require_api_key
def get_data_types():
    """Get available data types"""
    return jsonify({
        'dataTypes': [
            {'value': 'Foundation', 'label': 'Foundation Foods'},
            {'value': 'SR Legacy', 'label': 'SR Legacy'},
            {'value': 'Survey (FNDDS)', 'label': 'Survey (FNDDS)'},
            {'value': 'Branded', 'label': 'Branded Foods'},
            {'value': 'Experimental', 'label': 'Experimental Foods'}
        ]
    })

@app.route('/api/nutrients-list', methods=['GET'])
@require_api_key
def get_nutrients_list():
    """Get list of common nutrients for filtering"""
    # Common nutrients with their IDs from USDA database
    common_nutrients = [
        {'id': 1008, 'name': 'Energy (kcal)', 'unit': 'kcal'},
        {'id': 1003, 'name': 'Protein', 'unit': 'g'},
        {'id': 1004, 'name': 'Total lipid (fat)', 'unit': 'g'},
        {'id': 1005, 'name': 'Carbohydrate, by difference', 'unit': 'g'},
        {'id': 1079, 'name': 'Fiber, total dietary', 'unit': 'g'},
        {'id': 2000, 'name': 'Sugars, total including NLEA', 'unit': 'g'},
        {'id': 1093, 'name': 'Sodium, Na', 'unit': 'mg'},
        {'id': 1087, 'name': 'Calcium, Ca', 'unit': 'mg'},
        {'id': 1089, 'name': 'Iron, Fe', 'unit': 'mg'},
        {'id': 1106, 'name': 'Vitamin A, RAE', 'unit': 'µg'},
        {'id': 1162, 'name': 'Vitamin C, total ascorbic acid', 'unit': 'mg'},
    ]
    
    return jsonify({'nutrients': common_nutrients})

@app.route('/api/food-details/<int:fdc_id>', methods=['GET'])
@require_api_key
def get_food_details(fdc_id):
    """Get detailed food information by FDC ID"""
    try:
        # Get API and fetch food details
        if 'usda_enhanced' not in manager.apis:
            return jsonify({'error': 'Enhanced USDA API not configured'}), 400
            
        api = manager.apis['usda_enhanced']
        food_details = api.get_food_details(fdc_id)
        
        return jsonify(food_details)
        
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/save-to-foodbase', methods=['POST'])
def save_to_foodbase():
    """Save a food item to Food-Base component"""
    import requests
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        fdc_id = data.get('fdc_id')
        if not fdc_id:
            return jsonify({'error': 'FDC ID is required'}), 400
        
        # Get enhanced API instance
        if 'usda_enhanced' not in manager.apis:
            return jsonify({'error': 'Enhanced USDA API not configured'}), 400
        
        api = manager.apis['usda_enhanced']
        
        # Fetch complete food details from USDA API
        complete_food_data = api.get_food_details(fdc_id)
        
        # Send to Food-Base component
        FOOD_BASE_URL = 'http://localhost:5001'  # Food-Base component URL
        
        response = requests.post(
            f'{FOOD_BASE_URL}/api/foods',
            json=complete_food_data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                'success': True,
                'message': result.get('message', 'Food saved successfully'),
                'duplicate': result.get('duplicate', False),
                'food': result.get('food', {})
            })
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return jsonify({
                'success': False,
                'error': error_data.get('error', f'Food-Base returned status {response.status_code}')
            }), response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Could not connect to Food-Base component. Make sure it is running on port 5001.'
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request to Food-Base timed out. Please try again.'
        }), 504
    except APIError as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch food details: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@app.route('/api/check-foodbase-connection', methods=['GET'])
def check_foodbase_connection():
    """Check if Food-Base component is available"""
    import requests
    
    try:
        FOOD_BASE_URL = 'http://localhost:5001'
        response = requests.get(f'{FOOD_BASE_URL}/api/health', timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            return jsonify({
                'connected': True,
                'status': health_data.get('status', 'unknown'),
                'foods_stored': health_data.get('foods_stored', 0)
            })
        else:
            return jsonify({
                'connected': False,
                'error': f'Food-Base returned status {response.status_code}'
            })
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            'connected': False,
            'error': 'Could not connect to Food-Base component'
        })
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        })

@app.route('/api/add-enhanced-provider', methods=['POST'])
def add_enhanced_provider():
    """Add enhanced USDA provider with all endpoints"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        # Add enhanced API
        api = manager.add_enhanced_usda_api(api_key)
        
        # Test connection
        if api.test_connection():
            return jsonify({
                'message': 'Enhanced USDA API added successfully',
                'provider': 'usda_enhanced',
                'endpoints': [
                    'foods/search (enhanced)',
                    'foods/list',
                    'foods (multiple)',
                    'food/{id} (enhanced)'
                ]
            })
        else:
            return jsonify({'error': 'Failed to connect to USDA API'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions for formatting results

def format_search_results(results):
    """Format search results for UI display"""
    if 'foods' not in results:
        return []
    
    formatted = []
    for food in results['foods']:
        formatted_food = {
            'food_id': food.get('fdcId'),
            'name': food.get('description', 'Unknown'),
            'brand': food.get('brandOwner'),
            'data_type': food.get('dataType'),
            'published_date': food.get('publishedDate'),
            'ingredients': food.get('ingredients'),
            'calories': None,
            'protein': None,
            'carbs': None,
            'fat': None,
            'sodium': None,
            'serving_size': None,
            'serving_unit': None
        }
        
        # Extract basic nutrients if available
        nutrients = food.get('foodNutrients', [])
        for nutrient in nutrients:
            nutrient_id = nutrient.get('nutrientId')
            value = nutrient.get('value')
            
            if nutrient_id == 1008:  # Energy
                formatted_food['calories'] = value
            elif nutrient_id == 1003:  # Protein
                formatted_food['protein'] = value
            elif nutrient_id == 1005:  # Carbs
                formatted_food['carbs'] = value
            elif nutrient_id == 1004:  # Fat
                formatted_food['fat'] = value
            elif nutrient_id == 1093:  # Sodium
                formatted_food['sodium'] = value
        
        # Extract serving size information
        # Check for food portions (serving sizes)
        food_portions = food.get('foodPortions', [])
        if food_portions:
            # Use the first portion as default serving size
            portion = food_portions[0]
            formatted_food['serving_size'] = portion.get('amount')
            formatted_food['serving_unit'] = portion.get('modifier', 'serving')
        else:
            # Fallback to 100g as standard serving if no portions available
            formatted_food['serving_size'] = 100
            formatted_food['serving_unit'] = 'g'
        
        formatted.append(formatted_food)
    
    return formatted

def format_foods_list(results):
    """Format foods list results for UI - handles different API response structure"""
    # foods/list returns a list directly, while foods/search returns {'foods': [...]}
    if isinstance(results, list):
        # Direct list from foods/list endpoint
        foods_list = results
    elif isinstance(results, dict) and 'foods' in results:
        # foods/search format
        foods_list = results['foods']
    elif isinstance(results, dict):
        # Sometimes the response might be a dict but structured differently
        foods_list = results.get('foods', [results])
    else:
        # Fallback
        foods_list = []
    
    if not foods_list:
        return []
    
    formatted = []
    for food in foods_list:
        formatted_food = {
            'food_id': food.get('fdcId'),
            'name': food.get('description', 'Unknown'),
            'brand': food.get('brandOwner'),
            'data_type': food.get('dataType'),
            'published_date': food.get('publishedDate'),
            'ingredients': food.get('ingredients'),
            'calories': None,
            'protein': None,
            'carbs': None,
            'fat': None,
            'sodium': None,
            'serving_size': 100,  # Default for browse
            'serving_unit': 'g'   # Default for browse
        }
        
        # Extract basic nutrients if available (foods/list has limited nutrient data)
        nutrients = food.get('foodNutrients', [])
        for nutrient in nutrients:
            nutrient_id = nutrient.get('nutrientId')
            value = nutrient.get('value')
            
            if nutrient_id == 1008:  # Energy
                formatted_food['calories'] = value
            elif nutrient_id == 1003:  # Protein
                formatted_food['protein'] = value
            elif nutrient_id == 1005:  # Carbs
                formatted_food['carbs'] = value
            elif nutrient_id == 1004:  # Fat
                formatted_food['fat'] = value
            elif nutrient_id == 1093:  # Sodium
                formatted_food['sodium'] = value
        
        # Extract serving size information if available
        food_portions = food.get('foodPortions', [])
        if food_portions:
            portion = food_portions[0]
            formatted_food['serving_size'] = portion.get('amount', 100)
            formatted_food['serving_unit'] = portion.get('modifier', 'g')
        
        formatted.append(formatted_food)
    
    return formatted

def format_food_comparison(results):
    """Format food comparison results"""
    if not results:
        return []
    
    formatted = []
    for food in results:
        food_data = {
            'fdc_id': food.get('fdcId'),
            'description': food.get('description'),
            'data_type': food.get('dataType'),
            'brand_owner': food.get('brandOwner'),
            'nutrients': {}
        }
        
        # Extract all nutrients
        for nutrient in food.get('foodNutrients', []):
            nutrient_id = nutrient.get('nutrient', {}).get('id')
            nutrient_name = nutrient.get('nutrient', {}).get('name')
            value = nutrient.get('amount')
            unit = nutrient.get('nutrient', {}).get('unitName')
            
            if nutrient_id:
                food_data['nutrients'][nutrient_id] = {
                    'name': nutrient_name,
                    'value': value,
                    'unit': unit
                }
        
        formatted.append(food_data)
    
    return formatted

if __name__ == '__main__':
    import os
port = int(os.environ.get('PORT', 5000))
app.run(debug=True, port=port)