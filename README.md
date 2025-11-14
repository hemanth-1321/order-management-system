
---
# Order Management System

A **FastAPI + PostgreSQL + Redis + Celery** asynchronous order processing system with JWT authentication, rate limiting, and status-based order filtering.
---

## Features

- FastAPI REST API for managing orders
- JWT authentication with access & refresh tokens
- Async database operations using SQLAlchemy + `asyncpg`
- Background order processing using Celery
- Redis as Celery broker
- Async-safe task handling
- **Rate limiting per endpoint**
- **Filter orders by status**

---

## Design Decisions

This system is designed to be **highly responsive and scalable**:

- **FastAPI**: Async support, speed, and automatic API documentation.

- **PostgreSQL + Async SQLAlchemy**: Reliable relational database with non-blocking operations.

- **Redis**: Celery broker for background tasks.

- **Celery Async Tasks vs Cron Jobs**:

  - Cron jobs poll the database periodically and can introduce delays.
  - Celery tasks are **event-driven**, real-time, non-blocking, and scale well with multiple workers.

- **JWT Authentication**: Stateless and secure.

- **Rate Limiting**: Prevents abuse per endpoint.

- **Status-based Filtering**: Query orders by `STATUS` (`PENDING`, `PROCESSING`, `COMPLETED`, `CANCELLED`).

- **Docker Compose**: Consistent setup for PostgreSQL and Redis.

- **Postman Collection**: Ready-made tests for all endpoints.

---

## Environment Variables

Create a `.env` file in the project root:

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


### 3. Install dependencies

```bash
uv sync
```

> Installs FastAPI, Uvicorn, SQLAlchemy, Celery, Redis, Python-dotenv, Passlib, PyJWT, and other required packages.

---

## Docker Compose Setup

Spin up PostgreSQL and Redis:

```bash
docker-compose up -d
```

---

### alembic 
```bash
alembic upgrade head
```

## Running the API

```bash
uvicorn src.main:app --reload
```

- API docs: `http://localhost:8000/docs`

---

## Celery Worker

```bash
celery -A src.celery_tasks worker --loglevel=info
```

- Use `-P solo` if async loop issues occur.
- Example in FastAPI endpoint:

```python
from src.celery_tasks import process_order
process_order.delay(order_id)
```

---

## Rate Limiting

Each endpoint has a per-minute limit:

| Endpoint              | Limit  |
| --------------------- | ------ |
| `/auth/register`      | 5/min  |
| `/auth/login`         | 5/min  |
| `/auth/refresh`       | 10/min |
| `/orders/create`      | 20/min |
| `/orders/my-orders`   | 30/min |
| `/orders/{id}/cancel` | 10/min |

---

## Background Processing

- Orders are processed asynchronously using **Celery**.
- Status flow: `PENDING → PROCESSING → COMPLETED`.
- Logs show all processed orders.

---

## Testing

- Use **Postman** or **HTTPie**.
- Postman collection provided (`postman_collection.json`) with all endpoints ready for testing.

---

## License

MIT License

---
