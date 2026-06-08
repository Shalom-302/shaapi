from typing import Annotated

from fastapi import APIRouter, Path, Query, Request

from backend.common.exception import errors
from backend.common.pagination import DependsPagination, paging_data
from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db_postgres import CurrentSession
from backend.utils.serializers import select_as_dict
from backend.app.admin.schema.todo import CreateTodoParam, GetTodoDetails, UpdateTodoParam
from backend.app.admin.service.todo_service import todo_service

router = APIRouter(prefix="/todo", tags=["Todo"])


def _is_admin(request: Request) -> bool:
    """True if the current user has the 'admin' role."""
    roles = getattr(request.user, "roles", None) or []
    names = []
    for r in roles:
        if isinstance(r, dict):
            names.append(r.get("name"))
        else:
            names.append(getattr(r, "name", None))
    return "admin" in names


@router.post("/", summary="Create a todo", dependencies=[DependsJwtAuth])
async def create_todo(request: Request, obj: CreateTodoParam) -> ResponseModel:
    todo = await todo_service.create(owner_id=request.user.id, obj=obj)
    return response_base.success(request=request, data=GetTodoDetails(**select_as_dict(todo)))


@router.get(
    "/",
    summary="List my todos (paginated)",
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def list_my_todos(
    request: Request,
    db: CurrentSession,
    completed: Annotated[bool | None, Query()] = None,
) -> ResponseModel:
    stmt = await todo_service.get_select(owner_id=request.user.id, completed=completed)
    page = await paging_data(db, stmt, GetTodoDetails)
    return response_base.success(request=request, data=page)


@router.get(
    "/all",
    summary="List every user's todos (admin only)",
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def list_all_todos(request: Request, db: CurrentSession) -> ResponseModel:
    if not _is_admin(request):
        raise errors.ForbiddenError(msg="Admin role required")
    stmt = await todo_service.get_select()
    page = await paging_data(db, stmt, GetTodoDetails)
    return response_base.success(request=request, data=page)


@router.get("/{pk}", summary="Get a todo", dependencies=[DependsJwtAuth])
async def get_todo(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    todo = await todo_service.get_by_id(pk=pk, owner_id=request.user.id, is_admin=_is_admin(request))
    return response_base.success(request=request, data=GetTodoDetails(**select_as_dict(todo)))


@router.put("/{pk}", summary="Update a todo", dependencies=[DependsJwtAuth])
async def update_todo(
    request: Request, pk: Annotated[int, Path(...)], obj: UpdateTodoParam
) -> ResponseModel:
    count = await todo_service.update(
        pk=pk, owner_id=request.user.id, is_admin=_is_admin(request), obj=obj
    )
    return response_base.success(request=request) if count else response_base.fail(request=request)


@router.delete("/{pk}", summary="Delete a todo", dependencies=[DependsJwtAuth])
async def delete_todo(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    count = await todo_service.delete(pk=pk, owner_id=request.user.id, is_admin=_is_admin(request))
    return response_base.success(request=request) if count else response_base.fail(request=request)
