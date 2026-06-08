import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, get_id, id_key


class AnalyticsEvent(Base):
    """A single tracked event (page view, click, custom action…)."""

    __tablename__ = "analytics_event"

    id: Mapped[id_key] = mapped_column(init=False)
    x_id: Mapped[str] = mapped_column(sa.String(32), init=False, unique=True, default=get_id)
    event_type: Mapped[str] = mapped_column(sa.String(100), index=True, comment="e.g. 'page.view', 'button.click'")
    target: Mapped[str | None] = mapped_column(sa.String(200), default=None, comment="What was acted on")
    path: Mapped[str | None] = mapped_column(sa.String(300), default=None, comment="Route / DOM path")
    user_id: Mapped[int | None] = mapped_column(sa.Integer, index=True, default=None)
    session_id: Mapped[str | None] = mapped_column(sa.String(64), index=True, default=None)
    duration_ms: Mapped[int | None] = mapped_column(sa.Integer, default=None)
    # Optional heatmap fields (relative 0-1 positions)
    x_position: Mapped[float | None] = mapped_column(sa.Float, default=None)
    y_position: Mapped[float | None] = mapped_column(sa.Float, default=None)
    meta: Mapped[dict] = mapped_column(sa.JSON, default_factory=dict, comment="Free-form metadata")
