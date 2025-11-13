from celery import Celery
import asyncio
import logging

from src.database.db import async_session_maker
from src.database.models import Order, STATUS
from src.config.logger import configure_logging

app = Celery("tasks")
app.config_from_object("src.config.settings")

# Logging
configure_logging("INFO")
logger = logging.getLogger(__name__)

@app.task
def process_order(order_id: str):
    """
    Celery task to process an order asynchronously.
    Wrap async code in asyncio.run() since Celery cannot handle async directly.
    """
    async def _process():
        async with async_session_maker() as session:
            order = await session.get(Order, order_id)
            if not order:
                logger.warning(f"[Order {order_id}] Order not found!")
                return

            stages = [
                (STATUS.PROCESSING, "Processing order"),
                (STATUS.COMPLETED, "Finalizing order")
            ]

            for status, stage_name in stages:
                order.status = status
                await session.commit()
                logger.info(f"[Order {order_id}] Status updated to {status.value} - {stage_name}")
                await asyncio.sleep(2)

            logger.info(f"[Order {order_id}] Processing complete!")

    asyncio.run(_process())
