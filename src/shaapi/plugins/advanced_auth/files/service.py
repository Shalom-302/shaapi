import pyotp
from sqlalchemy import select

from backend.common.exception import errors
from backend.database.db_postgres import async_db_session
from backend.plugins.advanced_auth.models import AuthMfa

ISSUER = "shaapi"


class MfaService:
    @staticmethod
    async def _get(db, user_id: int) -> AuthMfa | None:
        return (
            await db.execute(select(AuthMfa).where(AuthMfa.user_id == user_id))
        ).scalar_one_or_none()

    @staticmethod
    async def setup(*, user_id: int, account: str) -> tuple[str, str]:
        """Generate (or regenerate) a TOTP secret and return its otpauth URI.

        The secret is stored disabled until confirmed via `enable`.
        """
        async with async_db_session.begin() as db:
            mfa = await MfaService._get(db, user_id)
            if mfa and mfa.is_enabled:
                raise errors.ForbiddenError(msg="MFA is already enabled")
            secret = pyotp.random_base32()
            if mfa:
                mfa.secret = secret
                mfa.is_enabled = False
            else:
                db.add(AuthMfa(user_id=user_id, secret=secret))
            uri = pyotp.TOTP(secret).provisioning_uri(name=account, issuer_name=ISSUER)
            return secret, uri

    @staticmethod
    async def enable(*, user_id: int, code: str) -> None:
        """Confirm setup: enable MFA if the code matches the pending secret."""
        async with async_db_session.begin() as db:
            mfa = await MfaService._get(db, user_id)
            if not mfa:
                raise errors.NotFoundError(msg="Start with MFA setup first")
            if not pyotp.TOTP(mfa.secret).verify(code, valid_window=1):
                raise errors.AuthorizationError(msg="Invalid MFA code")
            mfa.is_enabled = True

    @staticmethod
    async def verify(*, user_id: int, code: str) -> bool:
        """Check a TOTP code for an enabled user (use for login step-up)."""
        async with async_db_session() as db:
            mfa = await MfaService._get(db, user_id)
        if not mfa or not mfa.is_enabled:
            return False
        return pyotp.TOTP(mfa.secret).verify(code, valid_window=1)

    @staticmethod
    async def disable(*, user_id: int) -> None:
        async with async_db_session.begin() as db:
            mfa = await MfaService._get(db, user_id)
            if mfa:
                await db.delete(mfa)

    @staticmethod
    async def status(*, user_id: int) -> bool:
        async with async_db_session() as db:
            mfa = await MfaService._get(db, user_id)
        return bool(mfa and mfa.is_enabled)


mfa_service = MfaService()
