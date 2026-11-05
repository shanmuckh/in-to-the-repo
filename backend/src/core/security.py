"""
Authentication and security module for JWT token handling and password management.
Uses bcrypt for secure password hashing and python-jose for JWT tokens.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import HTTPException, Header

# Load environment variables
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


# ===== Pydantic Schemas =====

class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: int
    email: str
    username: str


class Token(BaseModel):
    """Token response format."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    """User creation request schema."""
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    """User login request schema."""
    email: str
    password: str


# ===== Password Handling =====

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    # Encode password to bytes, hash it, and return as string
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ===== JWT Token Handling =====

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary with token claims (user_id, email, username, etc.)
        expires_delta: Custom token expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        TokenData if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        username: str = payload.get("username")
        
        if user_id is None or email is None:
            return None
        
        return TokenData(user_id=user_id, email=email, username=username)
        
    except JWTError:
        return None


def get_token_expiry_seconds() -> int:
    """Get token expiry time in seconds."""
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60


def require_auth(authorization: str = Header(...)) -> TokenData:
    """
    Dependency that requires valid authentication.
    Raises 401 if token is missing or invalid.
    
    Usage:
        @router.post("/api/endpoint")
        async def endpoint(user: TokenData = Depends(require_auth)):
            # user.user_id, user.email, user.username available
            ...
    
    Args:
        authorization: Authorization header (Bearer token)
    
    Returns:
        TokenData with user information
    
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    token = authorization[7:]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    return token_data
