from typing import Annotated

from fastapi import APIRouter, Query, Request

from backend.common.pagination import DependsPagination, paging_data
from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db_postgres import CurrentSession
from backend.utils.serializers import select_as_dict
from backend.plugins.user_analytics.schemas import CreateEventParam, GetEventDetails
from backend.plugins.user_analytics.service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/events", summary="Record an analytics event", dependencies=[DependsJwtAuth])
async def record_event(request: Request, obj: CreateEventParam) -> ResponseModel:
    event = await analytics_service.record(**obj.model_dump())
    return response_base.success(request=request, data=GetEventDetails(**select_as_dict(event)))


@router.get(
    "/events",
    summary="List analytics events (paginated, filterable)",
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def list_events(
    request: Request,
    db: CurrentSession,
    event_type: Annotated[str | None, Query()] = None,
    user_id: Annotated[int | None, Query()] = None,
) -> ResponseModel:
    stmt = await analytics_service.get_select(event_type=event_type, user_id=user_id)
    page = await paging_data(db, stmt, GetEventDetails)
    return response_base.success(request=request, data=page)


@router.get("/stats", summary="Event counts grouped by type", dependencies=[DependsJwtAuth])
async def stats(request: Request) -> ResponseModel:
    return response_base.success(request=request, data=await analytics_service.stats())
