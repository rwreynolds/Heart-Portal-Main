-- Food-Base Database Schema
-- SQLite database schema for comprehensive food and nutrition storage

-- Main foods table - stores core food information
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fdc_id INTEGER UNIQUE NOT NULL,
    description VARCHAR(500) NOT NULL,
    brand_owner VARCHAR(200),
    brand_name VARCHAR(200),
    subbrand_name VARCHAR(200),
    data_type VARCHAR(50) NOT NULL,
    food_category VARCHAR(200),
    food_category_id INTEGER,
    published_date DATE,
    modified_date DATE,
    available_date DATE,
    ingredients TEXT,
    market_country VARCHAR(50),
    serving_size REAL,
    serving_size_unit VARCHAR(20),
    household_serving_fulltext VARCHAR(200),
    saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_data JSON
);

-- Nutrients reference table
CREATE TABLE IF NOT EXISTS nutrients (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    unit_name VARCHAR(50) NOT NULL,
    nutrient_nbr REAL,
    rank INTEGER
);

-- Food-Nutrient junction table with values
CREATE TABLE IF NOT EXISTS food_nutrients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    nutrient_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    data_points INTEGER,
    derivation_id INTEGER,
    min_value REAL,
    max_value REAL,
    median_value REAL,
    footnote VARCHAR(500),
    min_year_acquired INTEGER,
    FOREIGN KEY (food_id) REFERENCES foods (id) ON DELETE CASCADE,
    FOREIGN KEY (nutrient_id) REFERENCES nutrients (id),
    UNIQUE (food_id, nutrient_id)
);

-- Food portions/serving sizes
CREATE TABLE IF NOT EXISTS food_portions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    seq_num INTEGER,
    amount REAL NOT NULL,
    measure_unit_id INTEGER,
    measure_unit_name VARCHAR(100),
    measure_unit_abbreviation VARCHAR(20),
    modifier VARCHAR(200),
    gram_weight REAL NOT NULL,
    data_points INTEGER,
    footnote VARCHAR(500),
    min_year_acquired INTEGER,
    FOREIGN KEY (food_id) REFERENCES foods (id) ON DELETE CASCADE
);

-- User collections for organizing foods
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(500),
    color VARCHAR(7) DEFAULT '#007aff',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for foods in collections
CREATE TABLE IF NOT EXISTS food_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    collection_id INTEGER NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods (id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections (id) ON DELETE CASCADE,
    UNIQUE (food_id, collection_id)
);

-- Search and usage history
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_query VARCHAR(200),
    food_id INTEGER,
    action VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (food_id) REFERENCES foods (id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_foods_fdc_id ON foods (fdc_id);
CREATE INDEX IF NOT EXISTS idx_foods_data_type ON foods (data_type);
CREATE INDEX IF NOT EXISTS idx_foods_saved_at ON foods (saved_at);
CREATE INDEX IF NOT EXISTS idx_food_nutrients_food_id ON food_nutrients (food_id);
CREATE INDEX IF NOT EXISTS idx_food_nutrients_nutrient_id ON food_nutrients (nutrient_id);
CREATE INDEX IF NOT EXISTS idx_food_portions_food_id ON food_portions (food_id);
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history (timestamp);
CREATE INDEX IF NOT EXISTS idx_search_history_action ON search_history (action);

-- Insert common nutrients for reference
INSERT OR IGNORE INTO nutrients (id, name, unit_name, nutrient_nbr, rank) VALUES
(1008, 'Energy', 'kcal', 208, 300),
(1003, 'Protein', 'g', 203, 600),
(1004, 'Total lipid (fat)', 'g', 204, 800),
(1005, 'Carbohydrate, by difference', 'g', 205, 1110),
(1079, 'Fiber, total dietary', 'g', 291, 1200),
(2000, 'Sugars, total including NLEA', 'g', 269, 1210),
(1093, 'Sodium, Na', 'mg', 307, 5800),
(1087, 'Calcium, Ca', 'mg', 301, 5300),
(1089, 'Iron, Fe', 'mg', 303, 5400),
(1106, 'Vitamin A, RAE', 'µg', 320, 7420),
(1162, 'Vitamin C, total ascorbic acid', 'mg', 401, 6300),
(1124, 'Zinc, Zn', 'mg', 309, 5500),
(1175, 'Vitamin B-6', 'mg', 415, 6700),
(1177, 'Folate, total', 'µg', 417, 6900),
(1178, 'Vitamin B-12', 'µg', 418, 6800),
(1092, 'Potassium, K', 'mg', 306, 5600),
(1090, 'Magnesium, Mg', 'mg', 304, 5500),
(1095, 'Phosphorus, P', 'mg', 305, 5700),
(1109, 'Vitamin E (alpha-tocopherol)', 'mg', 323, 7905),
(1185, 'Vitamin K (phylloquinone)', 'µg', 430, 8800);

-- Insert default collections
INSERT OR IGNORE INTO collections (name, description, color) VALUES
('Favorites', 'Your favorite foods for quick access', '#ff3b30'),
('Breakfast', 'Foods typically eaten for breakfast', '#ff9500'),
('Lunch', 'Foods typically eaten for lunch', '#ffcc00'),
('Dinner', 'Foods typically eaten for dinner', '#34c759'),
('Snacks', 'Snack foods and quick bites', '#007aff'),
('High Protein', 'Foods high in protein content', '#5856d6'),
('Low Sodium', 'Foods with low sodium content', '#af52de'),
('Recipes', 'Foods used in recipes and cooking', '#ff2d92');

-- Database info and statistics views
CREATE VIEW IF NOT EXISTS food_stats AS
SELECT 
    COUNT(*) as total_foods,
    COUNT(DISTINCT brand_owner) as unique_brands,
    COUNT(DISTINCT data_type) as data_types,
    AVG(CASE WHEN fn.nutrient_id = 1008 THEN fn.amount END) as avg_calories,
    MAX(saved_at) as last_saved
FROM foods f
LEFT JOIN food_nutrients fn ON f.id = fn.food_id;

CREATE VIEW IF NOT EXISTS nutrient_coverage AS
SELECT 
    n.name as nutrient_name,
    n.unit_name,
    COUNT(fn.food_id) as foods_with_nutrient,
    AVG(fn.amount) as avg_amount,
    MIN(fn.amount) as min_amount,
    MAX(fn.amount) as max_amount
FROM nutrients n
LEFT JOIN food_nutrients fn ON n.id = fn.nutrient_id
GROUP BY n.id, n.name, n.unit_name
ORDER BY foods_with_nutrient DESC;

-- Triggers for updating timestamps
CREATE TRIGGER IF NOT EXISTS update_foods_timestamp 
AFTER UPDATE ON foods
BEGIN
    UPDATE foods SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;