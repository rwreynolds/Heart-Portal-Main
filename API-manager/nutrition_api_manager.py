"""
Nutrition API Manager - Base classes and implementations
"""

import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class APIProvider(Enum):
    """Enumeration of supported API providers"""
    USDA_FOODDATA = "usda_fooddata"
    EDAMAM = "edamam"
    SPOONACULAR = "spoonacular"
    NUTRITIONIX = "nutritionix"


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass


class NutritionAPIManager:
    """Base manager for nutrition APIs"""
    
    def __init__(self):
        self.apis = {}
    
    def add_api(self, provider: APIProvider, api_instance):
        """Add an API instance to the manager"""
        self.apis[provider.value] = api_instance
    
    def remove_api(self, provider: APIProvider):
        """Remove an API instance from the manager"""
        if provider.value in self.apis:
            del self.apis[provider.value]
    
    def get_api(self, provider: APIProvider):
        """Get an API instance"""
        return self.apis.get(provider.value)
    
    def list_apis(self) -> List[str]:
        """List all configured API providers"""
        return list(self.apis.keys())


class USDAFoodDataAPI:
    """Basic USDA FoodData Central API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
    
    def search_foods(self, query: str, page_size: int = 25) -> Dict[str, Any]:
        """Simple food search"""
        params = {
            'query': query,
            'pageSize': page_size
        }
        return self._make_request("foods/search", params)
    
    def get_food(self, fdc_id: int) -> Dict[str, Any]:
        """Get specific food by FDC ID"""
        return self._make_request(f"food/{fdc_id}")
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            result = self.search_foods("apple", page_size=1)
            return result.get("totalHits", 0) >= 0
        except:
            return False


class DataType(Enum):
    """Available data types in FoodData Central"""
    FOUNDATION = "Foundation"
    SR_LEGACY = "SR Legacy" 
    SURVEY = "Survey (FNDDS)"
    BRANDED = "Branded"
    EXPERIMENTAL = "Experimental"


class SortBy(Enum):
    """Available sort options"""
    DATA_TYPE = "dataType.keyword"
    DESCRIPTION = "lowercaseDescription.keyword"
    FDC_ID = "fdcId"
    PUBLISHED_DATE = "publishedDate"


@dataclass
class SearchCriteria:
    """Search criteria for foods/search endpoint"""
    query: str
    data_type: Optional[List[DataType]] = None
    page_size: int = 50
    page_number: int = 1
    sort_by: Optional[SortBy] = None
    sort_order: str = "asc"
    brand_owner: Optional[str] = None


@dataclass
class ListCriteria:
    """Criteria for foods/list endpoint"""
    data_type: Optional[List[DataType]] = None
    page_size: int = 50
    page_number: int = 1
    sort_by: Optional[SortBy] = None
    sort_order: str = "asc"


class EnhancedUSDAFoodDataAPI:
    """Enhanced USDA FoodData Central API client with all endpoints"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to parameters
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        try:
            if method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            else:
                response = self.session.get(url, params=params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
    
    def search_foods(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """
        Search for foods using the foods/search endpoint
        Enhanced version with full search criteria support
        """
        search_data = {
            "query": criteria.query,
            "pageSize": criteria.page_size,
            "pageNumber": criteria.page_number,
            "sortOrder": criteria.sort_order
        }
        
        # Add optional parameters
        if criteria.data_type:
            search_data["dataType"] = [dt.value for dt in criteria.data_type]
        
        if criteria.sort_by:
            search_data["sortBy"] = criteria.sort_by.value
            
        if criteria.brand_owner:
            search_data["brandOwner"] = criteria.brand_owner
        
        return self._make_request("foods/search", method="POST", data=search_data)
    
    def get_foods_list(self, criteria: ListCriteria) -> Dict[str, Any]:
        """
        Get paginated list of foods using foods/list endpoint
        """
        list_data = {
            "pageSize": criteria.page_size,
            "pageNumber": criteria.page_number,
            "sortOrder": criteria.sort_order
        }
        
        # Add optional parameters
        if criteria.data_type:
            list_data["dataType"] = [dt.value for dt in criteria.data_type]
            
        if criteria.sort_by:
            list_data["sortBy"] = criteria.sort_by.value
        
        return self._make_request("foods/list", method="POST", data=list_data)
    
    def get_multiple_foods(self, fdc_ids: List[int], nutrients: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Get multiple foods by FDC IDs using foods endpoint
        """
        foods_data = {
            "fdcIds": fdc_ids
        }
        
        if nutrients:
            foods_data["nutrients"] = nutrients
            
        return self._make_request("foods", method="POST", data=foods_data)
    
    def get_food_details(self, fdc_id: int, nutrients: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Get detailed food information by FDC ID
        Enhanced version with nutrient filtering
        """
        params = {}
        if nutrients:
            params["nutrients"] = ",".join(map(str, nutrients))
            
        return self._make_request(f"food/{fdc_id}", params=params)
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try a simple search to test connectivity
            criteria = SearchCriteria(query="apple", page_size=1)
            result = self.search_foods(criteria)
            return result.get("totalHits", 0) >= 0
        except:
            return False
    
    def get_data_types(self) -> List[str]:
        """Get available data types"""
        return [dt.value for dt in DataType]


class EnhancedNutritionAPIManager:
    """Enhanced manager with new USDA endpoints"""
    
    def __init__(self):
        self.apis = {}
        
    def add_enhanced_usda_api(self, api_key: str):
        """Add enhanced USDA API with all endpoints"""
        api = EnhancedUSDAFoodDataAPI(api_key)
        self.apis["usda_enhanced"] = api
        return api
    
    def browse_foods_by_category(self, data_type: DataType, page_size: int = 20, page_number: int = 1) -> Dict:
        """Browse foods by data type category"""
        if "usda_enhanced" not in self.apis:
            raise APIError("Enhanced USDA API not configured")
            
        api = self.apis["usda_enhanced"]
        criteria = ListCriteria(
            data_type=[data_type],
            page_size=page_size,
            page_number=page_number,
            sort_by=SortBy.DESCRIPTION
        )
        return api.get_foods_list(criteria)
    
    def advanced_search(self, query: str, data_types: Optional[List[DataType]] = None, 
                       brand_owner: Optional[str] = None, sort_by: Optional[SortBy] = None) -> Dict:
        """Advanced search with filtering options"""
        if "usda_enhanced" not in self.apis:
            raise APIError("Enhanced USDA API not configured")
            
        api = self.apis["usda_enhanced"]
        criteria = SearchCriteria(
            query=query,
            data_type=data_types,
            brand_owner=brand_owner,
            sort_by=sort_by,
            page_size=25
        )
        return api.search_foods(criteria)
    
    def compare_foods(self, fdc_ids: List[int], nutrients: Optional[List[int]] = None) -> Dict:
        """Compare multiple foods side by side"""
        if "usda_enhanced" not in self.apis:
            raise APIError("Enhanced USDA API not configured")
            
        api = self.apis["usda_enhanced"]
        return api.get_multiple_foods(fdc_ids, nutrients)