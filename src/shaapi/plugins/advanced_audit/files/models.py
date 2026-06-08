import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, get_id, id_key


class AuditLog(Base):
    """A single audit-trail entry: who did what, on which resource."""

    __tablename__ = "audit_log"

    id: Mapped[id_key] = mapped_column(init=False)
    x_id: Mapped[str] = mapped_column(sa.String(32), init=False, unique=True, default=get_id)
    action: Mapped[str] = mapped_column(sa.String(100), index=True, comment="e.g. 'order.created'")
    resource: Mapped[str] = mapped_column(sa.String(100), index=True, comment="e.g. 'order'")
    user_id: Mapped[int | None] = mapped_column(sa.Integer, index=True, default=None, comment="Actor user id")
    details: Mapped[str | None] = mapped_column(sa.Text, default=None, comment="Extra context")
