from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from .config import Settings


class User(BaseModel):
    """User model for authentication."""
    username: str
    is_agent: bool = False


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"


async def create_access_token(
    data: dict,
    settings: Settings,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new JWT token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create access token: {str(e)}"
        )


async def get_current_user(token: str) -> Optional[User]:
    """Validate JWT token and return user."""
    settings = Settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        
        return User(
            username=username,
            is_agent=payload.get("is_agent", False)
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        ) 