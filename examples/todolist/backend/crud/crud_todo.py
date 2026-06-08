from sqlalchemy import desc, select
from sqlalchemy.sql import Select

from backend.crud.crud_base import CRUDBase
from backend.models.todo import Todo
from backend.app.admin.schema.todo import CreateTodoParam, UpdateTodoParam


class CRUDTodo(CRUDBase[Todo]):
    async def get(self, db, pk: int) -> Todo | None:
        """Get a todo by primary key."""
        return await self.select_model(db, pk)

    async def get_list(self, owner_id: int | None = None, completed: bool | None = None) -> Select:
        """Build a Select for todos, optionally filtered by owner / completion."""
        stmt = select(self.model).order_by(desc(self.model.created_time))
        where = []
        if owner_id is not None:
            where.append(self.model.owner_id == owner_id)
        if completed is not None:
            where.append(self.model.completed == completed)
        if where:
            stmt = stmt.where(*where)
        return stmt

    async def create(self, db, obj_in: CreateTodoParam, owner_id: int) -> Todo:
        """Create a todo, injecting the owner from the authenticated user."""
        return await self.create_model(db, obj_in, owner_id=owner_id)

    async def update(self, db, pk: int, obj_in: UpdateTodoParam) -> int:
        """Update a todo (only the provided fields)."""
        return await self.update_model(db, pk, obj_in.model_dump(exclude_unset=True))

    async def delete(self, db, pk: int) -> int:
        """Delete a todo by primary key."""
        return await self.delete_model(db, pk)


todo_dao: CRUDTodo = CRUDTodo(Todo)
