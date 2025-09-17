# Heart Portal - Heart Failure Nutrition Management Platform

A comprehensive web-based platform designed to help individuals with heart failure manage their nutrition through USDA food data integration, personal food tracking, and educational resources.

## 🌟 Features

### Multi-Component Architecture
- **Landing Portal**: Central navigation hub with information about heart failure nutrition
- **Nutrition Database**: USDA Food Data Central API interface for comprehensive food data
- **Food Base**: Personal food storage and management system
- **Blog Manager**: Heart health educational content and resources

### Key Capabilities
- 🔍 Advanced food search using USDA Food Data Central API
- 📊 Detailed nutritional information with heart-healthy focus
- 💾 Personal food database for tracking favorites
- 📝 Educational blog content about heart failure nutrition
- 📱 Responsive design for mobile and desktop
- 🔒 SSL-secured production deployment

## 🚀 Live Demo

Visit the live application at: **https://heartfailureportal.com**

- Main Portal: https://heartfailureportal.com
- Nutrition Database: https://heartfailureportal.com/nutrition-database/
- Food Base: https://heartfailureportal.com/food-base/
- Blog Manager: https://heartfailureportal.com/blog-manager/

## 🏗️ Architecture

### Application Components
| Component | Port | Description |
|-----------|------|-------------|
| **Main App** | 3000 | Landing page and navigation hub |
| **Nutrition Database** | 5000 | USDA API interface |
| **Food Base** | 5001 | Personal food storage |
| **Blog Manager** | 5002 | Heart health blog system |

### Technology Stack
- **Backend**: Python Flask applications
- **Frontend**: HTML5, CSS3, JavaScript (responsive design)
- **Database**: SQLite for local storage
- **API Integration**: USDA Food Data Central API
- **Web Server**: Nginx reverse proxy
- **SSL**: Let's Encrypt certificates
- **Deployment**: Ubuntu 20.04 with systemd services

## 🛠️ Local Development

### Prerequisites
- Python 3.8+
- Flask
- Git
- USDA API Key (free from https://fdc.nal.usda.gov/api-guide.html)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Heart-Portal-Main.git
   cd Heart-Portal-Main
   ```

2. **Set up environment variables**
   Create `.env` files in each component directory with your USDA API key:
   ```bash
   USDA_API_KEY=your_api_key_here
   ```

3. **Install dependencies and run applications**
   ```bash
   # Main App (Port 3000)
   cd main-app
   python3 main_app.py

   # Nutrition Database (Port 5000)
   cd ../Nutrition-Database
   python3 app.py

   # Food Base (Port 5001)
   cd ../Food-Base
   python3 app.py

   # Blog Manager (Port 5002)
   cd ../Blog-Manager
   python3 app.py
   ```

4. **Access the application**
   - Main Portal: http://localhost:3000
   - Nutrition Database: http://localhost:5000
   - Food Base: http://localhost:5001
   - Blog Manager: http://localhost:5002

### Development Scripts
```bash
./scripts/dev-check.sh        # Verify local development environment
./scripts/deploy.sh           # Deploy to production server
./scripts/monitor-services.sh # Check production service health
./scripts/rollback.sh         # Rollback production deployment
```

## 🏥 Heart Failure Nutrition Focus

This platform is specifically designed for individuals managing heart failure, with features that emphasize:

- **Sodium Monitoring**: Detailed sodium content tracking for heart-healthy diets
- **Nutritional Education**: Evidence-based information about heart failure nutrition
- **Portion Control**: Tools for managing appropriate serving sizes
- **Meal Planning**: Resources for planning heart-healthy meals
- **API Integration**: Real-time access to comprehensive USDA nutritional data

## 📱 Responsive Design

The platform features a fully responsive design that works seamlessly across:
- Desktop computers
- Tablets
- Mobile phones
- Various screen sizes and orientations

## 🔒 Security Features

- SSL/TLS encryption for all communications
- Environment-specific configurations
- Secure API key management
- Input validation and sanitization
- Production-grade deployment practices

## 🚀 Production Deployment

The application is deployed on a secure Ubuntu server with:
- Nginx reverse proxy configuration
- Let's Encrypt SSL certificates
- Systemd service management
- Automated deployment pipeline
- Health monitoring and logging

### Server Architecture
- **Domain**: heartfailureportal.com
- **SSL**: Let's Encrypt with auto-renewal
- **Services**: 4 Flask applications managed by systemd
- **Monitoring**: Automated health checks and service monitoring

## 📊 API Integration

### USDA Food Data Central API
The platform integrates with the USDA's comprehensive food database, providing:
- Detailed nutritional information for thousands of foods
- Multiple food data types (Foundation Foods, Survey Foods, etc.)
- Real-time API access to the latest food data
- Advanced search capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support or questions about heart failure nutrition, please consult with your healthcare provider. This platform is designed to supplement, not replace, professional medical advice.

## 🔧 Development Status

- ✅ Multi-component Flask architecture
- ✅ USDA API integration
- ✅ Responsive web design
- ✅ SSL/HTTPS deployment
- ✅ Production server deployment
- ✅ Health monitoring system
- ✅ Database management tools

## 📞 Contact

For technical questions or contributions, please open an issue on GitHub.

---

**Disclaimer**: This platform is for educational and informational purposes. Always consult with healthcare professionals for medical advice regarding heart failure management.