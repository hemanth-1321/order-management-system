# src/database/db.py
from typing import Annotated, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncAttrs,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from fastapi import Depends
from src.config.settings import Config

class Base(AsyncAttrs, DeclarativeBase):
    pass

# For FastAPI - created once at startup
engine = create_async_engine(url=Config.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator to provide a DB session.
    Usage: `db: AsyncSession = Depends(get_db)` in FastAPI.
    """
    async with async_session_maker() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_db)]
