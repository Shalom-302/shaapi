from sqlalchemy import Select

from backend.crud.crud_todo import todo_dao
from backend.models.todo import Todo
from backend.app.admin.schema.todo import CreateTodoParam, UpdateTodoParam
from backend.common.exception import errors
from backend.database.db_postgres import async_db_session


class TodoService:
    @staticmethod
    async def create(*, owner_id: int, obj: CreateTodoParam) -> Todo:
        async with async_db_session.begin() as db:
            return await todo_dao.create(db, obj, owner_id=owner_id)

    @staticmethod
    async def get_select(*, owner_id: int | None = None, completed: bool | None = None) -> Select:
        return await todo_dao.get_list(owner_id=owner_id, completed=completed)

    @staticmethod
    async def _get_owned(db, *, pk: int, owner_id: int, is_admin: bool) -> Todo:
        todo = await todo_dao.get(db, pk)
        if not todo:
            raise errors.NotFoundError(msg="Todo not found")
        if not is_admin and todo.owner_id != owner_id:
            raise errors.ForbiddenError(msg="This todo does not belong to you")
        return todo

    @staticmethod
    async def get_by_id(*, pk: int, owner_id: int, is_admin: bool) -> Todo:
        async with async_db_session() as db:
            return await TodoService._get_owned(db, pk=pk, owner_id=owner_id, is_admin=is_admin)

    @staticmethod
    async def update(*, pk: int, owner_id: int, is_admin: bool, obj: UpdateTodoParam) -> int:
        async with async_db_session.begin() as db:
            await TodoService._get_owned(db, pk=pk, owner_id=owner_id, is_admin=is_admin)
            return await todo_dao.update(db, pk, obj)

    @staticmethod
    async def delete(*, pk: int, owner_id: int, is_admin: bool) -> int:
        async with async_db_session.begin() as db:
            await TodoService._get_owned(db, pk=pk, owner_id=owner_id, is_admin=is_admin)
            return await todo_dao.delete(db, pk)


todo_service = TodoService()
