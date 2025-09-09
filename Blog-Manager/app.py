"""
Blog Manager Flask Application for Heart Failure Portal
Serves blog posts and handles blog-related functionality
"""

from flask import Flask, render_template, request, jsonify, redirect
from datetime import datetime
import os

app = Flask(__name__)

def get_main_app_url():
    """Get the main app URL based on environment"""
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return 'https://heartfailureportal.com'
    return 'http://localhost:3000'

# Make the function available in templates
@app.context_processor
def utility_processor():
    return dict(get_main_app_url=get_main_app_url)

# Sample blog posts data (you'll want to use a database later)
BLOG_POSTS = [
    {
        'id': 1,
        'title': 'Understanding Heart Failure and Nutrition: Your Complete Guide',
        'content': '''
            <h2>What is Heart Failure?</h2>
            <p>Heart failure affects over 6 million Americans and occurs when your heart muscle doesn't pump blood as well as it should. This doesn't mean your heart has stopped working, but rather that it's working less efficiently than normal.</p>
            
            <h2>The Critical Role of Nutrition</h2>
            <p>Proper nutrition plays a crucial role in managing heart failure symptoms and improving your quality of life. The foods you eat directly impact:</p>
            <ul>
                <li><strong>Fluid retention:</strong> High sodium foods can cause your body to retain water, making your heart work harder</li>
                <li><strong>Energy levels:</strong> Balanced nutrition helps maintain steady energy throughout the day</li>
                <li><strong>Weight management:</strong> Maintaining a healthy weight reduces strain on your heart</li>
                <li><strong>Overall cardiovascular health:</strong> Heart-healthy foods support better circulation and heart function</li>
            </ul>
            
            <h2>Key Dietary Guidelines for Heart Failure</h2>
            <h3>1. Sodium Restriction</h3>
            <p>Most cardiologists recommend limiting sodium to 2,000-3,000mg per day. This helps prevent fluid buildup and reduces the workload on your heart.</p>
            
            <h3>2. Fluid Management</h3>
            <p>Your healthcare provider may recommend limiting fluids to 1.5-2 liters per day, depending on your condition severity.</p>
            
            <h3>3. Heart-Healthy Foods</h3>
            <p>Focus on foods rich in:</p>
            <ul>
                <li>Potassium (bananas, oranges, spinach)</li>
                <li>Magnesium (nuts, seeds, whole grains)</li>
                <li>Omega-3 fatty acids (fish, flaxseeds)</li>
                <li>Fiber (vegetables, fruits, beans)</li>
            </ul>
            
            <blockquote>Remember: Always consult with your healthcare provider before making significant dietary changes. Every person's heart failure journey is unique.</blockquote>
            
            <h2>Using Technology to Support Your Journey</h2>
            <p>Our Heart Portal tools can help you track nutrition and make informed food choices. The USDA Nutrition Database provides detailed nutritional information, while the Food Storage feature helps you organize heart-healthy meal planning.</p>
        ''',
        'date': datetime(2025, 1, 15),
        'author': 'Heart Portal Team',
        'excerpt': 'Learn how nutrition impacts heart failure management and discover practical strategies for heart-healthy eating.'
    },
    {
        'id': 2,
        'title': 'The USDA Database: A Powerful Tool for Heart-Healthy Living',
        'content': '''
            <h2>Introduction to USDA Food Data Central</h2>
            <p>The USDA Food Data Central is a comprehensive database containing nutritional information for thousands of foods. For heart failure patients, this resource is invaluable for making informed dietary choices.</p>
            
            <h2>Why Nutritional Data Matters</h2>
            <p>When managing heart failure, every milligram of sodium counts. The USDA database provides precise nutritional information that helps you:</p>
            <ul>
                <li>Track daily sodium intake accurately</li>
                <li>Compare similar foods to make better choices</li>
                <li>Plan balanced meals that support heart health</li>
                <li>Understand portion sizes and their nutritional impact</li>
            </ul>
            
            <h2>How to Use Our Nutrition Database Tool</h2>
            <h3>Step 1: Search for Foods</h3>
            <p>Use our search feature to find specific foods or browse categories. The database includes everything from fresh produce to packaged foods.</p>
            
            <h3>Step 2: Analyze Nutritional Content</h3>
            <p>Pay special attention to:</p>
            <ul>
                <li><strong>Sodium content:</strong> Keep daily intake under your recommended limit</li>
                <li><strong>Potassium levels:</strong> Important for heart rhythm and muscle function</li>
                <li><strong>Saturated fat:</strong> Limit to support overall cardiovascular health</li>
                <li><strong>Fiber content:</strong> Helps with cholesterol management</li>
            </ul>
            
            <h3>Step 3: Save Your Favorites</h3>
            <p>Use our Food Storage feature to save heart-healthy foods you discover. This makes meal planning easier and helps you stick to your nutritional goals.</p>
            
            <h2>Real-World Application</h2>
            <p>For example, when comparing bread options:</p>
            <ul>
                <li>Regular white bread: ~230mg sodium per slice</li>
                <li>Low-sodium whole grain: ~80mg sodium per slice</li>
                <li>Homemade bread (no salt): ~5mg sodium per slice</li>
            </ul>
            <p>This data helps you make choices that support your heart health goals while still enjoying the foods you love.</p>
            
            <blockquote>Pro tip: Look for the "per 100g" nutritional data to easily compare different foods on an equal basis.</blockquote>
            
            <h2>Getting Started</h2>
            <p>Ready to explore? Access our Nutrition Database through the Tools menu above. Start by searching for foods you commonly eat, and discover healthier alternatives that fit your dietary needs.</p>
        ''',
        'date': datetime(2025, 1, 10),
        'author': 'Heart Portal Team',
        'excerpt': 'Discover how to use nutritional data to support heart-healthy eating and make informed food choices.'
    },
    {
        'id': 3,
        'title': 'Low-Sodium Cooking: Flavor Without the Salt',
        'content': '''
            <h2>The Challenge of Low-Sodium Cooking</h2>
            <p>One of the biggest concerns heart failure patients have about dietary changes is losing flavor in their meals. The good news? You can create delicious, satisfying meals without relying on salt.</p>
            
            <h2>Natural Flavor Enhancers</h2>
            <h3>Herbs and Spices</h3>
            <p>Fresh and dried herbs add incredible flavor without sodium:</p>
            <ul>
                <li><strong>Garlic and onion:</strong> Fundamental flavor builders</li>
                <li><strong>Fresh herbs:</strong> Basil, cilantro, parsley, thyme</li>
                <li><strong>Warm spices:</strong> Cumin, paprika, turmeric, cinnamon</li>
                <li><strong>Heat:</strong> Black pepper, cayenne, chili powder</li>
            </ul>
            
            <h3>Acid and Citrus</h3>
            <p>Acidic ingredients brighten flavors and make food more satisfying:</p>
            <ul>
                <li>Lemon and lime juice</li>
                <li>Vinegars (balsamic, apple cider, white wine)</li>
                <li>Tomatoes (fresh, canned no-salt-added)</li>
            </ul>
            
            <h2>Heart-Healthy Cooking Techniques</h2>
            <h3>Building Flavor Layers</h3>
            <p>Professional chefs build flavor in layers. Here's how:</p>
            <ol>
                <li><strong>Start with aromatics:</strong> Sauté garlic, onions, or ginger</li>
                <li><strong>Add spices early:</strong> Toast spices to release their oils</li>
                <li><strong>Use cooking methods that concentrate flavor:</strong> Roasting, grilling, braising</li>
                <li><strong>Finish with fresh elements:</strong> Herbs, citrus, or a splash of vinegar</li>
            </ol>
            
            <h2>Sample Low-Sodium Recipes</h2>
            <h3>Mediterranean Herb Chicken</h3>
            <p><strong>Ingredients:</strong> Chicken breast, olive oil, lemon juice, garlic, oregano, thyme, black pepper</p>
            <p><strong>Sodium:</strong> Under 100mg per serving</p>
            
            <h3>Vegetable-Packed Pasta</h3>
            <p><strong>Ingredients:</strong> Whole grain pasta, zucchini, bell peppers, tomatoes, basil, garlic, olive oil</p>
            <p><strong>Sodium:</strong> Under 150mg per serving</p>
            
            <h2>Reading Labels Wisely</h2>
            <p>When shopping for ingredients:</p>
            <ul>
                <li>Choose "no salt added" canned goods</li>
                <li>Look for products with less than 140mg sodium per serving</li>
                <li>Rinse canned beans and vegetables to remove excess sodium</li>
                <li>Make your own seasoning blends without salt</li>
            </ul>
            
            <blockquote>Remember: Your taste buds will adapt! After 2-3 weeks of eating less sodium, you'll start to appreciate the natural flavors of foods more.</blockquote>
            
            <h2>Meal Planning for Success</h2>
            <p>Use our Food Storage tool to save your favorite low-sodium ingredients and recipes. This makes weekly meal planning easier and helps ensure you always have heart-healthy options available.</p>
        ''',
        'date': datetime(2025, 1, 5),
        'author': 'Heart Portal Team',
        'excerpt': 'Master the art of creating flavorful, satisfying meals without excess sodium using herbs, spices, and smart cooking techniques.'
    },
    {
        'id': 4,
        'title': 'Reading Food Labels: A Heart Patient\'s Essential Skill',
        'content': '''
            <h2>Why Food Labels Matter</h2>
            <p>For heart failure patients, reading food labels isn't just helpful—it's essential for managing your condition. The Nutrition Facts panel provides crucial information that helps you make heart-healthy choices.</p>
            
            <h2>The Nutrition Facts Panel: Key Areas to Focus On</h2>
            <h3>1. Serving Size</h3>
            <p>Always check the serving size first. All nutritional information is based on this amount. If you eat double the serving size, you'll get double the sodium, calories, and other nutrients.</p>
            
            <h3>2. Sodium Content</h3>
            <p>This is your most important number as a heart failure patient:</p>
            <ul>
                <li><strong>Low sodium:</strong> 140mg or less per serving</li>
                <li><strong>Moderate sodium:</strong> 140-400mg per serving</li>
                <li><strong>High sodium:</strong> 400mg or more per serving</li>
            </ul>
            <p>Aim for foods with less than 140mg sodium per serving when possible.</p>
            
            <h3>3. Saturated and Trans Fats</h3>
            <p>These fats can worsen heart health:</p>
            <ul>
                <li>Keep saturated fat under 7% of daily calories</li>
                <li>Avoid trans fats completely (look for "0g trans fat")</li>
            </ul>
            
            <h2>Hidden Sodium Sources</h2>
            <p>Sodium hides in unexpected places:</p>
            <ul>
                <li><strong>Bread and baked goods:</strong> Often 200-300mg per slice</li>
                <li><strong>Condiments:</strong> Ketchup, mustard, soy sauce</li>
                <li><strong>Processed meats:</strong> Deli meat, bacon, sausage</li>
                <li><strong>Canned soups:</strong> Can contain 800-1200mg per serving</li>
                <li><strong>Cheese:</strong> Especially processed varieties</li>
            </ul>
            
            <h2>Ingredient Lists: What to Look For</h2>
            <p>Ingredients are listed in order by weight. Avoid products where these appear early in the list:</p>
            <ul>
                <li>Salt, sodium chloride</li>
                <li>Monosodium glutamate (MSG)</li>
                <li>Sodium bicarbonate (baking soda)</li>
                <li>Sodium citrate</li>
                <li>Sodium phosphate</li>
            </ul>
            
            <h2>Heart-Healthy Label Claims</h2>
            <p>Understanding common claims:</p>
            <ul>
                <li><strong>"Heart healthy":</strong> Must meet specific criteria for saturated fat, cholesterol, and sodium</li>
                <li><strong>"Reduced sodium":</strong> 25% less sodium than the original product</li>
                <li><strong>"Low sodium":</strong> 140mg or less per serving</li>
                <li><strong>"No salt added":</strong> No salt was added during processing, but the food may naturally contain sodium</li>
            </ul>
            
            <h2>Practical Shopping Tips</h2>
            <h3>Compare Similar Products</h3>
            <p>Use our Nutrition Database tool to compare similar products before shopping. This helps you identify the best options for your heart health.</p>
            
            <h3>Focus on Fresh Foods</h3>
            <p>The perimeter of the grocery store (fresh produce, meat, dairy) typically contains foods with fewer additives and less sodium.</p>
            
            <h3>Plan Ahead</h3>
            <p>Use our Food Storage feature to save heart-healthy products you've researched. This makes future shopping trips faster and more focused.</p>
            
            <blockquote>Pro tip: Take a photo of nutrition labels for products you're considering. You can compare them at home using our tools to make the best choice for your health.</blockquote>
            
            <h2>Making It Easier</h2>
            <p>Label reading gets easier with practice. Start by checking just sodium content, then gradually look at other nutrients as you become more comfortable with the process.</p>
        ''',
        'date': datetime(2024, 12, 28),
        'author': 'Heart Portal Team',
        'excerpt': 'Learn to decode food labels like a pro and make informed choices that support your heart health goals.'
    }
]

@app.route('/')
def blog_list():
    """Blog post listing page"""
    return render_template('blog.html', posts=BLOG_POSTS)

@app.route('/post/<int:post_id>')
def blog_post(post_id):
    """Individual blog post page"""
    post = next((p for p in BLOG_POSTS if p['id'] == post_id), None)
    if not post:
        return render_template('404.html'), 404
    return render_template('blog_post.html', post=post)

# Environment-aware redirect functions for Tools menu
@app.route('/redirect/nutrition')
def redirect_to_nutrition():
    """Redirect to Nutrition Database - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/nutrition-database/')
    
    # Local development
    return redirect('http://localhost:5000')

@app.route('/redirect/foodbase')
def redirect_to_foodbase():
    """Redirect to Food-Base - environment-aware"""
    # Check if we're running in production (server has heartfailureportal.com in hostname)
    if os.path.exists('/etc/hostname'):
        with open('/etc/hostname', 'r') as f:
            hostname = f.read().strip()
        if 'ubuntu' in hostname or 'heartfailure' in hostname:
            return redirect('http://heartfailureportal.com/food-base/')
    
    # Local development
    return redirect('http://localhost:5001')

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002, host='0.0.0.0')