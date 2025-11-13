from passlib.context import CryptContext
from datetime import timedelta, datetime
import jwt
from config.settings import Config
import datetime
import uuid
import logging
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def generate_passwd_hash(password: str) -> str:
    """
    Generate a bcrypt hash of the given password.

    Args:
        password (str): Plain-text password

    Returns:
        str: Hashed password
    """
    return bcrypt_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.

    Args:
        password (str): Plain-text password
        hashed_password (str): Bcrypt hashed password

    Returns:
        bool: True if the password matches, False otherwise
    """
    return bcrypt_context.verify(password, hashed_password)

def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False) -> str:
    """
    Create a JWT token (access or refresh) for a user.

    Args:
        user_data (dict): Dictionary containing user info to encode in the token
        expiry (timedelta, optional): Token lifetime. Defaults to Config.ACCESS_TOKEN_EXPIRE_MINUTES
        refresh (bool, optional): True if this is a refresh token. Defaults to False

    Returns:
        str: Encoded JWT token
    """
    if expiry is None:
        expiry = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(datetime.timezone.utc)
    payload = {
        "user": user_data.copy(),
        "exp": int((now + expiry).timestamp()),  # Expiration time as POSIX timestamp
        "iat": int(now.timestamp()),             # Issued at timestamp
        "jti": str(uuid.uuid4()),               # Unique token ID
        "refresh": refresh                      # Refresh token indicator
    }

    token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return token


def decode_token(token: str) -> dict | None:
    """
    Decode a JWT token and return its payload.

    Args:
        token (str): JWT token

    Returns:
        dict | None: Decoded payload if valid, None if invalid
    """
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    except jwt.ExpiredSignatureError:
        logging.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logging.warning(f"Invalid token: {e}")
        return None