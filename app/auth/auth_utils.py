from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from supabase import Client
from .supabase_client import get_supabase, get_service_supabase
from ..config import get_settings

security = HTTPBearer()
settings = get_settings()


class AuthUser:
    def __init__(self, user_id: str, email: str, role: Optional[str] = None):
        self.id = user_id
        self.email = email
        self.role = role or "tourist"


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token using Supabase JWT secret"""
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured"
        )
    
    try:
        payload = jwt.decode(
            token, 
            settings.supabase_jwt_secret, 
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthUser:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", "tourist")
    
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return AuthUser(user_id=user_id, email=email, role=role)


async def get_current_tourist(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require tourist role"""
    if current_user.role not in ["tourist", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tourist access required"
        )
    return current_user


async def get_current_authority(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require authority role"""
    if current_user.role not in ["authority", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authority access required"
        )
    return current_user


async def get_current_admin(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def create_user_account(email: str, password: str, role: str = "tourist") -> Dict[str, Any]:
    """Create user account via Supabase Auth"""
    supabase = get_service_supabase()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase not configured"
        )
    
    try:
        # Create user with custom claims
        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "user_metadata": {"role": role}
        })
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


async def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticate user via Supabase Auth"""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase not configured"
        )
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )