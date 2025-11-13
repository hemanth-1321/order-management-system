import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from src.config.ratelimiting import limiter 

from src.auth.schema import UserCreate, LoginRequest, RefreshRequest
from src.auth.services import UserService
from src.database.db import SessionDep

logger = logging.getLogger(__name__)
auth_router = APIRouter()


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute") 
async def signup(user_data: UserCreate, session: SessionDep, request: Request):
    logger.debug(f"Received signup request for {user_data.email}")
    service = UserService(session)
    try:
        user = await service.create_user(user_data)
        logger.info(f"User {user.email} registered successfully")
        return {"id": user.id, "name": user.name, "email": user.email}
    except ValueError as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/login")
@limiter.limit("5/minute") 
async def login(login_data: LoginRequest, session: SessionDep, response: Response, request: Request):
    logger.debug(f"Login attempt for email: {login_data.email}")
    service = UserService(session)
    user = await service.authenticate_user(login_data.email, login_data.password)

    if not user:
        logger.warning(f"Login failed for {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = service.create_access_token({"id": user.id, "email": user.email})
    refresh_token = await service.create_refresh_token(user)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60
    )
    logger.info(f"Tokens issued for {login_data.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/refresh")
@limiter.limit("10/minute")  
async def refresh_token(request: RefreshRequest, session: SessionDep, req: Request):
    if not request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required",
        )

    service = UserService(session)
    new_access_token = await service.refresh_access_token(request.refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    logger.info("Access token refreshed successfully")
    return {"access_token": new_access_token, "token_type": "bearer"}
