import logging
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.future import select

from src.auth.schema import UserCreate
from src.config.settings import Config
from src.database.models import User, RefreshToken
from src.database.db import SessionDep
logger = logging.getLogger(__name__)
bcrypt_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserService:
    """
    Service class to handle user-related operations:
    - User creation and authentication
    - Password hashing & verification
    - JWT access & refresh token management
    - Refresh token persistence
    """

    def __init__(self, session: SessionDep):
        """
        Initialize the service with a SQLAlchemy SessionDep.
        :param session: Async database session for CRUD operations
        """
        self.session = session

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plaintext password using Argon2.
        :param password: plaintext password
        :return: hashed password string
        """
        logger.debug("Hashing user password")
        return bcrypt_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a hashed password.
        :param password: plaintext password
        :param hashed_password: hashed password from DB
        :return: True if valid, False otherwise
        """
        logger.debug("Verifying password")
        return bcrypt_context.verify(password, hashed_password)

    @staticmethod
    def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False) -> str:
        """
        Create a JWT token (access or refresh).
        :param user_data: dictionary containing at least 'id' and 'email'
        :param expiry: token lifetime; defaults to Config.ACCESS_TOKEN_EXPIRE_MINUTES
        :param refresh: whether this is a refresh token
        :return: encoded JWT string
        """
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
        """
        Decode a JWT token safely.
        :param token: JWT token string
        :return: decoded payload if valid, None otherwise
        """
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

    async def create_refresh_token(self, user: User) -> str:
        """
        Generate a refresh token, remove any existing token for the user,
        and store it in the database.
        :param user: User instance
        :return: refresh token string
        """
        logger.debug(f"Creating refresh token for user {user.email}")
        expiry = datetime.now(timezone.utc) + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = self.create_access_token(
            {"id": user.id, "email": user.email},
            expiry=timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS),
            refresh=True,
        )

        existing = await self.session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        old_token = existing.scalars().first()
        if old_token:
            await self.session.delete(old_token)
            await self.session.commit()

        new_refresh = RefreshToken(token=refresh_token, user_id=user.id, expires_at=expiry)
        self.session.add(new_refresh)
        await self.session.commit()
        await self.session.refresh(new_refresh)

        logger.info(f"Refresh token stored for user {user.email}")
        return refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str | None:
        """
        Validate a refresh token and issue a new access token.
        :param refresh_token: the stored refresh token
        :return: new access token if valid, None otherwise
        """
        logger.debug("Attempting to refresh access token")
        try:
            decoded = jwt.decode(refresh_token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])

            # Ensure token is a refresh token
            if decoded.get("type") != "refresh":
                logger.warning("Invalid token type (expected refresh)")
                return None

            # Fetch the user
            user_id = decoded.get("sub")
            result = await self.session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                logger.warning("User not found for refresh token")
                return None

            # Fetch stored refresh token
            stored_token = await self.session.execute(
                select(RefreshToken).where(RefreshToken.token == refresh_token)
            )
            token_entry = stored_token.scalars().first()
            if not token_entry:
                logger.warning("No stored refresh token found")
                return None

            # Check expiry
            if token_entry.expires_at < datetime.now(timezone.utc):
                logger.warning("Refresh token expired")
                await self.session.delete(token_entry)
                await self.session.commit()
                return None

            # Issue new access token
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
        """
        Create a new user after verifying email uniqueness and hashing password.
        :param user_data: UserCreate Pydantic schema
        :return: User instance
        """
        logger.debug(f"Attempting to create user with email: {user_data.email}")

        # Check for existing user
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
        """
        Authenticate user credentials.
        :param email: user email
        :param password: plaintext password
        :return: User instance if valid, None otherwise
        """
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
