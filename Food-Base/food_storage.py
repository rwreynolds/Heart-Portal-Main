"""
Food Storage Service
Handles all food storage operations and data processing
"""

from datetime import datetime, date
from database import db
from database.models import Food, Nutrient, FoodNutrient, FoodPortion, SearchHistory
from sqlalchemy.exc import IntegrityError
import json

class FoodStorageService:
    """Service for managing food storage operations"""
    
    def __init__(self):
        pass
    
    def save_food_from_api(self, food_data, ip_address=None):
        """
        Save a food item from API-Manager data
        
        Args:
            food_data: Dictionary containing food data from USDA API
            ip_address: Optional IP address for logging
            
        Returns:
            dict: Result with saved food info or error
        """
        try:
            # Extract FDC ID
            fdc_id = food_data.get('fdcId') or food_data.get('food_id')
            if not fdc_id:
                return {'error': 'No FDC ID found in food data'}
            
            # Check if food already exists
            existing_food = Food.query.filter_by(fdc_id=fdc_id).first()
            if existing_food:
                # Log the duplicate save attempt
                self._log_search_history(
                    action='duplicate_save',
                    food_id=existing_food.id,
                    ip_address=ip_address
                )
                return {
                    'message': 'Food already saved',
                    'food': existing_food.to_dict(),
                    'duplicate': True
                }
            
            # Create new food record
            food = self._create_food_from_api_data(food_data)
            db.session.add(food)
            db.session.flush()  # Get the ID
            
            # Save nutrients
            self._save_nutrients(food, food_data)
            
            # Save portions
            self._save_portions(food, food_data)
            
            # Commit all changes
            db.session.commit()
            
            # Log the successful save
            self._log_search_history(
                action='save',
                food_id=food.id,
                ip_address=ip_address
            )
            
            return {
                'message': 'Food saved successfully',
                'food': food.to_dict(),
                'duplicate': False
            }
            
        except IntegrityError as e:
            db.session.rollback()
            return {'error': f'Database integrity error: {str(e)}'}
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to save food: {str(e)}'}
    
    def _create_food_from_api_data(self, food_data):
        """Create Food model from API data"""
        # Parse dates
        published_date = None
        if food_data.get('publishedDate'):
            try:
                published_date = datetime.fromisoformat(food_data['publishedDate'].replace('Z', '+00:00')).date()
            except:
                pass
        
        # Create food instance
        food = Food(
            fdc_id=food_data.get('fdcId') or food_data.get('food_id'),
            description=food_data.get('description') or food_data.get('name', 'Unknown Food'),
            brand_owner=food_data.get('brandOwner') or food_data.get('brand_owner') or food_data.get('brand'),
            brand_name=food_data.get('brandName'),
            subbrand_name=food_data.get('subbrandName'),
            data_type=food_data.get('dataType') or food_data.get('data_type', 'Unknown'),
            food_category=food_data.get('foodCategory', {}).get('description') if isinstance(food_data.get('foodCategory'), dict) else food_data.get('foodCategory'),
            food_category_id=food_data.get('foodCategory', {}).get('id') if isinstance(food_data.get('foodCategory'), dict) else food_data.get('foodCategoryId'),
            published_date=published_date,
            ingredients=food_data.get('ingredients'),
            market_country=food_data.get('marketCountry'),
            serving_size=food_data.get('serving_size'),
            serving_size_unit=food_data.get('serving_unit'),
            household_serving_fulltext=food_data.get('householdServingFullText'),
            raw_data=json.dumps(food_data)  # Store complete API response as JSON string
        )
        
        return food
    
    def _save_nutrients(self, food, food_data):
        """Save nutrient data for a food"""
        nutrients_data = food_data.get('foodNutrients', [])
        
        for nutrient_data in nutrients_data:
            # Get nutrient info
            nutrient_info = nutrient_data.get('nutrient', {})
            nutrient_id = nutrient_info.get('id') or nutrient_data.get('nutrientId')
            amount = nutrient_data.get('amount') or nutrient_data.get('value')
            
            if not nutrient_id or amount is None:
                continue
            
            # Ensure nutrient exists in reference table
            self._ensure_nutrient_exists(nutrient_id, nutrient_info)
            
            # Create food-nutrient relationship
            food_nutrient = FoodNutrient(
                food_id=food.id,
                nutrient_id=nutrient_id,
                amount=float(amount),
                data_points=nutrient_data.get('dataPoints'),
                derivation_id=nutrient_data.get('derivationId'),
                min_value=nutrient_data.get('min'),
                max_value=nutrient_data.get('max'),
                median_value=nutrient_data.get('median'),
                footnote=nutrient_data.get('footnote'),
                min_year_acquired=nutrient_data.get('minYearAcquired')
            )
            
            db.session.add(food_nutrient)
    
    def _save_portions(self, food, food_data):
        """Save portion data for a food"""
        portions_data = food_data.get('foodPortions', [])
        
        for portion_data in portions_data:
            portion = FoodPortion(
                food_id=food.id,
                seq_num=portion_data.get('sequenceNumber'),
                amount=portion_data.get('amount', 1.0),
                measure_unit_id=portion_data.get('measureUnitId'),
                measure_unit_name=portion_data.get('measureUnitName'),
                measure_unit_abbreviation=portion_data.get('measureUnitAbbreviation'),
                modifier=portion_data.get('modifier'),
                gram_weight=portion_data.get('gramWeight', 100.0),
                data_points=portion_data.get('dataPoints'),
                footnote=portion_data.get('footnote'),
                min_year_acquired=portion_data.get('minYearAcquired')
            )
            
            db.session.add(portion)
    
    def _ensure_nutrient_exists(self, nutrient_id, nutrient_info):
        """Ensure nutrient exists in reference table"""
        existing = Nutrient.query.get(nutrient_id)
        if not existing:
            nutrient = Nutrient(
                id=nutrient_id,
                name=nutrient_info.get('name', f'Nutrient {nutrient_id}'),
                unit_name=nutrient_info.get('unitName', ''),
                nutrient_nbr=nutrient_info.get('number'),
                rank=nutrient_info.get('rank')
            )
            db.session.add(nutrient)
    
    def _log_search_history(self, action, search_query=None, food_id=None, ip_address=None):
        """Log user actions for analytics"""
        try:
            history = SearchHistory(
                search_query=search_query,
                food_id=food_id,
                action=action,
                ip_address=ip_address
            )
            db.session.add(history)
        except Exception:
            # Don't fail the main operation if logging fails
            pass
    
    def get_all_foods(self, limit=None, offset=None):
        """Get all saved foods with optional pagination"""
        query = Food.query.order_by(Food.saved_at.desc())
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        foods = query.all()
        return [food.to_dict() for food in foods]
    
    def get_food_by_id(self, food_id):
        """Get a specific food by ID"""
        food = Food.query.get(food_id)
        return food.to_dict() if food else None
    
    def get_food_by_fdc_id(self, fdc_id):
        """Get a specific food by FDC ID"""
        food = Food.query.filter_by(fdc_id=fdc_id).first()
        return food.to_dict() if food else None
    
    def update_food(self, food_id, update_data):
        """Update food information"""
        try:
            food = Food.query.get(food_id)
            if not food:
                return {'error': 'Food not found'}
            
            # Update allowed fields
            allowed_fields = [
                'description', 'brand_owner', 'brand_name', 'subbrand_name',
                'ingredients', 'market_country', 'serving_size', 'serving_size_unit'
            ]
            
            updated_fields = []
            for field in allowed_fields:
                if field in update_data:
                    setattr(food, field, update_data[field])
                    updated_fields.append(field)
            
            if not updated_fields:
                return {'error': 'No valid fields to update'}
            
            # Update the updated_at timestamp
            food.updated_at = datetime.utcnow()
            
            # Log the update
            self._log_search_history(action='update', food_id=food_id)
            
            db.session.commit()
            
            return {
                'message': 'Food updated successfully',
                'updated_fields': updated_fields,
                'food': food.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update food: {str(e)}'}

    def delete_food(self, food_id):
        """Delete a food by ID"""
        try:
            food = Food.query.get(food_id)
            if not food:
                return {'error': 'Food not found'}
            
            # Log the deletion
            self._log_search_history(action='delete', food_id=food_id)
            
            db.session.delete(food)
            db.session.commit()
            
            return {'message': 'Food deleted successfully'}
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete food: {str(e)}'}
    
    def search_foods(self, query, limit=50):
        """Search foods by description or brand"""
        if not query:
            return self.get_all_foods(limit=limit)
        
        # Log the search
        self._log_search_history(action='search', search_query=query)
        
        # Search in description and brand
        foods = Food.query.filter(
            db.or_(
                Food.description.ilike(f'%{query}%'),
                Food.brand_owner.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        return [food.to_dict() for food in foods]
    
    def get_foods_by_category(self, data_type, limit=50):
        """Get foods by data type category"""
        foods = Food.query.filter_by(data_type=data_type).limit(limit).all()
        return [food.to_dict() for food in foods]
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            total_foods = Food.query.count()
            unique_brands = db.session.query(Food.brand_owner).distinct().count()
            data_types = db.session.query(Food.data_type).distinct().count()
            
            # Get last saved food
            last_food = Food.query.order_by(Food.saved_at.desc()).first()
            last_saved = last_food.saved_at.isoformat() if last_food else None
            
            return {
                'total_foods': total_foods,
                'unique_brands': unique_brands,
                'data_types': data_types,
                'last_saved': last_saved
            }
        except Exception as e:
            return {
                'total_foods': 0,
                'unique_brands': 0,
                'data_types': 0,
                'last_saved': None,
                'error': str(e)
            }