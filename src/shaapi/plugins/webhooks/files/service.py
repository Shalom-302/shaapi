import hashlib
import hmac
import json
from typing import Any, Sequence

import httpx

from backend.common.exception import errors
from backend.common.log import log
from backend.crud.crud_base import CRUDBase
from backend.database.db_postgres import async_db_session
from backend.plugins.webhooks.models import WebhookSubscription
from backend.plugins.webhooks.schemas import CreateWebhookParam, UpdateWebhookParam


class CRUDWebhook(CRUDBase[WebhookSubscription]):
    async def get(self, db, pk: int) -> WebhookSubscription | None:
        return await self.select_model(db, pk)

    async def list_all(self, db) -> Sequence[WebhookSubscription]:
        return await self.select_models(db)

    async def list_for_event(self, db, event: str) -> Sequence[WebhookSubscription]:
        return await self.select_models(db, event=event, is_enabled=True)

    async def create(self, db, obj_in: CreateWebhookParam) -> WebhookSubscription:
        return await self.create_model(db, obj_in)

    async def update(self, db, pk: int, obj_in: UpdateWebhookParam) -> int:
        return await self.update_model(db, pk, obj_in.model_dump(exclude_unset=True))

    async def delete(self, db, pk: int) -> int:
        return await self.delete_model(db, pk)


webhook_dao: CRUDWebhook = CRUDWebhook(WebhookSubscription)


class WebhookService:
    @staticmethod
    async def create(*, obj: CreateWebhookParam) -> WebhookSubscription:
        async with async_db_session.begin() as db:
            return await webhook_dao.create(db, obj)

    @staticmethod
    async def get_all() -> Sequence[WebhookSubscription]:
        async with async_db_session() as db:
            return await webhook_dao.list_all(db)

    @staticmethod
    async def get_by_id(*, pk: int) -> WebhookSubscription:
        async with async_db_session() as db:
            wh = await webhook_dao.get(db, pk)
            if not wh:
                raise errors.NotFoundError(msg="Webhook not found")
            return wh

    @staticmethod
    async def update(*, pk: int, obj: UpdateWebhookParam) -> int:
        async with async_db_session.begin() as db:
            if not await webhook_dao.get(db, pk):
                raise errors.NotFoundError(msg="Webhook not found")
            return await webhook_dao.update(db, pk, obj)

    @staticmethod
    async def delete(*, pk: int) -> int:
        async with async_db_session.begin() as db:
            if not await webhook_dao.get(db, pk):
                raise errors.NotFoundError(msg="Webhook not found")
            return await webhook_dao.delete(db, pk)

    @staticmethod
    async def emit(event: str, payload: dict[str, Any]) -> int:
        """Deliver an event to every enabled subscription for it.

        Returns the number of subscriptions notified. Call this from your own
        services, e.g. `await webhook_service.emit("order.placed", {...})`.
        """
        async with async_db_session() as db:
            subs = await webhook_dao.list_for_event(db, event)
        if not subs:
            return 0
        body = json.dumps({"event": event, "data": payload}, separators=(",", ":"))
        async with httpx.AsyncClient(timeout=10) as client:
            for sub in subs:
                headers = {"Content-Type": "application/json", "X-Webhook-Event": event}
                if sub.secret:
                    headers["X-Webhook-Signature"] = hmac.new(
                        sub.secret.encode(), body.encode(), hashlib.sha256
                    ).hexdigest()
                try:
                    await client.post(sub.url, content=body, headers=headers)
                except Exception as exc:  # noqa: BLE001
                    log.warning("Webhook delivery to %s failed: %s", sub.url, exc)
        return len(subs)


webhook_service = WebhookService()
