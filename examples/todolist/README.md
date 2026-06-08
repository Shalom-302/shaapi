# Example: a Todo API with auth (admin + user)

This example shows how little it takes to build a real, authenticated feature on
top of a shaapi project: a per-user todo list with ownership rules and an
admin-only "see everything" endpoint.

*Cet exemple montre à quel point il est simple de bâtir une vraie fonctionnalité
authentifiée sur shaapi : une todolist par utilisateur, avec règles de propriété
et un endpoint réservé aux admins.*

---

## What it demonstrates / Ce que ça démontre

- **JWT auth** — register / login, protected routes (`DependsJwtAuth`)
- **Per-user data** — each user only sees and edits their own todos
- **Ownership enforcement** — accessing someone else's todo returns `403`
- **Role-based access** — only users with the `admin` role can `GET /todo/all`

All of it on **FastAPI + async SQLAlchemy + Pydantic v2**, with zero extra
plumbing — shaapi already provides the auth, DB session, RBAC and response layer.

## The whole feature = 5 files + 1 line

```
backend/
├── models/todo.py                      # SQLAlchemy model
├── app/admin/schema/todo.py            # Pydantic schemas
├── crud/crud_todo.py                   # data access (CRUDBase)
├── app/admin/service/todo_service.py   # business logic
└── app/admin/api/v1/todo.py            # router (auto-discovered)
```

The router is **auto-discovered** — dropping `todo.py` into `app/admin/api/v1/`
is enough to expose its endpoints. No central registry to edit.

## Install into a shaapi project / Installer dans un projet shaapi

```bash
# 1. Create a project
pip install shaapi
shaapi create-project "todoapp"

# 2. Copy this feature on top of it
cp -r examples/todolist/backend/. todoapp/backend/

# 3. Register the model (one line) in todoapp/backend/models/__init__.py
#    from backend.models.todo import Todo

# 4. Run
cd todoapp
./docker-run.sh up
```

In development the table is auto-created on startup. For production, generate a
migration: `./docker-run.sh makemigrations "add todo table"`.

## Endpoints

| Method | Path                         | Who            | Description                 |
|--------|------------------------------|----------------|-----------------------------|
| POST   | `/admin/api/v1/auth/register`| public         | Create an account           |
| POST   | `/admin/api/v1/auth/login`   | public         | Get an access token         |
| POST   | `/admin/api/v1/todo/`        | any user       | Create a todo               |
| GET    | `/admin/api/v1/todo/`        | any user       | List **my** todos (paged)   |
| GET    | `/admin/api/v1/todo/{id}`    | owner/admin    | Get one todo                |
| PUT    | `/admin/api/v1/todo/{id}`    | owner/admin    | Update a todo               |
| DELETE | `/admin/api/v1/todo/{id}`    | owner/admin    | Delete a todo               |
| GET    | `/admin/api/v1/todo/all`     | **admin only** | List every user's todos     |

Authenticated calls send `Authorization: Bearer <access_token>`.

## Make a user an admin / Donner le rôle admin

```sql
INSERT INTO role (x_id, name, status, remark, created_time)
VALUES ('admin0000000000000000000001', 'admin', 1, '', now());
INSERT INTO user_role (user_id, role_id)
SELECT <USER_ID>, id FROM role WHERE name = 'admin';
```

## Reproduce the proof / Reproduire la preuve

With the stack running, from the repo root:

```bash
python examples/todolist/smoke_test.py
```

Expected output: registration, per-user CRUD, a `403` when a user touches
another user's todo, a `403` on `/todo/all` for a normal user, and `200` once
the user is granted the `admin` role.
