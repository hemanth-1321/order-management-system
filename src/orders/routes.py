from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.celery_tasks import process_order
from src.auth.dependencies import get_current_user
from src.database.db import SessionDep
from src.orders.services import OrderService
from src.orders.schema import OrderCreate, OrderRead
from src.database.models import User

order_router = APIRouter()

@order_router.post("/create", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    session:SessionDep,

    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
):
    service = OrderService(session)
    order = await service.create_order(
        user=current_user,
        product_name=order_data.product_name,
        amount=order_data.amount
    )
    process_order.delay(order.id)

    return order

@order_router.get("/my-orders", response_model=list[OrderRead])
async def my_orders(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
):
    service = OrderService(session)
    orders = await service.get_orders_for_user(current_user)
    return orders
