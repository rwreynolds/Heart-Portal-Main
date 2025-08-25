"""
Enhanced Nutrition API Manager with persistence support
"""

import os
from dotenv import load_dotenv
import json
from pathlib import Path
from nutrition_api_manager import (
    NutritionAPIManager,
    USDAFoodDataAPI,
    APIProvider,
    APIError
)

# Load environment variables from .env file
load_dotenv()

class APIKeyManager:
    """Manages API keys with environment variable fallback"""
    
    def __init__(self, config_file: str = "api_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file with environment variable fallback"""
        config = {}
        
        # Try to load from config file first
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError):
                config = {}
        
        # Override with environment variables if they exist
        env_mappings = {
            'usda_fooddata': 'USDA_API_KEY',
            'edamam': 'EDAMAM_API_KEY',
            'spoonacular': 'SPOONACULAR_API_KEY',
            'nutritionix': 'NUTRITIONIX_API_KEY'
        }
        
        for provider, env_var in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                config[provider] = env_value
        
        return config
    
    def save_api_key(self, provider: str, api_key: str):
        """Save API key to config file"""
        self.config[provider] = api_key
        self._save_config()
    
    def get_api_key(self, provider: str) -> str:
        """Get API key for provider"""
        return self.config.get(provider)
    
    def remove_api_key(self, provider: str):
        """Remove API key for provider"""
        if provider in self.config:
            del self.config[provider]
            self._save_config()
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            # Only save keys that are not from environment variables
            env_mappings = {
                'usda_fooddata': 'USDA_API_KEY',
                'edamam': 'EDAMAM_API_KEY', 
                'spoonacular': 'SPOONACULAR_API_KEY',
                'nutritionix': 'NUTRITIONIX_API_KEY'
            }
            
            config_to_save = {}
            for provider, api_key in self.config.items():
                # Only save to file if not set via environment variable
                env_var = env_mappings.get(provider)
                if not env_var or not os.getenv(env_var):
                    config_to_save[provider] = api_key
            
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=2)
        except IOError as e:
            raise APIError(f"Failed to save configuration: {e}")
    
    def get_configured_providers(self) -> list:
        """Get list of providers with configured API keys"""
        return list(self.config.keys())


class EnhancedNutritionAPIManager(NutritionAPIManager):
    """Enhanced manager with API key persistence"""
    
    def __init__(self, config_file: str = "api_config.json"):
        super().__init__()
        self.key_manager = APIKeyManager(config_file)
        self._load_saved_apis()
    
    def _load_saved_apis(self):
        """Load previously configured APIs from saved keys"""
        for provider_name in self.key_manager.get_configured_providers():
            try:
                provider = APIProvider(provider_name)
                api_key = self.key_manager.get_api_key(provider_name)
                
                if provider == APIProvider.USDA_FOODDATA:
                    api_instance = USDAFoodDataAPI(api_key)
                    self.add_api(provider, api_instance)
                # Add other providers as they're implemented
                
            except (ValueError, APIError) as e:
                print(f"Failed to load {provider_name}: {e}")
    
    def add_api_with_persistence(self, provider: APIProvider, api_key: str):
        """Add API and persist the key"""
        # Save the key
        self.key_manager.save_api_key(provider.value, api_key)
        
        # Create and add the API instance
        if provider == APIProvider.USDA_FOODDATA:
            api_instance = USDAFoodDataAPI(api_key)
            self.add_api(provider, api_instance)
        # Add other providers as implemented
        
    def remove_api_with_persistence(self, provider: APIProvider):
        """Remove API and delete the persisted key"""
        self.remove_api(provider)
        self.key_manager.remove_api_key(provider.value)