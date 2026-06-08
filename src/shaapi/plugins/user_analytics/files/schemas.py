from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class CreateEventParam(SchemaBase):
    event_type: str
    target: str | None = None
    path: str | None = None
    user_id: int | None = None
    session_id: str | None = None
    duration_ms: int | None = None
    x_position: float | None = None
    y_position: float | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class GetEventDetails(SchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    x_id: str
    event_type: str
    target: str | None = None
    path: str | None = None
    user_id: int | None = None
    session_id: str | None = None
    duration_ms: int | None = None
    meta: dict[str, Any]
    created_time: datetime
