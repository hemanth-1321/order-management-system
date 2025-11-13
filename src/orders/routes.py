from fastapi import APIRouter, Depends, status,Request,Query
from src.celery_tasks import process_order
from src.auth.dependencies import get_current_user
from src.database.db import SessionDep

from src.orders.services import OrderService
from src.orders.schema import OrderCreate, OrderRead
from src.database.models import User,STATUS
from src.config.ratelimiting import limiter
order_router = APIRouter()

@order_router.post("/create", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_order(
    session: SessionDep,
    order_data: OrderCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    service = OrderService(session)
    order = await service.create_order(
        user=current_user,
        product_name=order_data.product_name,
        amount=order_data.amount
    )

    process_order.delay(str(order.id)) 

    return order

@order_router.get("/my-orders", response_model=list[OrderRead])
@limiter.limit("30/minute")
async def my_orders(
    session: SessionDep,
    request: Request,
    current_user: User = Depends(get_current_user),
    status: STATUS | None = Query(None, description="Optional order status filter (e.g. PENDING, CANCELLED, COMPLETED)"),
):
    service = OrderService(session)
    orders = await service.get_orders_for_user(current_user, status)
    return orders

@order_router.patch("/{order_id}/cancel", response_model=OrderRead)
@limiter.limit("10/minute")
async def cancel_order(
    order_id: str,
    session: SessionDep,
     request: Request,
    current_user: User = Depends(get_current_user),
):
    service = OrderService(session)
    return await service.cancel_order(order_id, current_user)