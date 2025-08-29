# 🍎 Enhanced Nutrition API Manager - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Getting Started](#getting-started)
4. [API Configuration](#api-configuration)
5. [Features Guide](#features-guide)
6. [API Endpoints](#api-endpoints)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

---

## Overview

The Enhanced Nutrition API Manager is a comprehensive Flask web application for accessing and managing nutrition data from the USDA FoodData Central API. It provides an intuitive web interface for searching, browsing, and comparing food nutrition information.

### Key Features
- 🔍 **Advanced Search** - Search foods with multiple filters
- 📊 **Food Browsing** - Browse foods by category/data type
- ⚖️ **Food Comparison** - Compare nutritional profiles side-by-side
- 📈 **Analytics** - Database insights and statistics
- 🔑 **API Management** - Easy API key configuration with persistence

---

## Installation & Setup

### Prerequisites
- Python 3.7+
- pip package manager
- USDA FoodData Central API key (free from [https://fdc.nal.usda.gov/api-guide.html](https://fdc.nal.usda.gov/api-guide.html))

### Installation Steps

1. **Clone/Download the Project**
   ```bash
   cd /path/to/Heart-Portal-Main/API-manager
   ```

2. **Install Dependencies**
   ```bash
   pip install flask requests python-dotenv
   ```

3. **Get USDA API Key**
   - Visit [USDA FoodData Central API](https://fdc.nal.usda.gov/api-guide.html)
   - Sign up for a free API key
   - Keep your API key handy for configuration

4. **Start the Application**
   ```bash
   python app.py
   ```
   The app will start on `http://127.0.0.1:5000`

---

## Getting Started

### First-Time Setup

1. **Access the Application**
   - Open your browser and go to `http://127.0.0.1:5000`
   - You'll see the Enhanced Nutrition API Manager interface

2. **Configure API Access**
   - In the "Enhanced API Providers" section
   - Enter your USDA API key
   - Click "Add Enhanced Provider"
   - Wait for confirmation message

3. **Load Data Types**
   - Click "Load Data Types" to populate available food categories
   - This enables filtering options in search and browse features

---

## API Configuration

### Method 1: Web Interface (Recommended)
1. Enter your USDA API key in the web interface
2. Click "Add Enhanced Provider"
3. API key is automatically saved for future sessions

### Method 2: Environment Variables
Create a `.env` file in the API-manager directory:
```env
USDA_API_KEY=your_api_key_here
```

### Method 3: Configuration File
The app automatically creates `api_config.json` to store API keys securely.

---

## Features Guide

### 🔍 Advanced Search

**Purpose**: Search for specific foods with advanced filtering options

**How to Use**:
1. Navigate to the "Advanced Search" tab
2. Enter your search query (e.g., "chicken breast", "organic milk")
3. **Optional Filters**:
   - **Brand Owner**: Filter by specific brand (e.g., "General Mills")
   - **Data Types**: Select food categories to include
   - **Sort Options**: Choose how to sort results
4. Click "Advanced Search"
5. Browse paginated results
6. Click any food item to view detailed nutrition information
7. Use "+ Compare" button to add foods to comparison list

**Tips**:
- Be specific in search terms for better results
- Use data type filters to narrow results (e.g., only "Foundation" foods)
- Try different sort options for different perspectives

### 📊 Browse Foods

**Purpose**: Explore foods by category without specific search terms

**How to Use**:
1. Navigate to the "Browse Foods" tab
2. Select one or more food categories (data types)
3. Choose items per page (10-100)
4. Click "Browse Foods"
5. Navigate through pages of results
6. Use "Random Sample" for quick exploration

**Available Categories**:
- **Foundation Foods**: Core foods with comprehensive nutrient profiles
- **SR Legacy**: Standard Reference legacy data
- **Survey (FNDDS)**: Food and Nutrient Database for Dietary Studies
- **Branded Foods**: Commercial branded products
- **Experimental Foods**: Research and experimental data

### ⚖️ Compare Foods

**Purpose**: Side-by-side nutritional comparison of multiple foods

**How to Use**:

**Method 1: From Search Results**
1. Search or browse for foods
2. Click "+ Compare" on foods you want to compare
3. Selected foods appear in the comparison panel
4. Click "Compare Selected Foods"

**Method 2: Direct FDC IDs**
1. Navigate to "Compare Foods" tab
2. Enter FDC IDs separated by commas (e.g., "170148,170149,170150")
3. Click "Compare by IDs"

**Comparison Features**:
- Side-by-side nutrient comparison table
- Common nutrients highlighted (calories, protein, fat, carbs, etc.)
- Remove foods from comparison easily
- Maximum 20 foods can be compared at once

### 📈 Analytics

**Purpose**: Get insights into the USDA database structure

**Features**:
- Database statistics by food category
- Sample data export capabilities
- Usage analytics (planned)

---

## API Endpoints

The application provides REST API endpoints for programmatic access:

### Core Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Main application interface |
| `/api/advanced-search` | POST | Advanced food search |
| `/api/foods-list` | POST | Browse foods by category |
| `/api/compare-foods` | POST | Compare multiple foods |
| `/api/data-types` | GET | Get available data types |
| `/api/nutrients-list` | GET | Get common nutrients list |
| `/api/add-enhanced-provider` | POST | Configure API provider |

### Example API Usage

**Search Foods**:
```javascript
fetch('/api/advanced-search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: 'chicken breast',
        dataTypes: ['Foundation', 'Branded'],
        sortBy: 'description',
        pageSize: 25
    })
})
```

**Compare Foods**:
```javascript
fetch('/api/compare-foods', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        fdcIds: [170148, 170149, 170150]
    })
})
```

---

## Troubleshooting

### Common Issues

#### 1. "Address already in use" Error
**Problem**: Port 5000 is already occupied
**Solutions**:
- **Option A**: Kill existing process
  ```bash
  lsof -ti :5000 | xargs kill -9
  ```
- **Option B**: Use different port
  ```bash
  python -c "from app import app; app.run(debug=True, port=5001)"
  ```
- **Option C**: Stop VS Code debugger if running

#### 2. "Import could not be resolved" Error
**Problem**: Module import issues
**Solutions**:
- Ensure you're in the correct directory: `API-manager/`
- Install required packages: `pip install flask requests python-dotenv`
- Check Python path and virtual environment

#### 3. API Key Not Working
**Problem**: USDA API requests failing
**Solutions**:
- Verify API key is correct and active
- Check USDA API status: [https://fdc.nal.usda.gov/](https://fdc.nal.usda.gov/)
- Ensure internet connectivity
- Try re-entering the API key

#### 4. Empty Search Results
**Problem**: No results returned from searches
**Solutions**:
- Try broader search terms
- Remove data type filters
- Check API key configuration
- Verify USDA API is responding

#### 5. Frontend Not Loading
**Problem**: Web interface doesn't display correctly
**Solutions**:
- Clear browser cache
- Check browser console for JavaScript errors
- Ensure Flask app is running
- Try different browser

### Debug Mode

Enable detailed error logging:
```python
app.run(debug=True, port=5000)
```

### Log Files

Check terminal output for detailed error messages when running the Flask app.

---

## Advanced Usage

### Environment Configuration

Create `.env` file for advanced configuration:
```env
# API Keys
USDA_API_KEY=your_usda_key_here
EDAMAM_API_KEY=your_edamam_key_here
SPOONACULAR_API_KEY=your_spoonacular_key_here
NUTRITIONIX_API_KEY=your_nutritionix_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Custom Nutrient Analysis

The system supports filtering by specific nutrient IDs. Common nutrient IDs:

| Nutrient | ID | Unit |
|----------|-----|------|
| Energy | 1008 | kcal |
| Protein | 1003 | g |
| Total Fat | 1004 | g |
| Carbohydrates | 1005 | g |
| Fiber | 1079 | g |
| Sugars | 2000 | g |
| Sodium | 1093 | mg |
| Calcium | 1087 | mg |
| Iron | 1089 | mg |
| Vitamin A | 1106 | µg |
| Vitamin C | 1162 | mg |

### Batch Food Comparison

For comparing large numbers of foods programmatically:

```python
import requests

# Compare up to 20 foods at once
fdc_ids = [170148, 170149, 170150, 170151, 170152]
nutrients = [1008, 1003, 1004, 1005]  # calories, protein, fat, carbs

response = requests.post('http://127.0.0.1:5000/api/compare-foods', json={
    'fdcIds': fdc_ids,
    'nutrients': nutrients
})

comparison_data = response.json()
```

### Integration with Other Applications

The API endpoints can be integrated into other applications:

- **Nutrition tracking apps**: Use search and detail endpoints
- **Recipe analysis**: Compare ingredients nutritionally
- **Research tools**: Batch analyze food databases
- **Mobile apps**: RESTful API suitable for mobile integration

---

## Support & Resources

### Documentation
- [USDA FoodData Central API Guide](https://fdc.nal.usda.gov/api-guide.html)
- [Flask Documentation](https://flask.palletsprojects.com/)

### Data Sources
- **Foundation Foods**: Research-grade data for key foods
- **SR Legacy**: Historical Standard Reference data
- **FNDDS**: Survey data from dietary studies
- **Branded Foods**: Label data from commercial products

### Getting Help
- Check this user guide first
- Review troubleshooting section
- Check browser console for JavaScript errors
- Verify API key and internet connectivity

---

*Last Updated: 2025*
*Version: 1.0*