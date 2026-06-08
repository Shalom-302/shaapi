from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class TodoSchemaBase(SchemaBase):
    title: str = Field(..., max_length=200)
    description: str | None = None


class CreateTodoParam(TodoSchemaBase):
    pass


class UpdateTodoParam(SchemaBase):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    completed: bool | None = None


class GetTodoDetails(TodoSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    x_id: str
    owner_id: int
    completed: bool
    created_time: datetime
