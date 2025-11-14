import asyncio
import logging
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.database.models import Order, STATUS
from src.config.settings import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
app = Celery("tasks")
app.conf.broker_url = Config.REDIS_URL
app.conf.result_backend = Config.REDIS_URL
app.conf.broker_connection_retry_on_startup = True

def get_task_session_maker():
    engine = create_async_engine(
        url=Config.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def process_order_async(order_id: str):
    session_maker = get_task_session_maker()
    async with session_maker() as session:
        order = await session.get(Order, order_id)
        if not order:
            logger.warning(f"[Order {order_id}] not found")
            return f"[Order {order_id}] not found"

        stages = [
            (STATUS.PROCESSING, "Processing order"),
            (STATUS.COMPLETED, "Finalizing order")
        ]

        for status, stage_name in stages:
            order.status = status
            await session.commit()
            logger.info(f"[Order {order_id}] Status updated to {status.value} - {stage_name}")
            await asyncio.sleep(2)  # simulate work

        logger.info(f"[Order {order_id}] Processing complete!")
        return f"Order {order_id} processed successfully"

# Celery task wrapper (sync)
@app.task(bind=True)
def process_order(self, order_id: str):
    logger.info(f"[Task] process_order started for Order ID: {order_id}")
    return asyncio.run(process_order_async(order_id))
