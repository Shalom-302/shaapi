import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, get_id, id_key


class Payment(Base):
    """A payment intent recorded by shaapi and (optionally) a provider."""

    __tablename__ = "payment"

    id: Mapped[id_key] = mapped_column(init=False)
    x_id: Mapped[str] = mapped_column(sa.String(32), init=False, unique=True, default=get_id)
    amount: Mapped[int] = mapped_column(sa.Integer, comment="Amount in the smallest currency unit (e.g. cents)")
    currency: Mapped[str] = mapped_column(sa.String(8), default="usd")
    status: Mapped[str] = mapped_column(sa.String(20), default="pending", index=True, comment="pending|succeeded|failed")
    provider: Mapped[str] = mapped_column(sa.String(30), default="stripe")
    reference: Mapped[str | None] = mapped_column(sa.String(200), default=None, comment="Provider payment id")
    user_id: Mapped[int | None] = mapped_column(sa.Integer, index=True, default=None)
    meta: Mapped[dict] = mapped_column(sa.JSON, default_factory=dict)
