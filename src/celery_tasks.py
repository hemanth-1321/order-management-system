import asyncio
import logging
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.database.models import Order, STATUS
from src.config.settings import Config
app = Celery("tasks")
app.config_from_object("src.config.settings")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_task_session_maker():
    """
    Create a new AsyncEngine + sessionmaker inside the task
    (safe for prefork Celery workers)
    """
    engine = create_async_engine(
        url=Config.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

@app.task(bind=True)
def process_order(self, order_id: str):
    logger.info(f"[Task] process_order started for Order ID: {order_id}")

    async def _process():
        # Create session maker after fork
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
                await asyncio.sleep(2)

            logger.info(f"[Order {order_id}] Processing complete!")
            return f"Order {order_id} processed successfully"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_process())
    loop.close()
    return result
