# Al Barakah Mart - Django E-commerce Platform

A modern, feature-rich e-commerce platform built with Django for selling organic groceries and daily essentials in Dhaka, Bangladesh.

## Features

### Customer Features
- 🛒 Shopping cart with AJAX operations
- ❤️ Wishlist functionality
- 🔍 Advanced product search and filtering
- 👁️ Quick View modal for instant product previews
- 📱 Fully responsive design
- 💳 Multiple payment gateway support
- 📦 Order tracking and history
- ⭐ Product reviews and ratings
- 🎯 Smart product recommendations (bought-together algorithm)

### Admin Features
- 📊 Advanced analytics dashboard
- 📈 Real-time visitor tracking
- 💰 Revenue and sales reports
- 📦 Inventory management with low stock alerts
- 🎫 Support ticket system
- 🏷️ Coupon and discount management
- 📧 Email notifications
- 🔐 Secure admin panel with rate limiting

### Technical Highlights
- ⚡ Optimized database queries with caching
- 🔒 Security hardening (CSRF, HSTS, rate limiting)
- 🎨 Modern UI with Tailwind CSS
- 📱 Mobile-first responsive design
- 🚀 SEO optimized with dynamic meta tags
- 🔄 AJAX-powered interactions
- 💾 Atomic transactions for data integrity
- 📊 Comprehensive analytics tracking

## Tech Stack

- **Backend**: Django (Optimized for 5.1+)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Icons**: Lucide Icons
- **Payment**: SSLCommerz integration
- **Analytics**: Custom analytics engine

## Installation

### Prerequisites
- Python 3.10+
- pip
- virtualenv (recommended)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jahidulislamseo/shop.git
cd shop
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run development server:
```bash
python manage.py runserver
```

7. Access the application:
- Frontend: http://localhost:8000
- Admin: http://localhost:8000/manager-portal-631/

## Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SSLCommerz
SSLCOMMERZ_STORE_ID=your-store-id
SSLCOMMERZ_STORE_PASSWORD=your-store-password
SSLCOMMERZ_IS_SANDBOX=True
```

## Project Structure

```
al-barakah-mart-django/
├── config/              # Project settings
├── core/                # Core app (site settings, analytics)
├── products/            # Product catalog
├── orders/              # Shopping cart & orders
├── users/               # User authentication & profiles
├── marketing/           # Coupons & promotions
├── analytics/           # Analytics engine
├── templates/           # Global templates
├── static/              # Static files
└── media/               # User uploads
```

## Key Features Implementation

### Cart Persistence
Guest carts automatically merge when users log in or register.

### AJAX Cart
Add to cart without page reload with instant toast notifications.

### Smart Related Products
Analyzes order history to show "bought together" products with intelligent fallbacks.

### Quick View Modal
Instant product preview without leaving the shop page.

### Stock Validation
Atomic transactions prevent overselling with race condition handling using F() expressions.

## Security Features

- Rate limiting on authentication endpoints
- Secure headers (HSTS, X-Frame-Options, CSP)
- CSRF protection
- Obfuscated admin URL
- SQL injection prevention
- XSS protection

## Performance Optimizations

- Database query optimization with select_related/prefetch_related
- Strategic database indexing
- Page caching for static content
- Lazy loading for images
- Minified CSS/JS (production)

## Contributing

This is a private project. For any issues or suggestions, please contact the repository owner.

## License

Proprietary - All rights reserved

## Contact

For inquiries: jahidulislamseo@gmail.com

---

**Version**: 1.0.1  
**Last Updated**: February 2026
