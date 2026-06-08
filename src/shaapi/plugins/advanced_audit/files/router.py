from typing import Annotated

from fastapi import APIRouter, Path, Query, Request

from backend.common.pagination import DependsPagination, paging_data
from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db_postgres import CurrentSession
from backend.utils.serializers import select_as_dict
from backend.plugins.advanced_audit.schemas import CreateAuditLogParam, GetAuditLogDetails
from backend.plugins.advanced_audit.service import audit_service

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "/logs",
    summary="List audit logs (paginated, filterable)",
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def list_audit_logs(
    request: Request,
    db: CurrentSession,
    action: Annotated[str | None, Query()] = None,
    resource: Annotated[str | None, Query()] = None,
    user_id: Annotated[int | None, Query()] = None,
) -> ResponseModel:
    stmt = await audit_service.get_select(action=action, resource=resource, user_id=user_id)
    page = await paging_data(db, stmt, GetAuditLogDetails)
    return response_base.success(request=request, data=page)


@router.post("/logs", summary="Record an audit log", dependencies=[DependsJwtAuth])
async def create_audit_log(request: Request, obj: CreateAuditLogParam) -> ResponseModel:
    log = await audit_service.record(
        action=obj.action, resource=obj.resource, user_id=obj.user_id, details=obj.details
    )
    return response_base.success(request=request, data=GetAuditLogDetails(**select_as_dict(log)))


@router.get("/logs/{pk}", summary="Get an audit log", dependencies=[DependsJwtAuth])
async def get_audit_log(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    log = await audit_service.get_by_id(pk=pk)
    return response_base.success(request=request, data=GetAuditLogDetails(**select_as_dict(log)))


@router.delete("/logs/{pk}", summary="Delete an audit log", dependencies=[DependsJwtAuth])
async def delete_audit_log(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    count = await audit_service.delete(pk=pk)
    return response_base.success(request=request) if count else response_base.fail(request=request)
