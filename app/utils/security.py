"""
utils/security.py
-----------------
Handles password hashing and JWT (JSON Web Token) operations.

JWT is how we authenticate users:
1. User logs in with email/password
2. Server verifies password and creates a JWT token
3. User sends this token in the 'Authorization' header on future requests
4. Server decodes the token to know who is making the request

Think of JWT like a stamped ticket: the server "stamps" it on login,
and the server can verify the stamp on each request without hitting the database.
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()

# CryptContext handles password hashing.
# bcrypt is a slow, secure hashing algorithm designed for passwords.
# schemes=["bcrypt"] means we use bcrypt.
# deprecated="auto" means old algorithms are auto-rejected.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    Returns a string like: "$2b$12$..."
    The original password CANNOT be recovered from this hash.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain-text password matches a stored hash.
    Returns True if they match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT token containing the given data (payload).
    
    The token expires after ACCESS_TOKEN_EXPIRE_MINUTES minutes.
    The token is signed with JWT_SECRET - without this secret, the token
    cannot be forged or tampered with.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    Decode and verify a JWT token.
    Returns the payload dict if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
