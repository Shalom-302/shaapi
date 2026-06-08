from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class CreatePaymentParam(SchemaBase):
    amount: int = Field(..., gt=0, description="Amount in the smallest currency unit (cents)")
    currency: str = "usd"


class GetPaymentDetails(SchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    x_id: str
    amount: int
    currency: str
    status: str
    provider: str
    reference: str | None = None
    user_id: int | None = None
    meta: dict[str, Any]
    created_time: datetime
