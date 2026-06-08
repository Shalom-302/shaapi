from datetime import datetime

from pydantic import ConfigDict

from backend.common.schema import SchemaBase


class CreateAuditLogParam(SchemaBase):
    action: str
    resource: str
    user_id: int | None = None
    details: str | None = None


class GetAuditLogDetails(SchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    x_id: str
    action: str
    resource: str
    user_id: int | None = None
    details: str | None = None
    created_time: datetime
