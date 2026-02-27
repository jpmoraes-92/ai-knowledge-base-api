from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.schemas import TokenResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# In-memory user store (replace with database in production)
USERS_DB = {
    "admin": {
        "user_id": "user_001",
        "username": "admin",
        "hashed_password": hash_password("admin123"),
    },
    "test_user": {
        "user_id": "user_002", 
        "username": "test_user",
        "hashed_password": hash_password("test123"),
    },
}


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user by username and password.
    
    Args:
        username: Username to authenticate
        password: Plain text password
        
    Returns:
        User dictionary if authentication succeeds, None otherwise
    """
    user = USERS_DB.get(username)
    
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """
    Login endpoint that returns a JWT access token.
    
    Uses OAuth2 PasswordRequestForm for standard authentication flow.
    
    Args:
        form_data: OAuth2PasswordRequestForm with username and password
        
    Returns:
        TokenResponse with access_token, token_type, user_id, and expires_in
        
    Raises:
        HTTPException: If credentials are invalid (401 Unauthorized)
    """
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user_id as subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_id"]},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user["user_id"],
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user(user_id: str = Depends(get_current_user_id)) -> dict:
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        user_id: Current user_id extracted from JWT token
        
    Returns:
        Dictionary with user_id
        
    Raises:
        HTTPException: If token is invalid or missing (401 Unauthorized)
    """
    return {
        "user_id": user_id,
        "message": "Usuário autenticado com sucesso"
    }