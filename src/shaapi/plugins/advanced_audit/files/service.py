from typing import Sequence

from sqlalchemy import desc, select
from sqlalchemy.sql import Select

from backend.common.exception import errors
from backend.crud.crud_base import CRUDBase
from backend.database.db_postgres import async_db_session
from backend.plugins.advanced_audit.models import AuditLog
from backend.plugins.advanced_audit.schemas import CreateAuditLogParam


class CRUDAuditLog(CRUDBase[AuditLog]):
    async def get(self, db, pk: int) -> AuditLog | None:
        return await self.select_model(db, pk)

    async def get_list(
        self, action: str | None = None, resource: str | None = None, user_id: int | None = None
    ) -> Select:
        stmt = select(self.model).order_by(desc(self.model.created_time))
        where = []
        if action:
            where.append(self.model.action == action)
        if resource:
            where.append(self.model.resource == resource)
        if user_id is not None:
            where.append(self.model.user_id == user_id)
        return stmt.where(*where) if where else stmt

    async def create(self, db, obj_in: CreateAuditLogParam) -> AuditLog:
        return await self.create_model(db, obj_in)

    async def delete(self, db, pk: int) -> int:
        return await self.delete_model(db, pk)


audit_dao: CRUDAuditLog = CRUDAuditLog(AuditLog)


class AuditService:
    @staticmethod
    async def record(
        *, action: str, resource: str, user_id: int | None = None, details: str | None = None
    ) -> AuditLog:
        """Record an audit event. Call this from your own services."""
        async with async_db_session.begin() as db:
            return await audit_dao.create(
                db,
                CreateAuditLogParam(action=action, resource=resource, user_id=user_id, details=details),
            )

    @staticmethod
    async def get_select(*, action=None, resource=None, user_id=None) -> Select:
        return await audit_dao.get_list(action=action, resource=resource, user_id=user_id)

    @staticmethod
    async def get_by_id(*, pk: int) -> AuditLog:
        async with async_db_session() as db:
            log = await audit_dao.get(db, pk)
            if not log:
                raise errors.NotFoundError(msg="Audit log not found")
            return log

    @staticmethod
    async def delete(*, pk: int) -> int:
        async with async_db_session.begin() as db:
            if not await audit_dao.get(db, pk):
                raise errors.NotFoundError(msg="Audit log not found")
            return await audit_dao.delete(db, pk)


audit_service = AuditService()
