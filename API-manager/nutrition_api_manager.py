"""
Nutrition API Manager
A Python module for managing multiple nutrition data API endpoints.
"""

import requests
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time


class APIProvider(Enum):
    USDA_FOODDATA = "usda_fooddata"
    EDAMAM = "edamam"
    SPOONACULAR = "spoonacular"
    NUTRITIONIX = "nutritionix"


@dataclass
class NutritionData:
    """Standardized nutrition data structure"""
    food_id: str
    name: str
    brand: Optional[str]
    serving_size: Optional[str]
    calories: Optional[float]
    protein: Optional[float]  # grams
    carbs: Optional[float]    # grams
    fat: Optional[float]      # grams
    fiber: Optional[float]    # grams
    sugar: Optional[float]    # grams
    sodium: Optional[float]   # mg
    raw_data: Dict[str, Any]
    source: str


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass


class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        now = time.time()
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.calls.append(now)


class BaseNutritionAPI(ABC):
    """Abstract base class for nutrition APIs"""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: Optional[tuple] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(*rate_limit) if rate_limit else None
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'NutritionAPIManager/1.0',
            'Content-Type': 'application/json',
            'X-API-HEARS': "Ocnd7wcThywKAMRJM0QCbtNsXhs77wNnNXtBvJCt"
        })
    
    @abstractmethod
    def search_foods(self, query: str, limit: int = 10) -> List[NutritionData]:
        """Search for foods by name/description"""
        pass
    
    @abstractmethod
    def get_food_details(self, food_id: str) -> NutritionData:
        """Get detailed nutrition information for a specific food"""
        pass
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with rate limiting and error handling"""
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")


class USDAFoodDataAPI(BaseNutritionAPI):
    """USDA FoodData Central API implementation"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    def __init__(self, api_key: str):
        # USDA has generous rate limits, but we'll be conservative
        super().__init__(api_key, rate_limit=(1000, 3600))  # 1000 calls per hour
        
        # Add API key to headers
        if self.api_key:
            self.session.headers['X-API-Key'] = self.api_key
    
    def search_foods(self, query: str, limit: int = 10) -> List[NutritionData]:
        """Search for foods using USDA FoodData Central"""
        params = {
            'query': query,
            'pageSize': min(limit, 200),  # USDA max is 200
            'dataType': ['Branded', 'Foundation', 'SR Legacy']
        }
        
        url = f"{self.BASE_URL}/foods/search"
        data = self._make_request(url, params)
        
        results = []
        for food in data.get('foods', []):
            nutrition_data = self._parse_usda_food(food)
            results.append(nutrition_data)
        
        return results
    
    def get_food_details(self, food_id: str) -> NutritionData:
        """Get detailed food information by FDC ID"""
        url = f"{self.BASE_URL}/food/{food_id}"
        data = self._make_request(url)
        return self._parse_usda_food(data)
    
    def _parse_usda_food(self, food_data: Dict) -> NutritionData:
        """Parse USDA food data into standardized format"""
        
        # Extract basic info
        food_id = str(food_data.get('fdcId', ''))
        name = food_data.get('description', '')
        brand = food_data.get('brandOwner') or food_data.get('brandName')
        
        # Parse serving size
        serving_size = None
        portions = food_data.get('foodPortions', [])
        if portions:
            portion = portions[0]
            serving_size = f"{portion.get('amount', '')} {portion.get('modifier', '')}".strip()
        
        # Extract nutrients
        nutrients = {}
        for nutrient in food_data.get('foodNutrients', []):
            nutrient_name = nutrient.get('nutrient', {}).get('name', '').lower()
            nutrient_value = nutrient.get('amount')
            
            if nutrient_value is not None:
                nutrients[nutrient_name] = float(nutrient_value)
        
        # Map to standardized fields
        calories = nutrients.get('energy') or nutrients.get('energy (atwater general factors)')
        protein = nutrients.get('protein')
        carbs = nutrients.get('carbohydrate, by difference')
        fat = nutrients.get('total lipid (fat)')
        fiber = nutrients.get('fiber, total dietary')
        sugar = nutrients.get('sugars, total including nlea')
        sodium = nutrients.get('sodium')
        
        return NutritionData(
            food_id=food_id,
            name=name,
            brand=brand,
            serving_size=serving_size,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            sodium=sodium,
            raw_data=food_data,
            source=APIProvider.USDA_FOODDATA.value
        )


class NutritionAPIManager:
    """Main manager class for coordinating multiple nutrition APIs"""
    
    def __init__(self):
        self.apis: Dict[APIProvider, BaseNutritionAPI] = {}
    
    def add_api(self, provider: APIProvider, api_instance: BaseNutritionAPI):
        """Add an API provider to the manager"""
        self.apis[provider] = api_instance
    
    def remove_api(self, provider: APIProvider):
        """Remove an API provider from the manager"""
        if provider in self.apis:
            del self.apis[provider]
    
    def search_foods(self, query: str, providers: Optional[List[APIProvider]] = None, 
                    limit: int = 10) -> Dict[str, List[NutritionData]]:
        """Search across multiple API providers"""
        if providers is None:
            providers = list(self.apis.keys())
        
        results = {}
        for provider in providers:
            if provider in self.apis:
                try:
                    api_results = self.apis[provider].search_foods(query, limit)
                    results[provider.value] = api_results
                except APIError as e:
                    print(f"Error searching {provider.value}: {e}")
                    results[provider.value] = []
        
        return results
    
    def get_food_details(self, provider: APIProvider, food_id: str) -> Optional[NutritionData]:
        """Get detailed food information from a specific provider"""
        if provider not in self.apis:
            raise ValueError(f"Provider {provider.value} not available")
        
        try:
            return self.apis[provider].get_food_details(food_id)
        except APIError as e:
            print(f"Error getting food details from {provider.value}: {e}")
            return None
    
    def get_available_providers(self) -> List[APIProvider]:
        """Get list of available API providers"""
        return list(self.apis.keys())


# Example usage
if __name__ == "__main__":
    # Initialize the manager
    manager = NutritionAPIManager()
    
    # Add USDA API (requires API key)
    usda_api_key = "T4icWj0OuaPliFh96iwKJiAty3vnPI5diCYPDP21"  # Get from https://fdc.nal.usda.gov/api-key-signup.html
    usda_api = USDAFoodDataAPI(usda_api_key)
    manager.add_api(APIProvider.USDA_FOODDATA, usda_api)
    
    # Search for foods
    print("Searching for food...")
    results = manager.search_foods("salt", limit=10)
    
    for provider, foods in results.items():
        print(f"\n{provider} results:")
        for food in foods[:3]:  # Show first 3 results
            print(f"  - {food.name}")
            if food.brand:
                print(f"    Brand: {food.brand}")
            if food.calories:
                print(f"    Calories: {food.calories}")
            print()
    
    # Get detailed information for a specific food
    if results and APIProvider.USDA_FOODDATA.value in results:
        first_food = results[APIProvider.USDA_FOODDATA.value][0]
        print(f"Getting details for: {first_food.name}")
        details = manager.get_food_details(APIProvider.USDA_FOODDATA, first_food.food_id)
        if details:
            print(f"  Brand: {details.brand}")
            print(f"")
            print(f"Detailed nutrition info:")
            print(f"  Calories: {details.calories}")
            print(f"  Protein: {details.protein}g")
            print(f"  Carbs: {details.carbs}g")
            print(f"  Fat: {details.fat}g")
            print(f"  Sodium: {details.sodium}g")
            print(f"  Serving Size: {details.serving_size}g")
            print(f"  Sugar: {details.sugar}g")