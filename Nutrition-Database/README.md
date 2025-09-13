# Nutrition Database

A comprehensive management interface for accessing USDA Food Data Central with Heart Portal integration.

## Features

- **Web-based Management UI**: Clean, responsive interface built with Flask
- **API Provider Management**: Add/remove/test nutrition API providers
- **Food Search**: Search across multiple nutrition databases simultaneously
- **Detailed Nutrition Data**: View comprehensive nutritional information
- **Connection Testing**: Test API connectivity and functionality
- **Real-time Results**: Live search results with detailed food information

## Supported APIs

- **USDA FoodData Central**: ✅ Fully implemented
- **Edamam**: 🚧 Coming soon
- **Spoonacular**: 🚧 Coming soon
- **Nutritionix**: 🚧 Coming soon

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to: `http://localhost:5000`

## API Keys

To use the nutrition APIs, you'll need to obtain API keys:

- **USDA FoodData Central**: Get your free API key at https://fdc.nal.usda.gov/api-key-signup.html

## Usage

### Adding API Providers

1. Select a provider from the dropdown
2. Enter your API key
3. Click "Add Provider"
4. Test the connection using the "Test" button

### Searching for Foods

1. Enter a food name or description in the search box
2. Set the number of results you want (1-50)
3. Click "Search Foods"
4. Click on any food item to view detailed nutritional information

### Testing Connections

- Use the "Test" button next to each provider to verify connectivity
- Use "Test All Connections" to test all configured providers at once

## File Structure

```
Nutrition-Database/
├── app.py                      # Flask web application
├── nutrition_api_manager.py    # Core nutrition API classes
├── requirements.txt           # Python dependencies
├── templates/
│   └── index.html            # Web interface template with sticky navigation
└── Test.py                   # Example usage script
```

## API Endpoints

The Flask app provides the following REST endpoints:

- `GET /api/providers` - List available and configured providers
- `POST /api/add-provider` - Add a new API provider
- `POST /api/remove-provider` - Remove an API provider
- `POST /api/search` - Search for foods across providers
- `POST /api/food-details` - Get detailed food information
- `POST /api/test-connection` - Test API provider connectivity

## Development

The application is built with:
- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Styling**: Modern, responsive design inspired by Apple's design system

## Example API Usage

```python
from nutrition_api_manager import NutritionAPIManager, USDAFoodDataAPI, APIProvider

# Initialize the manager
manager = NutritionAPIManager()

# Add USDA API
usda_api = USDAFoodDataAPI("your-api-key-here")
manager.add_api(APIProvider.USDA_FOODDATA, usda_api)

# Search for foods
results = manager.search_foods("chicken breast", limit=5)

# Get detailed information
food_details = manager.get_food_details(APIProvider.USDA_FOODDATA, "food_id")
```