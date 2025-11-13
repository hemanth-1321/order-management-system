Got it! Here’s a polished version of your README with:

- **Initial manual pip install using `uv sync`** included in the setup.
- **Postman collection note** included for testing.

---

# Order Management System

A FastAPI + PostgreSQL + Redis + Celery-based asynchronous order processing system.

---

## Features

- FastAPI REST API for managing orders
- JWT authentication
- Async database operations using SQLAlchemy + `asyncpg`
- Background order processing using Celery
- Redis as Celery broker
- Async-safe task handling

---

## Environment Variables

Create a `.env` file in the project root with the following:

```env
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/orders
REDIS_URL=redis://localhost:6379/0
```

---

## Setup Instructions

### 1. Clone the repository

```bash
https://github.com/hemanth-1321/order-management-system
cd order-management-system
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies manually

```bash
uv sync
```

> This will install all required packages like FastAPI, Uvicorn, SQLAlchemy, Celery, Redis, Python-dotenv, Passlib, and PyJWT.

---

## Docker Compose Setup

We provide a `docker-compose.yml` that spins up **PostgreSQL** and **Redis**:

```bash
docker-compose up -d
```

This will start:

- PostgreSQL database
- Redis server for Celery

No manual Docker commands needed.

---

## Running the API

In one terminal:

```bash
uvicorn src.main:app --reload
```

- API docs: `http://localhost:8000/docs`

---

## Celery Worker

In a separate terminal:

```bash
celery -A src.celery_tasks worker --loglevel=info
```

> Use `-P solo` if you encounter async loop issues.

Your FastAPI endpoints can enqueue tasks like this:

```python
from src.celery_tasks import process_order

process_order.delay(order_id)
```

---

## Testing

You can use **Postman** or **HTTPie**.

### Example: Create Order

```http
POST /orders/create
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

{
    "product_name": "Book",
    "amount": 99.0
}
```

> For testing, a `postman_collection.json` is provided. Import it into Postman to test all endpoints quickly.

---
