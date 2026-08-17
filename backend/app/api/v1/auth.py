from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.dependencies import DatabaseSession
from app.models.user import AuthProvider, User

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    auth_provider: str

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            auth_provider=user.auth_provider.value,
        )


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


def _create_token(user: User) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest, db: DatabaseSession):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        name=data.email.split("@")[0],
        password_hash=_hash_password(data.password),
        auth_provider=AuthProvider.EMAIL,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    await logger.ainfo("User registered", user_id=str(user.id), email=data.email)
    return AuthResponse(user=UserResponse.from_user(user), token=_create_token(user))


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: DatabaseSession):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not _verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return AuthResponse(user=UserResponse.from_user(user), token=_create_token(user))


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.from_user(user)
