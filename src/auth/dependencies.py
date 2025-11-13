import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.services import UserService
from src.database.models import User
from src.database.db import get_db

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and return the authenticated User.
    Raises HTTPException if token is invalid or user does not exist.
    """
    logger.debug("Authenticating user via JWT token")
    user_service = UserService(session)
    payload = user_service.decode_token(token)

    if not payload:
        logger.warning("Invalid JWT token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("JWT token missing 'sub' field")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Fetch the user from DB
    user = await session.get(User, user_id)
    if not user:
        logger.warning(f"User not found in DB for id: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    logger.info(f"User {user.email} authenticated successfully via token")
    return user
