import logging
import uuid
from typing import Optional
from fastapi import HTTPException
from datetime import datetime, timezone
from sqlalchemy.future import select
from src.database.models import Order, STATUS, User
from src.database.db import SessionDep
logger = logging.getLogger(__name__)

class OrderService:
    """Service class for order operations with logging"""

    def __init__(self, session:SessionDep ):
        self.session = session

    async def create_order(self, user: User, product_name: str, amount: float) -> Order:
        """Create a new order with status PENDING"""
        logger.debug(f"Creating order for user {user.email} | product: {product_name} | amount: {amount}")

        new_order = Order(
            id=str(uuid.uuid4()),
            user_id=user.id,
            product_name=product_name,
            amount=amount,
            status=STATUS.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        self.session.add(new_order)
        await self.session.commit()
        await self.session.refresh(new_order)

        logger.info(f"Order created: {new_order.id} for user {user.email}")
        return new_order

    async def get_orders_for_user(self, user: User, status: Optional[STATUS] = None) -> list[Order]:
        """Fetch all orders for a specific user (optionally filtered by status)"""
        logger.debug(f"Fetching orders for user {user.email} with status filter: {status}")

        query = select(Order).where(Order.user_id == user.id)
        if status:
            query = query.where(Order.status == status)

        result = await self.session.execute(query)
        orders = result.scalars().all()

        logger.info(f"Found {len(orders)} orders for user {user.email} (status={status})")
        return orders


    async def cancel_order(self, order_id: str, user: User) -> Order:
        """Cancel an order if it is pending"""
        logger.debug(f"User {user.email} requested to cancel order {order_id}")

        result = await self.session.execute(
            select(Order).where(Order.id == order_id, Order.user_id == user.id)
        )
        order = result.scalar_one_or_none()

        if not order:
            logger.warning(f"Order {order_id} not found for user {user.email}")
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != STATUS.PENDING:
            logger.warning(f"Order {order_id} cannot be cancelled (status: {order.status})")
            raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")

        order.status = STATUS.CANCELLED
        await self.session.commit()
        await self.session.refresh(order)

        logger.info(f"Order {order_id} cancelled by user {user.email}")
        return order