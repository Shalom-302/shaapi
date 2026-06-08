from typing import Sequence

from sqlalchemy import desc, select
from sqlalchemy.sql import Select

from backend.common.exception import errors
from backend.common.log import log
from backend.crud.crud_base import CRUDBase
from backend.database.db_postgres import async_db_session
from backend.plugins.payment.models import Payment
from backend.plugins.payment.providers import get_provider


class CRUDPayment(CRUDBase[Payment]):
    async def get(self, db, pk: int) -> Payment | None:
        return await self.select_model(db, pk)

    async def get_list(self, status: str | None = None, user_id: int | None = None) -> Select:
        stmt = select(self.model).order_by(desc(self.model.created_time))
        where = []
        if status:
            where.append(self.model.status == status)
        if user_id is not None:
            where.append(self.model.user_id == user_id)
        return stmt.where(*where) if where else stmt


payment_dao: CRUDPayment = CRUDPayment(Payment)


class PaymentService:
    @staticmethod
    async def create(*, amount: int, currency: str, user_id: int | None, provider: str = "stripe") -> Payment:
        """Record a payment. If the provider is configured (e.g. STRIPE_SECRET_KEY),
        a remote payment intent is created; otherwise it stays 'pending' so the
        flow can be built before adding credentials.
        """
        prov = get_provider(provider)
        async with async_db_session.begin() as db:
            payment = Payment(amount=amount, currency=currency, provider=provider, user_id=user_id)
            db.add(payment)
            await db.flush()
            if prov.configured():
                try:
                    res = await prov.create_intent(amount, currency)
                    payment.reference = res["reference"]
                    payment.meta = {"client_secret": res.get("client_secret")}
                except Exception as exc:  # noqa: BLE001
                    log.warning("Payment provider error: %s", exc)
                    payment.status = "failed"
                    payment.meta = {"error": str(exc)}
            else:
                payment.meta = {"note": "provider not configured; recorded as pending"}
            return payment

    @staticmethod
    async def get_select(*, status=None, user_id=None) -> Select:
        return await payment_dao.get_list(status=status, user_id=user_id)

    @staticmethod
    async def get_by_id(*, pk: int) -> Payment:
        async with async_db_session() as db:
            p = await payment_dao.get(db, pk)
            if not p:
                raise errors.NotFoundError(msg="Payment not found")
            return p

    @staticmethod
    async def set_status(*, pk: int, status: str) -> Payment:
        """Mark a payment status (call this from your provider webhook handler)."""
        async with async_db_session.begin() as db:
            p = await payment_dao.get(db, pk)
            if not p:
                raise errors.NotFoundError(msg="Payment not found")
            p.status = status
            return p


payment_service = PaymentService()
