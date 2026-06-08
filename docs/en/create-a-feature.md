# Create a feature — a Todo API

Let's add a real, authenticated feature: a **per-user todo list** with ownership
rules and an admin-only "see everything" endpoint. It's 5 small files plus one
line — and shaapi handles the auth, DB, and responses for you.

> The complete code lives in [`examples/todolist`](../../examples/todolist).

## 1. The model — `backend/models/todo.py`

```python
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from backend.common.model import Base, get_id, id_key


class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[id_key] = mapped_column(init=False)
    x_id: Mapped[str] = mapped_column(sa.String(32), init=False, unique=True, default=get_id)
    title: Mapped[str] = mapped_column(sa.String(200))
    owner_id: Mapped[int] = mapped_column(sa.ForeignKey("user.id", ondelete="CASCADE"), index=True)
    description: Mapped[str | None] = mapped_column(sa.Text, default=None)
    completed: Mapped[bool] = mapped_column(sa.Boolean, default=False)
```

Register it in `backend/models/__init__.py`:

```python
from backend.models.todo import Todo
```

## 2. The schemas — `backend/app/admin/schema/todo.py`

```python
from datetime import datetime
from pydantic import ConfigDict, Field
from backend.common.schema import SchemaBase


class CreateTodoParam(SchemaBase):
    title: str = Field(..., max_length=200)
    description: str | None = None


class UpdateTodoParam(SchemaBase):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    completed: bool | None = None


class GetTodoDetails(SchemaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    x_id: str
    title: str
    description: str | None = None
    owner_id: int
    completed: bool
    created_time: datetime
```

## 3. Data access — `backend/crud/crud_todo.py`

```python
from sqlalchemy import desc, select
from backend.crud.crud_base import CRUDBase
from backend.models.todo import Todo
from backend.app.admin.schema.todo import CreateTodoParam, UpdateTodoParam


class CRUDTodo(CRUDBase[Todo]):
    async def get(self, db, pk: int):
        return await self.select_model(db, pk)

    async def get_list(self, owner_id=None, completed=None):
        stmt = select(self.model).order_by(desc(self.model.created_time))
        where = []
        if owner_id is not None:
            where.append(self.model.owner_id == owner_id)
        if completed is not None:
            where.append(self.model.completed == completed)
        return stmt.where(*where) if where else stmt

    async def create(self, db, obj_in: CreateTodoParam, owner_id: int):
        return await self.create_model(db, obj_in, owner_id=owner_id)

    async def update(self, db, pk: int, obj_in: UpdateTodoParam):
        return await self.update_model(db, pk, obj_in.model_dump(exclude_unset=True))

    async def delete(self, db, pk: int):
        return await self.delete_model(db, pk)


todo_dao = CRUDTodo(Todo)
```

## 4. Business logic — `backend/app/admin/service/todo_service.py`

Transactions and the ownership rule live here:

```python
from backend.crud.crud_todo import todo_dao
from backend.common.exception import errors
from backend.database.db_postgres import async_db_session


class TodoService:
    @staticmethod
    async def create(*, owner_id, obj):
        async with async_db_session.begin() as db:
            return await todo_dao.create(db, obj, owner_id=owner_id)

    @staticmethod
    async def get_select(*, owner_id=None, completed=None):
        return await todo_dao.get_list(owner_id=owner_id, completed=completed)

    @staticmethod
    async def _owned(db, *, pk, owner_id, is_admin):
        todo = await todo_dao.get(db, pk)
        if not todo:
            raise errors.NotFoundError(msg="Todo not found")
        if not is_admin and todo.owner_id != owner_id:
            raise errors.ForbiddenError(msg="This todo does not belong to you")
        return todo
    # get_by_id / update / delete reuse _owned — see examples/todolist


todo_service = TodoService()
```

## 5. The router — `backend/app/admin/api/v1/todo.py`

Defining a `router` here is all it takes — shaapi discovers it automatically.
`DependsJwtAuth` protects the route; `request.user` is the logged-in user.

```python
from typing import Annotated
from fastapi import APIRouter, Path, Request
from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.utils.serializers import select_as_dict
from backend.app.admin.schema.todo import CreateTodoParam, GetTodoDetails
from backend.app.admin.service.todo_service import todo_service

router = APIRouter(prefix="/todo", tags=["Todo"])


@router.post("/", summary="Create a todo", dependencies=[DependsJwtAuth])
async def create_todo(request: Request, obj: CreateTodoParam) -> ResponseModel:
    todo = await todo_service.create(owner_id=request.user.id, obj=obj)
    return response_base.success(request=request, data=GetTodoDetails(**select_as_dict(todo)))
```

(The full router adds list/get/update/delete and an admin-only `/todo/all`.)

## 6. Run & test

```bash
./docker-run.sh up        # dev: the table is auto-created on startup
```

Open Swagger at `http://localhost:8000/admin/api/v1/docs`, register a user, log
in, and the Todo endpoints are there. For a scripted proof:

```bash
python examples/todolist/smoke_test.py
```

It registers two users, creates todos, verifies a user **cannot** read another
user's todo (`403`), and that `/todo/all` is admin-only.

## Going to production

In production set `DB_AUTO_CREATE=false` and generate a migration instead of
relying on auto-create:

```bash
./docker-run.sh makemigrations "add todo table"
```

The migration file lands in `backend/alembic/versions/` — commit it. See
[Deployment](deployment.md).
