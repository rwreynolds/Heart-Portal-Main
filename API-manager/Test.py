from nutrition_api_manager import NutritionAPIManager, USDAFoodDataAPI, APIProvider

# Initialize
manager = NutritionAPIManager()
usda_api = USDAFoodDataAPI("T4icWj0OuaPliFh96iwKJiAty3vnPI5diCYPDP21")
manager.add_api(APIProvider.USDA_FOODDATA, usda_api)

# Search for foods
results = manager.search_foods("coca cola", limit=5)

# Get detailed nutrition info
food_details = manager.get_food_details(APIProvider.USDA_FOODDATA, "1105073")
print(f"  Information: {food_details.raw_data.description}g")
