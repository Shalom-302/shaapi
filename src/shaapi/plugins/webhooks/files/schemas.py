from typing import Any

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class CreateWebhookParam(SchemaBase):
    name: str
    event: str
    url: str
    secret: str | None = None
    is_enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class UpdateWebhookParam(SchemaBase):
    name: str | None = None
    event: str | None = None
    url: str | None = None
    secret: str | None = None
    is_enabled: bool | None = None
    config: dict[str, Any] | None = None


class GetWebhookDetails(SchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    x_id: str
    name: str
    event: str
    url: str
    is_enabled: bool
    config: dict[str, Any]
    # `secret` is intentionally omitted from output.
