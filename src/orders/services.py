import logging
import uuid
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

    async def get_orders_for_user(self, user: User) -> list[Order]:
        """Fetch all orders for a specific user"""
        logger.debug(f"Fetching orders for user {user.email}")
        result = await self.session.execute(
            select(Order).where(Order.user_id == user.id)
        )
        orders = result.scalars().all()
        logger.info(f"Found {len(orders)} orders for user {user.email}")
        return orders
