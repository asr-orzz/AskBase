from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey

API_KEY_PREFIX = "rag_"


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (full_key, key_hash, key_prefix)."""
    raw = secrets.token_urlsafe(32)
    full_key = f"{API_KEY_PREFIX}{raw}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:12]
    return full_key, key_hash, key_prefix


async def create_api_key(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    organization_id: uuid.UUID,
    name: str,
    expires_at: datetime | None = None,
) -> tuple[str, ApiKey]:
    """Create and persist a new API key. Returns the plaintext key (shown once) and the record."""
    full_key, key_hash, key_prefix = generate_api_key()

    api_key = ApiKey(
        tenant_id=tenant_id,
        organization_id=organization_id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.flush()
    return full_key, api_key


async def validate_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    """Validate an API key and return the record if valid."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        return None

    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        return None

    api_key.last_used_at = datetime.now(timezone.utc)
    await db.flush()
    return api_key


async def revoke_api_key(db: AsyncSession, key_id: uuid.UUID) -> bool:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        return False
    api_key.is_active = False
    await db.flush()
    return True
