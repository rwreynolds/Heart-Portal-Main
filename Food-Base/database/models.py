"""
SQLAlchemy models for Food-Base database
Stores comprehensive food and nutrition data
"""

from . import db
from datetime import datetime
from sqlalchemy import Text, JSON
from sqlalchemy.orm import relationship

class Food(db.Model):
    """Main food items table"""
    __tablename__ = 'foods'
    
    # Primary identifiers
    id = db.Column(db.Integer, primary_key=True)
    fdc_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    
    # Basic food information
    description = db.Column(db.String(500), nullable=False)
    brand_owner = db.Column(db.String(200))
    brand_name = db.Column(db.String(200))
    subbrand_name = db.Column(db.String(200))
    
    # Classification
    data_type = db.Column(db.String(50), nullable=False, index=True)
    food_category = db.Column(db.String(200))
    food_category_id = db.Column(db.Integer)
    
    # Publication info
    published_date = db.Column(db.Date)
    modified_date = db.Column(db.Date)
    available_date = db.Column(db.Date)
    
    # Additional details
    ingredients = db.Column(Text)
    market_country = db.Column(db.String(50))
    serving_size = db.Column(db.Float)
    serving_size_unit = db.Column(db.String(20))
    household_serving_fulltext = db.Column(db.String(200))
    
    # Storage metadata
    saved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Store raw API response for future reference
    raw_data = db.Column(JSON)
    
    # Relationships
    nutrients = relationship('FoodNutrient', back_populates='food', cascade='all, delete-orphan')
    portions = relationship('FoodPortion', back_populates='food', cascade='all, delete-orphan')
    collections = relationship('FoodCollection', back_populates='food', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Food {self.fdc_id}: {self.description[:50]}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'fdc_id': self.fdc_id,
            'fdcId': self.fdc_id,  # For compatibility with API-Manager
            'description': self.description,
            'name': self.description,  # For compatibility
            'brand_owner': self.brand_owner,
            'brandOwner': self.brand_owner,  # For compatibility
            'brand': self.brand_owner,  # For compatibility
            'brand_name': self.brand_name,
            'subbrand_name': self.subbrand_name,
            'data_type': self.data_type,
            'dataType': self.data_type,  # For compatibility
            'food_category': self.food_category,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'publishedDate': self.published_date.isoformat() if self.published_date else None,
            'ingredients': self.ingredients,
            'market_country': self.market_country,
            'serving_size': self.serving_size,
            'serving_unit': self.serving_size_unit,
            'saved_at': self.saved_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'nutrients': [n.to_dict() for n in self.nutrients],
            'portions': [p.to_dict() for p in self.portions]
        }
    
    def get_nutrient_value(self, nutrient_id):
        """Get specific nutrient value"""
        nutrient = next((n for n in self.nutrients if n.nutrient_id == nutrient_id), None)
        return nutrient.amount if nutrient else None
    
    @property
    def calories(self):
        """Energy in kcal (nutrient ID 1008)"""
        return self.get_nutrient_value(1008)
    
    @property
    def protein(self):
        """Protein in grams (nutrient ID 1003)"""
        return self.get_nutrient_value(1003)
    
    @property
    def carbs(self):
        """Carbohydrates in grams (nutrient ID 1005)"""
        return self.get_nutrient_value(1005)
    
    @property
    def fat(self):
        """Total fat in grams (nutrient ID 1004)"""
        return self.get_nutrient_value(1004)
    
    @property
    def sodium(self):
        """Sodium in milligrams (nutrient ID 1093)"""
        return self.get_nutrient_value(1093)

class Nutrient(db.Model):
    """Reference table for nutrients"""
    __tablename__ = 'nutrients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    unit_name = db.Column(db.String(50), nullable=False)
    nutrient_nbr = db.Column(db.Float)
    rank = db.Column(db.Integer)
    
    # Relationships
    food_nutrients = relationship('FoodNutrient', back_populates='nutrient')
    
    def __repr__(self):
        return f'<Nutrient {self.id}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit_name': self.unit_name,
            'nutrient_nbr': self.nutrient_nbr,
            'rank': self.rank
        }

class FoodNutrient(db.Model):
    """Junction table linking foods to their nutrient values"""
    __tablename__ = 'food_nutrients'
    
    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    nutrient_id = db.Column(db.Integer, db.ForeignKey('nutrients.id'), nullable=False)
    
    # Nutrient values
    amount = db.Column(db.Float, nullable=False)
    data_points = db.Column(db.Integer)
    derivation_id = db.Column(db.Integer)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    median_value = db.Column(db.Float)
    footnote = db.Column(db.String(500))
    min_year_acquired = db.Column(db.Integer)
    
    # Relationships
    food = relationship('Food', back_populates='nutrients')
    nutrient = relationship('Nutrient', back_populates='food_nutrients')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('food_id', 'nutrient_id'),)
    
    def __repr__(self):
        return f'<FoodNutrient F:{self.food_id} N:{self.nutrient_id} = {self.amount}>'
    
    def to_dict(self):
        return {
            'nutrient_id': self.nutrient_id,
            'nutrientId': self.nutrient_id,  # For compatibility
            'amount': self.amount,
            'value': self.amount,  # For compatibility
            'unit': self.nutrient.unit_name if self.nutrient else None,
            'name': self.nutrient.name if self.nutrient else None,
            'data_points': self.data_points,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'median_value': self.median_value,
            'nutrient': {
                'id': self.nutrient_id,
                'name': self.nutrient.name if self.nutrient else None,
                'unitName': self.nutrient.unit_name if self.nutrient else None
            } if self.nutrient else None
        }

class FoodPortion(db.Model):
    """Food serving portions/measures"""
    __tablename__ = 'food_portions'
    
    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    
    # Portion details
    seq_num = db.Column(db.Integer)
    amount = db.Column(db.Float, nullable=False)
    measure_unit_id = db.Column(db.Integer)
    measure_unit_name = db.Column(db.String(100))
    measure_unit_abbreviation = db.Column(db.String(20))
    modifier = db.Column(db.String(200))
    gram_weight = db.Column(db.Float, nullable=False)
    data_points = db.Column(db.Integer)
    footnote = db.Column(db.String(500))
    min_year_acquired = db.Column(db.Integer)
    
    # Relationships
    food = relationship('Food', back_populates='portions')
    
    def __repr__(self):
        return f'<FoodPortion {self.amount} {self.modifier} = {self.gram_weight}g>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'seq_num': self.seq_num,
            'amount': self.amount,
            'measure_unit_name': self.measure_unit_name,
            'modifier': self.modifier,
            'gram_weight': self.gram_weight,
            'data_points': self.data_points
        }

class Collection(db.Model):
    """User-defined collections/categories for organizing foods"""
    __tablename__ = 'collections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(500))
    color = db.Column(db.String(7), default='#007aff')  # Hex color code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    foods = relationship('FoodCollection', back_populates='collection', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Collection {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat(),
            'food_count': len(self.foods)
        }

class FoodCollection(db.Model):
    """Junction table for foods in collections"""
    __tablename__ = 'food_collections'
    
    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    food = relationship('Food', back_populates='collections')
    collection = relationship('Collection', back_populates='foods')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('food_id', 'collection_id'),)
    
    def __repr__(self):
        return f'<FoodCollection F:{self.food_id} C:{self.collection_id}>'

class SearchHistory(db.Model):
    """Track user searches and food saves"""
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(200))
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'))
    action = db.Column(db.String(50), nullable=False)  # 'search', 'save', 'view', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # Support IPv6
    
    # Relationships
    food = relationship('Food')
    
    def __repr__(self):
        return f'<SearchHistory {self.action}: {self.search_query or self.food_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'search_query': self.search_query,
            'food_id': self.food_id,
            'action': self.action,
            'timestamp': self.timestamp.isoformat(),
            'food_name': self.food.description if self.food else None
        }