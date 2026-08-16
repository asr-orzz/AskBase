from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.auth.api_keys import create_api_key, revoke_api_key
from app.auth.dependencies import RequireAuth, RequireAdmin
from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.passwords import hash_password, verify_password
from app.core.dependencies import DatabaseSession
from app.models.api_key import ApiKey
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.user import User

router = APIRouter(tags=["Auth"])


# --- Schemas ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    org_name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    org_id: str


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1)
    expires_at: datetime | None = None


# --- Registration & Login ---

@router.post("/auth/register", status_code=201)
async def register(data: RegisterRequest, db: DatabaseSession):
    existing = (await db.execute(
        select(User).where(User.email == data.email)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()

    slug = data.org_name.lower().replace(" ", "-")[:50]
    org = Organization(name=data.org_name, slug=slug)
    db.add(org)
    await db.flush()

    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.ADMIN,
    )
    db.add(membership)
    await db.flush()

    access = create_access_token(user.id, org.id, "admin")
    refresh = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=str(user.id),
        org_id=str(org.id),
    )


@router.post("/auth/login")
async def login(data: LoginRequest, db: DatabaseSession):
    user = (await db.execute(
        select(User).where(User.email == data.email)
    )).scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")

    membership = (await db.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )).scalar_one_or_none()

    org_id = membership.organization_id if membership else None
    role = membership.role.value if membership else "viewer"

    access = create_access_token(user.id, org_id, role)
    refresh = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=str(user.id),
        org_id=str(org_id) if org_id else "",
    )


@router.get("/auth/me")
async def get_current_user(auth: RequireAuth, db: DatabaseSession):
    user = (await db.execute(
        select(User).where(User.id == auth.user_id)
    )).scalar_one_or_none()

    return {
        "id": str(auth.user_id),
        "email": user.email if user else "",
        "full_name": user.full_name if user else "",
        "org_id": str(auth.org_id) if auth.org_id else None,
        "role": auth.role,
        "is_superuser": auth.is_superuser,
        "via_api_key": auth.via_api_key,
    }


# --- API Key Management ---

@router.post("/api-keys", status_code=201)
async def create_key(data: ApiKeyCreate, auth: RequireAuth, db: DatabaseSession):
    if not auth.org_id:
        raise HTTPException(400, "No organization context")

    full_key, api_key = await create_api_key(
        db, auth.tenant_id, auth.org_id, data.name, data.expires_at,
    )

    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": full_key,
        "prefix": api_key.key_prefix,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "warning": "Store this key securely. It will not be shown again.",
    }


@router.get("/api-keys")
async def list_keys(auth: RequireAuth, db: DatabaseSession):
    if not auth.org_id:
        raise HTTPException(400, "No organization context")

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.organization_id == auth.org_id,
        ).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        {
            "id": str(k.id),
            "name": k.name,
            "prefix": k.key_prefix,
            "is_active": k.is_active,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else "",
        }
        for k in keys
    ]


@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_key(key_id: uuid.UUID, auth: RequireAuth, db: DatabaseSession):
    success = await revoke_api_key(db, key_id)
    if not success:
        raise HTTPException(404, "API key not found")
