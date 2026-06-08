from typing import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.sql import Select

from backend.crud.crud_base import CRUDBase
from backend.database.db_postgres import async_db_session
from backend.plugins.user_analytics.models import AnalyticsEvent
from backend.plugins.user_analytics.schemas import CreateEventParam


class CRUDAnalytics(CRUDBase[AnalyticsEvent]):
    async def create(self, db, obj_in: CreateEventParam) -> AnalyticsEvent:
        return await self.create_model(db, obj_in)

    async def get_list(self, event_type: str | None = None, user_id: int | None = None) -> Select:
        stmt = select(self.model).order_by(desc(self.model.created_time))
        where = []
        if event_type:
            where.append(self.model.event_type == event_type)
        if user_id is not None:
            where.append(self.model.user_id == user_id)
        return stmt.where(*where) if where else stmt


analytics_dao: CRUDAnalytics = CRUDAnalytics(AnalyticsEvent)


class AnalyticsService:
    @staticmethod
    async def record(*, event_type: str, **kwargs) -> AnalyticsEvent:
        """Record an analytics event. Call from your own code or the API."""
        async with async_db_session.begin() as db:
            return await analytics_dao.create(db, CreateEventParam(event_type=event_type, **kwargs))

    @staticmethod
    async def get_select(*, event_type=None, user_id=None) -> Select:
        return await analytics_dao.get_list(event_type=event_type, user_id=user_id)

    @staticmethod
    async def stats() -> list[dict]:
        """Return event counts grouped by event_type, most frequent first."""
        async with async_db_session() as db:
            rows = (
                await db.execute(
                    select(AnalyticsEvent.event_type, func.count().label("count"))
                    .group_by(AnalyticsEvent.event_type)
                    .order_by(desc(func.count()))
                )
            ).all()
        return [{"event_type": r[0], "count": r[1]} for r in rows]


analytics_service = AnalyticsService()
