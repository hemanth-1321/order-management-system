import logging
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schema import UserCreate
from src.config.settings import Config
from src.database.models import User, RefreshToken

logger = logging.getLogger(__name__)
bcrypt_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserService:
    """Service class to handle user-related operations: create, login, token generation, refresh"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------ Password hashing ------------------
    @staticmethod
    def hash_password(password: str) -> str:
        logger.debug("Hashing user password")
        return bcrypt_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        logger.debug("Verifying password")
        return bcrypt_context.verify(password, hashed_password)

    # ------------------ Token management ------------------
    @staticmethod
    def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False) -> str:
        """Create either an access or refresh JWT."""
        logger.debug(f"Creating {'refresh' if refresh else 'access'} token for {user_data.get('email')}")
        if expiry is None:
            expiry = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)

        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_data["id"],
            "email": user_data["email"],
            "type": "refresh" if refresh else "access",
            "exp": int((now + expiry).timestamp()),
            "iat": int(now.timestamp()),
            "jti": str(uuid.uuid4()),
        }

        token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
        logger.debug("JWT token created successfully")
        return token

    @staticmethod
    def decode_token(token: str) -> dict | None:
        """Decode a JWT token safely."""
        try:
            decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
            logger.debug("JWT token decoded successfully")
            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    # ------------------ Refresh Token ------------------
    async def create_refresh_token(self, user: User) -> str:
        """Create and persist a refresh token (replaces existing)."""
        logger.debug(f"Creating refresh token for user {user.email}")

        expiry = datetime.now(timezone.utc) + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = self.create_access_token(
            {"id": user.id, "email": user.email},
            expiry=timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS),
            refresh=True,
        )

        # Remove existing refresh token (enforce one per user)
        existing = await self.session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        old_token = existing.scalars().first()
        if old_token:
            await self.session.delete(old_token)
            await self.session.commit()

        new_refresh = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=expiry,
        )
        self.session.add(new_refresh)
        await self.session.commit()
        await self.session.refresh(new_refresh)

        logger.info(f"Refresh token stored for user {user.email}")
        return refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str | None:
        """Verify refresh token and issue new access token."""
        logger.debug("Attempting to refresh access token")

        try:
            decoded = jwt.decode(refresh_token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
            if decoded.get("type") != "refresh":
                logger.warning("Invalid token type (expected refresh)")
                return None

            user_id = decoded.get("sub")
            result = await self.session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()

            if not user:
                logger.warning("User not found for refresh token")
                return None

            stored_token = await self.session.execute(
                select(RefreshToken).where(RefreshToken.token == refresh_token)
            )
            token_entry = stored_token.scalars().first()

            if not token_entry:
                logger.warning("No stored refresh token found")
                return None

            if token_entry.expires_at < datetime.now(timezone.utc):
                logger.warning("Refresh token expired")
                await self.session.delete(token_entry)
                await self.session.commit()
                return None

            # ✅ Create new access token
            new_access = self.create_access_token({"id": user.id, "email": user.email})
            logger.info(f"Access token refreshed for user {user.email}")
            return new_access

        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None

    # ------------------ User CRUD ------------------
    async def create_user(self, user_data: UserCreate) -> User:
        logger.debug(f"Attempting to create user with email: {user_data.email}")

        existing_user = await self.session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalars().first():
            logger.warning(f"User with email {user_data.email} already exists")
            raise ValueError("User with this email already exists")

        hashed_password = self.hash_password(user_data.password)
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        logger.info(f"New user created: {new_user.email}")
        return new_user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        logger.debug(f"Authenticating user with email: {email}")
        result = await self.session.execute(select(User).filter(User.email == email))
        user = result.scalars().first()

        if not user:
            logger.warning(f"User not found for email: {email}")
            return None

        if not self.verify_password(password, user.password):
            logger.warning(f"Invalid password for user: {email}")
            return None

        logger.info(f"User {email} authenticated successfully")
        return user
