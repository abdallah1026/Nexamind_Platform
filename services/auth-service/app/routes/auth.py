from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone, timedelta
from typing import Optional
import re

from ..core.database import get_db
from ..core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_api_key, hash_api_key
)
from ..core.config import settings
from ..models.tenant import Tenant
from ..models.user import User
from ..models.role import Role
from ..models.api_key import APIKey
from ..schemas.auth import (
    TenantCreate, TenantResponse, LoginRequest, TokenResponse,
    RefreshRequest, APIKeyCreate, APIKeyResponse, UserResponse
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_tenant(data: TenantCreate, db: AsyncSession = Depends(get_db)):
    """Register a new tenant with an admin user"""
    
    existing = await db.execute(select(Tenant).where(Tenant.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    tenant = Tenant(name=data.name, slug=data.slug)
    db.add(tenant)
    await db.flush()

    role = Role(
        tenant_id=tenant.id,
        name="admin",
        permissions=["*"],
        is_system=True
    )
    db.add(role)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        role_id=role.id,
        email=data.admin_email,
        hashed_password=hash_password(data.admin_password),
        full_name=data.admin_full_name,
        is_verified=True
    )
    db.add(user)
    await db.commit()
    
    tokens = _create_tokens(user)
    return {
        "tenant": {"id": str(tenant.id), "name": tenant.name, "slug": tenant.slug},
        "user": {"id": str(user.id), "email": user.email},
        **tokens
    }

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    await db.execute(
        update(User).where(User.id == user.id).values(last_login=datetime.now(timezone.utc))
    )
    await db.commit()
    return TokenResponse(**_create_tokens(user))

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    return TokenResponse(**_create_tokens(user))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/api-key", response_model=APIKeyResponse)
async def create_api_key(
    data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    full_key, key_hash, key_prefix = generate_api_key()
    expires_at = None
    if data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)
    
    api_key = APIKey(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=data.scopes,
        expires_at=expires_at
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    response = APIKeyResponse.model_validate(api_key)
    response.full_key = full_key  
    return response

def _create_tokens(user: User) -> dict:
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
