import enum

from sqlalchemy import Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuthProvider(str, enum.Enum):
    EMAIL = "email"


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_provider: Mapped[AuthProvider] = mapped_column(
        SAEnum(AuthProvider, values_callable=lambda e: [x.value for x in e], name="auth_provider"),
        default=AuthProvider.EMAIL,
        nullable=False,
    )
    custom_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    use_custom_key: Mapped[bool] = mapped_column(default=False, nullable=False)
