import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, get_id, id_key


class WebhookSubscription(Base):
    """A subscription that receives HTTP callbacks for a given event."""

    __tablename__ = "webhook_subscription"

    id: Mapped[id_key] = mapped_column(init=False)
    x_id: Mapped[str] = mapped_column(sa.String(32), init=False, unique=True, default=get_id)
    name: Mapped[str] = mapped_column(sa.String(100), comment="Descriptive name")
    event: Mapped[str] = mapped_column(sa.String(100), index=True, comment="Event key, e.g. 'order.placed'")
    url: Mapped[str] = mapped_column(sa.String(500), comment="Target URL to POST to")
    secret: Mapped[str | None] = mapped_column(sa.String(200), default=None, comment="Optional HMAC signing secret")
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    config: Mapped[dict] = mapped_column(sa.JSON, default_factory=dict, comment="Free-form settings")
