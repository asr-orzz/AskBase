from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_keys import validate_api_key
from app.auth.jwt import decode_token
from app.core.database import get_db
from app.models.organization import OrgRole, OrganizationMember
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    org_id: uuid.UUID | None
    role: str
    is_superuser: bool = False
    via_api_key: bool = False
    api_key_id: uuid.UUID | None = None


async def _get_auth_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """
    Extract authentication context from either:
    1. Bearer JWT token (Authorization header)
    2. API Key (X-API-Key header)
    """
    # Try API key first
    if x_api_key:
        api_key = await validate_api_key(db, x_api_key)
        if not api_key:
            raise HTTPException(401, "Invalid or expired API key")
        return AuthContext(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            tenant_id=api_key.tenant_id,
            org_id=api_key.organization_id,
            role="developer",
            via_api_key=True,
            api_key_id=api_key.id,
        )

    # Try JWT
    if credentials:
        try:
            payload = decode_token(credentials.credentials)
        except ValueError:
            raise HTTPException(401, "Invalid or expired token")

        user_id = uuid.UUID(payload["sub"])
        user = (await db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(401, "User not found or inactive")

        org_id = uuid.UUID(payload["org_id"]) if payload.get("org_id") else None
        role = payload.get("role", "viewer")

        return AuthContext(
            user_id=user.id,
            tenant_id=org_id or user.id,
            org_id=org_id,
            role=role,
            is_superuser=user.is_superuser,
        )

    raise HTTPException(401, "Missing authentication credentials")


RequireAuth = Annotated[AuthContext, Depends(_get_auth_context)]


def require_role(*allowed_roles: str):
    """Dependency factory: raises 403 if user role is not in allowed_roles."""

    async def _check(auth: RequireAuth) -> AuthContext:
        if auth.is_superuser:
            return auth
        if auth.role not in allowed_roles:
            raise HTTPException(
                403,
                f"Insufficient permissions. Required: {', '.join(allowed_roles)}"
            )
        return auth

    return Depends(_check)


RequireAdmin = Annotated[AuthContext, require_role("admin")]
RequireDeveloper = Annotated[AuthContext, require_role("admin", "developer")]
RequireViewer = Annotated[AuthContext, require_role("admin", "developer", "viewer")]
