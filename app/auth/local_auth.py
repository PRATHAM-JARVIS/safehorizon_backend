"""
Local authentication system for development/testing without Supabase dependency
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt as bcrypt_lib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.database_models import Tourist, Authority


class LocalAuthService:
    def __init__(self):
        # Simple JWT secret for local development
        self.jwt_secret = "local-dev-secret-key-change-in-production"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        # Encode password to bytes and hash it
        password_bytes = password.encode('utf-8')
        salt = bcrypt_lib.gensalt()
        hashed = bcrypt_lib.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        # Encode both to bytes for comparison
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt_lib.checkpw(password_bytes, hashed_bytes)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token (no expiration)"""
        to_encode = data.copy()
        # Remove expiration - tokens will not expire
        # expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        # to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    async def create_tourist_account(self, db: AsyncSession, email: str, password: str, **kwargs) -> str:
        """Create a new tourist account locally"""
        # Check if user already exists
        result = await db.execute(select(Tourist).where(Tourist.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValueError("User already exists")
        
        # Generate UUID-like ID
        user_id = secrets.token_hex(16)
        hashed_password = self.hash_password(password)
        
        tourist = Tourist(
            id=user_id,
            email=email,
            name=kwargs.get('name'),
            phone=kwargs.get('phone'),
            emergency_contact=kwargs.get('emergency_contact'),
            emergency_phone=kwargs.get('emergency_phone'),
            password_hash=hashed_password  # We'll need to add this field
        )
        
        db.add(tourist)
        await db.commit()
        await db.refresh(tourist)
        
        return user_id
    
    async def authenticate_tourist(self, db: AsyncSession, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate tourist user"""
        result = await db.execute(select(Tourist).where(Tourist.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not hasattr(user, 'password_hash'):
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        # Create access token
        access_token = self.create_access_token({
            "sub": user.id,
            "email": user.email,
            "role": "tourist"
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "role": "tourist"
        }
    
    async def create_authority_account(self, db: AsyncSession, email: str, password: str, **kwargs) -> str:
        """Create a new authority account locally"""
        # Check if user already exists
        result = await db.execute(select(Authority).where(Authority.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValueError("Authority user already exists")
        
        # Generate UUID-like ID
        user_id = secrets.token_hex(16)
        hashed_password = self.hash_password(password)
        
        authority = Authority(
            id=user_id,
            email=email,
            name=kwargs.get('name'),
            badge_number=kwargs.get('badge_number'),
            department=kwargs.get('department'),
            rank=kwargs.get('rank'),
            password_hash=hashed_password
        )
        
        db.add(authority)
        await db.commit()
        await db.refresh(authority)
        
        return user_id
    
    async def authenticate_authority(self, db: AsyncSession, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate authority user"""
        result = await db.execute(select(Authority).where(Authority.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not hasattr(user, 'password_hash'):
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        # Determine role - admin users have specific email or rank
        role = "authority"
        if email == "admin" or (hasattr(user, 'rank') and user.rank and "admin" in user.rank.lower()):
            role = "admin"
        
        # Create access token
        access_token = self.create_access_token({
            "sub": user.id,
            "email": user.email,
            "role": role
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "role": role
        }


# Global instance
local_auth = LocalAuthService()