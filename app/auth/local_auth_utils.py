"""
Local authentication utilities that don't depend on Supabase
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .local_auth import local_auth
from ..database import get_db
from ..models.database_models import Tourist, Authority

security = HTTPBearer()


class AuthUser:
    def __init__(self, user_id: str, email: str, role: Optional[str] = None):
        self.id = user_id
        self.email = email
        self.role = role or "tourist"


async def create_user_account(email: str, password: str, role: str = "tourist", **kwargs) -> Dict[str, Any]:
    """Create a new user account locally"""
    from ..database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            if role == "tourist":
                user_id = await local_auth.create_tourist_account(db, email, password, **kwargs)
            elif role == "authority":
                user_id = await local_auth.create_authority_account(db, email, password, **kwargs)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported role: {role}"
                )
            
            return {"user": {"id": user_id, "email": email}}
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


async def authenticate_user(email: str, password: str, role: str = "tourist") -> Dict[str, Any]:
    """Authenticate user locally"""
    from ..database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        if role == "tourist":
            result = await local_auth.authenticate_tourist(db, email, password)
        else:
            result = await local_auth.authenticate_authority(db, email, password)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return result


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthUser:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    try:
        payload = local_auth.verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", "tourist")
    
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return AuthUser(user_id=user_id, email=email, role=role)


async def get_current_tourist(current_user: AuthUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Tourist:
    """Get current tourist from database"""
    if current_user.role not in ["tourist", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Tourist role required. Current role: {current_user.role}"
        )
    
    result = await db.execute(select(Tourist).where(Tourist.id == current_user.id))
    tourist = result.scalar_one_or_none()
    
    if not tourist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tourist not found"
        )
    
    return tourist


async def get_current_authority(current_user: AuthUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Authority:
    """Get current authority from database"""
    if current_user.role not in ["authority", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Authority role required"
        )
    
    result = await db.execute(select(Authority).where(Authority.id == current_user.id))
    authority = result.scalar_one_or_none()
    
    if not authority:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authority not found"
        )
    
    return authority


async def get_current_admin(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Get current admin user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin role required"
        )
    
    return current_user