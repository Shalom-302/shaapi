import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class AuthMfa(Base):
    """A user's TOTP multi-factor authentication secret (one per user)."""

    __tablename__ = "auth_mfa"

    id: Mapped[id_key] = mapped_column(init=False)
    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("user.id", ondelete="CASCADE"), unique=True, index=True
    )
    secret: Mapped[str] = mapped_column(sa.String(64), comment="Base32 TOTP secret")
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=False)
