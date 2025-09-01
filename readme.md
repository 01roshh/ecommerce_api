# 🛒 E-commerce API

A RESTful E-commerce API built with **FastAPI**, **SQLAlchemy**, and **JWT authentication**.  
This project provides product management, user authentication, order processing, and optional payment integration.

---

## 🚀 Features
- User authentication (JWT-based)
- Product CRUD (Create, Read, Update, Delete)
- Cart & Order management
- Secure password hashing
- Database integration (PostgreSQL/MySQL)
- Optional: Payment integration (Stripe)
- Environment-based configuration

---

## 📂 Project Structure
ecommerce_api/
│── app/
│ ├── main.py # Entry point
│ ├── models/ # SQLAlchemy models
│ ├── schemas/ # Pydantic schemas
│ ├── routes/ # API routes (products, users, orders)
│ ├── services/ # Business logic
│ ├── core/ # Config, security, JWT utils
│ └── db.py # Database connection
│
│── tests/ # Pytest test cases
│── requirements.txt # Dependencies
│── .env # Environment variables
│── README.md # Documentation


---

## 🛠️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/ecommerce_api.git
cd ecommerce_api


python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt

DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce_db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
STRIPE_SECRET_KEY=your_stripe_key   # optional

uvicorn app.main:app --reload
