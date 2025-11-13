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

## Design Decisions

This system is designed to be **highly responsive and scalable**:

- **FastAPI**: Chosen for its async support, speed, and automatic API documentation via Swagger/Redoc.
- **PostgreSQL + Async SQLAlchemy**: Reliable relational database with non-blocking async operations.
- **Redis**: Used as a Celery broker.
- **Celery Async Tasks vs Cron Jobs**:

  - **Reason for Celery**: Cron jobs are time-based and poll the database at intervals, which can introduce delays and inefficiency. Celery allows **real-time background processing** immediately when a new order is created.
  - Async Celery tasks are event-driven, non-blocking, and scale better with multiple workers.

- **JWT Authentication**: Stateless and secure way to protect endpoints.
- **.env Configuration**: Centralized configuration makes switching environments simple.
- **Docker Compose**: Ensures consistent environment setup for PostgreSQL and Redis.
- **Manual `uv sync` Install**: Keeps dependency management under controlled virtual environment.
- **Postman Collection**: Provides ready-made tests for all endpoints.

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

> Installs FastAPI, Uvicorn, SQLAlchemy, Celery, Redis, Python-dotenv, Passlib, PyJWT, and other required packages.

---

## Docker Compose Setup

A `docker-compose.yml` is provided to spin up **PostgreSQL** and **Redis**:

```bash
docker-compose up -d
```

This starts:

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

Example usage in FastAPI endpoint:

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

> A `postman_collection.json` is provided. Import it into Postman to test all endpoints quickly.

---

## License

MIT License

---
