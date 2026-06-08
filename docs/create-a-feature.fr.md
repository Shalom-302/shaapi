# Créer une fonctionnalité — une API Todo

Ajoutons une vraie fonctionnalité authentifiée : une **todolist par utilisateur**
avec règles de propriété et un endpoint réservé aux admins. C'est 5 petits
fichiers et une ligne — shaapi s'occupe de l'auth, de la BDD et des réponses.

> Le code complet est dans [`examples/todolist`](https://github.com/Shalom-302/shaapi/tree/main/examples/todolist).

## 1. Le modèle — `backend/models/todo.py`

```python
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from backend.common.model import Base, get_id, id_key


class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[id_key] = mapped_column(init=False)
    x_id: Mapped[str] = mapped_column(sa.String(32), init=False, unique=True, default=get_id)
    title: Mapped[str] = mapped_column(sa.String(200))
    owner_id: Mapped[int] = mapped_column(sa.ForeignKey("user.id", ondelete="CASCADE"), index=True)
    description: Mapped[str | None] = mapped_column(sa.Text, default=None)
    completed: Mapped[bool] = mapped_column(sa.Boolean, default=False)
```

Enregistrez-le dans `backend/models/__init__.py` :

```python
from backend.models.todo import Todo
```

## 2. Les schémas — `backend/app/admin/schema/todo.py`

```python
from datetime import datetime
from pydantic import ConfigDict, Field
from backend.common.schema import SchemaBase


class CreateTodoParam(SchemaBase):
    title: str = Field(..., max_length=200)
    description: str | None = None


class UpdateTodoParam(SchemaBase):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    completed: bool | None = None


class GetTodoDetails(SchemaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    x_id: str
    title: str
    description: str | None = None
    owner_id: int
    completed: bool
    created_time: datetime
```

## 3. Accès aux données — `backend/crud/crud_todo.py`

```python
from sqlalchemy import desc, select
from backend.crud.crud_base import CRUDBase
from backend.models.todo import Todo
from backend.app.admin.schema.todo import CreateTodoParam, UpdateTodoParam


class CRUDTodo(CRUDBase[Todo]):
    async def get(self, db, pk: int):
        return await self.select_model(db, pk)

    async def get_list(self, owner_id=None, completed=None):
        stmt = select(self.model).order_by(desc(self.model.created_time))
        where = []
        if owner_id is not None:
            where.append(self.model.owner_id == owner_id)
        if completed is not None:
            where.append(self.model.completed == completed)
        return stmt.where(*where) if where else stmt

    async def create(self, db, obj_in: CreateTodoParam, owner_id: int):
        return await self.create_model(db, obj_in, owner_id=owner_id)

    async def update(self, db, pk: int, obj_in: UpdateTodoParam):
        return await self.update_model(db, pk, obj_in.model_dump(exclude_unset=True))

    async def delete(self, db, pk: int):
        return await self.delete_model(db, pk)


todo_dao = CRUDTodo(Todo)
```

## 4. Logique métier — `backend/app/admin/service/todo_service.py`

Les transactions et la règle de propriété vivent ici :

```python
from backend.crud.crud_todo import todo_dao
from backend.common.exception import errors
from backend.database.db_postgres import async_db_session


class TodoService:
    @staticmethod
    async def create(*, owner_id, obj):
        async with async_db_session.begin() as db:
            return await todo_dao.create(db, obj, owner_id=owner_id)

    @staticmethod
    async def get_select(*, owner_id=None, completed=None):
        return await todo_dao.get_list(owner_id=owner_id, completed=completed)

    @staticmethod
    async def _owned(db, *, pk, owner_id, is_admin):
        todo = await todo_dao.get(db, pk)
        if not todo:
            raise errors.NotFoundError(msg="Todo introuvable")
        if not is_admin and todo.owner_id != owner_id:
            raise errors.ForbiddenError(msg="Ce todo ne vous appartient pas")
        return todo
    # get_by_id / update / delete réutilisent _owned — voir examples/todolist


todo_service = TodoService()
```

## 5. Le router — `backend/app/admin/api/v1/todo.py`

Définir un `router` suffit — shaapi le découvre automatiquement. `DependsJwtAuth`
protège la route ; `request.user` est l'utilisateur connecté.

```python
from fastapi import APIRouter, Request
from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.utils.serializers import select_as_dict
from backend.app.admin.schema.todo import CreateTodoParam, GetTodoDetails
from backend.app.admin.service.todo_service import todo_service

router = APIRouter(prefix="/todo", tags=["Todo"])


@router.post("/", summary="Créer un todo", dependencies=[DependsJwtAuth])
async def create_todo(request: Request, obj: CreateTodoParam) -> ResponseModel:
    todo = await todo_service.create(owner_id=request.user.id, obj=obj)
    return response_base.success(request=request, data=GetTodoDetails(**select_as_dict(todo)))
```

(Le router complet ajoute list/get/update/delete et un `/todo/all` réservé aux admins.)

## 6. Lancer & tester

```bash
./docker-run.sh up        # dev : la table est créée automatiquement au démarrage
```

Ouvrez Swagger sur `http://localhost:8000/admin/api/v1/docs`, créez un compte,
connectez-vous : les endpoints Todo sont là. Pour une preuve scriptée :

```bash
python examples/todolist/smoke_test.py
```

Il crée deux utilisateurs, des todos, vérifie qu'un utilisateur **ne peut pas**
lire le todo d'un autre (`403`), et que `/todo/all` est réservé aux admins.

## Passer en production

En production, mettez `DB_AUTO_CREATE=false` et générez une migration au lieu de
compter sur la création automatique :

```bash
./docker-run.sh makemigrations "ajout table todo"
```

Le fichier de migration arrive dans `backend/alembic/versions/` — versionnez-le.
Voir [Déploiement](deployment.md).
