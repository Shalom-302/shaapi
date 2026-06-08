from fastapi import Request

from fastapi import APIRouter

from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.plugins.advanced_auth.schemas import MfaCodeParam, MfaSetupResult, MfaStatus
from backend.plugins.advanced_auth.service import mfa_service

router = APIRouter(prefix="/auth/mfa", tags=["MFA"])


@router.post("/setup", summary="Start MFA setup (returns a TOTP secret)", dependencies=[DependsJwtAuth])
async def mfa_setup(request: Request) -> ResponseModel:
    account = getattr(request.user, "email", None) or str(request.user.id)
    secret, uri = await mfa_service.setup(user_id=request.user.id, account=account)
    return response_base.success(request=request, data=MfaSetupResult(secret=secret, otpauth_uri=uri))


@router.post("/enable", summary="Confirm and enable MFA", dependencies=[DependsJwtAuth])
async def mfa_enable(request: Request, obj: MfaCodeParam) -> ResponseModel:
    await mfa_service.enable(user_id=request.user.id, code=obj.code)
    return response_base.success(request=request)


@router.post("/verify", summary="Verify a TOTP code", dependencies=[DependsJwtAuth])
async def mfa_verify(request: Request, obj: MfaCodeParam) -> ResponseModel:
    valid = await mfa_service.verify(user_id=request.user.id, code=obj.code)
    return response_base.success(request=request, data={"valid": valid})


@router.post("/disable", summary="Disable MFA", dependencies=[DependsJwtAuth])
async def mfa_disable(request: Request) -> ResponseModel:
    await mfa_service.disable(user_id=request.user.id)
    return response_base.success(request=request)


@router.get("/status", summary="Is MFA enabled?", dependencies=[DependsJwtAuth])
async def mfa_status(request: Request) -> ResponseModel:
    enabled = await mfa_service.status(user_id=request.user.id)
    return response_base.success(request=request, data=MfaStatus(enabled=enabled))
