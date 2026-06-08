import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, get_id, id_key


class Todo(Base):
    """A todo item, owned by a user."""

    __tablename__ = "todo"

    id: Mapped[id_key] = mapped_column(init=False)
    x_id: Mapped[str] = mapped_column(sa.String(32), init=False, unique=True, default=get_id)
    title: Mapped[str] = mapped_column(sa.String(200), comment="Todo title")
    owner_id: Mapped[int] = mapped_column(
        sa.ForeignKey("user.id", ondelete="CASCADE"), index=True, comment="Owner user id"
    )
    description: Mapped[str | None] = mapped_column(sa.Text, default=None, comment="Optional details")
    completed: Mapped[bool] = mapped_column(sa.Boolean, default=False, comment="Completion status")
