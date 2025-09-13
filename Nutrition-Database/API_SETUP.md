# API Key Setup Guide

## USDA FoodData Central API Key

The Nutrition Database component requires a USDA FoodData Central API key to function properly.

### Getting Your API Key

1. **Visit the USDA FoodData Central website:**
   - Go to https://fdc.nal.usda.gov/
   - Click on "API" in the top navigation

2. **Request an API Key:**
   - Click "Get API Key" or "Request API Key"
   - Fill out the simple registration form
   - You'll receive your API key immediately via email

3. **Configure Your API Key:**
   - Open the `.env` file in the Nutrition-Database folder
   - Replace `your_actual_usda_api_key_here` with your actual API key
   - Save the file

### Example .env Configuration

```bash
# .env - Add this to your .gitignore!
USDA_API_KEY=your_actual_api_key_from_usda_here
# EDAMAM_API_KEY=your_edamam_key_here
# SPOONACULAR_API_KEY=your_spoonacular_key_here  
# NUTRITIONIX_API_KEY=your_nutritionix_key_here
```

### Verification

After setting up your API key:

1. Restart the Nutrition Database service
2. Visit http://localhost:5000
3. You should see "🔑 API Key: Configured" in the header
4. Try performing a search to verify everything works

### Troubleshooting

**Common Issues:**

1. **"API key not configured" error:**
   - Check that your .env file is in the correct directory (Nutrition-Database/)
   - Ensure the API key doesn't have extra spaces or quotes
   - Verify the key isn't the placeholder text

2. **"Invalid API key" errors:**
   - Double-check your API key by copying it again from the USDA email
   - Make sure you're using the FoodData Central API key, not another USDA service

3. **Service still shows "Not Configured":**
   - Restart the Nutrition Database service after changing the .env file
   - Check the server logs for any error messages

### Security Notes

- Never commit your .env file to version control
- The .env file should already be in .gitignore
- Keep your API keys secure and don't share them publicly
- If you accidentally expose your key, request a new one from USDA