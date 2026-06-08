from typing import Annotated

from fastapi import APIRouter, Path, Query, Request

from backend.common.pagination import DependsPagination, paging_data
from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db_postgres import CurrentSession
from backend.utils.serializers import select_as_dict
from backend.plugins.payment.schemas import CreatePaymentParam, GetPaymentDetails
from backend.plugins.payment.service import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", summary="Create a payment", dependencies=[DependsJwtAuth])
async def create_payment(request: Request, obj: CreatePaymentParam) -> ResponseModel:
    payment = await payment_service.create(
        amount=obj.amount, currency=obj.currency, user_id=getattr(request.user, "id", None)
    )
    return response_base.success(request=request, data=GetPaymentDetails(**select_as_dict(payment)))


@router.get(
    "/",
    summary="List payments (paginated, filterable)",
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def list_payments(
    request: Request,
    db: CurrentSession,
    status: Annotated[str | None, Query()] = None,
    user_id: Annotated[int | None, Query()] = None,
) -> ResponseModel:
    stmt = await payment_service.get_select(status=status, user_id=user_id)
    page = await paging_data(db, stmt, GetPaymentDetails)
    return response_base.success(request=request, data=page)


@router.get("/{pk}", summary="Get a payment", dependencies=[DependsJwtAuth])
async def get_payment(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    payment = await payment_service.get_by_id(pk=pk)
    return response_base.success(request=request, data=GetPaymentDetails(**select_as_dict(payment)))


@router.post("/{pk}/confirm", summary="Mark a payment succeeded", dependencies=[DependsJwtAuth])
async def confirm_payment(request: Request, pk: Annotated[int, Path(...)]) -> ResponseModel:
    payment = await payment_service.set_status(pk=pk, status="succeeded")
    return response_base.success(request=request, data=GetPaymentDetails(**select_as_dict(payment)))
