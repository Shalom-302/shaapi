from typing import Annotated

from fastapi import APIRouter, Path, Request

from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.utils.serializers import select_as_dict, select_list_serialize
from backend.plugins.webhooks.schemas import (
    CreateWebhookParam,
    GetWebhookDetails,
    UpdateWebhookParam,
)
from backend.plugins.webhooks.service import webhook_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/", summary="List webhook subscriptions", dependencies=[DependsJwtAuth])
async def list_webhooks(request: Request) -> ResponseModel:
    data = select_list_serialize(await webhook_service.get_all())
    return response_base.success(request=request, data=data)


@router.post("/", summary="Create a webhook subscription", dependencies=[DependsJwtAuth])
async def create_webhook(request: Request, obj: CreateWebhookParam) -> ResponseModel:
    wh = await webhook_service.create(obj=obj)
    return response_base.success(request=request, data=GetWebhookDetails(**select_as_dict(wh)))


@router.get("/{pk}", summary="Get a webhook subscription", dependencies=[DependsJwtAuth])
async def get_webhook(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    wh = await webhook_service.get_by_id(pk=pk)
    return response_base.success(request=request, data=GetWebhookDetails(**select_as_dict(wh)))


@router.put("/{pk}", summary="Update a webhook subscription", dependencies=[DependsJwtAuth])
async def update_webhook(
    request: Request, pk: Annotated[int, Path(...)], obj: UpdateWebhookParam
) -> ResponseModel:
    count = await webhook_service.update(pk=pk, obj=obj)
    return response_base.success(request=request) if count else response_base.fail(request=request)


@router.delete("/{pk}", summary="Delete a webhook subscription", dependencies=[DependsJwtAuth])
async def delete_webhook(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    count = await webhook_service.delete(pk=pk)
    return response_base.success(request=request) if count else response_base.fail(request=request)
