# E-commerce API (Fixed & Enhanced)

A professional-grade Django Rest Framework e-commerce API with modern features, security, and performance optimizations.

## ✨ Key Features
- **Consolidated Architecture**: Unified `views.py` and `urls.py` for a clean, maintainable codebase.
- **Stock Management**: Atomic transactions for order creation with automatic stock deduction and restoration upon cancellation.
- **Security**: Environment variable support via `python-decouple`. Sensitive keys are no longer hardcoded.
- **Performance**:
  - Redis Caching for Product List and Details.
  - Efficient Signals that clear specific cache keys instead of rebuilding global ones.
  - Pagination enabled by default.
- **Payments**: Integrated Stripe Payment Intent creation and confirmation logic.
- **Business Logic**: Complete flow for Cart, Wishlist, Coupons, and Order processing.

## 🚀 Setup & Installation

1. **Environment Variables**:
   Create a `.env` file in the root directory (based on `.env.example`).
   ```env
   SECRET_KEY=...
   DEBUG=False
   DB_NAME=...
   REDIS_URL=redis://localhost:6379/0
   STRIPE_SECRET_KEY=...
   ```

2. **Database**:
   ```bash
   python manage.py migrate
   ```

3. **Run Server**:
   ```bash
   python manage.py runserver
   ```

## 📚 API Documentation
- **Swagger UI**: `/api/docs/`
- **Redoc**: `/api/redoc/`

## 🛠️ Main Endpoints
- `POST /api/auth/register/` - User Registration
- `POST /api/auth/login/` - JWT Login
- `GET /api/products/` - Product Listing (with search/filter/sort)
- `POST /api/cart/add/` - Add items to cart
- `POST /api/orders/create/` - Create order from cart (Atomic)
- `POST /api/orders/<id>/checkout/` - Initiate Stripe Payment
- `POST /api/orders/<id>/cancel/` - Cancel order and restore stock

## 🛡️ Security Fixes Applied
- Removed hardcoded Stripe/Django keys.
- Used `permissions.IsAuthenticatedOrReadOnly` by default.
- Fixed `ProductManager` which was hiding valid products.
- Added `transaction.atomic` to sensitive checkout flows.
