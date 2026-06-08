# Learn FastAPI with shaapi

FastAPI is a fantastic *web framework* — but a framework is not an *application*.
When you start a real project you immediately face questions FastAPI doesn't
answer for you:

- Where do I put my database code? My business logic? My validation?
- How do I structure auth, permissions, configuration, migrations?
- How do I keep it all organized when the project grows to 50+ endpoints?

This is the gap shaapi fills. Think of it as a **pre-framework**: an opinionated,
batteries-included layer *on top of* FastAPI that answers those questions with
production-proven patterns — while staying 100% standard FastAPI underneath.

If you're learning FastAPI, reading a shaapi project teaches you how serious
backends are actually organized.

## The core idea: separation of concerns

A naive FastAPI app puts everything in one file: routing, validation, SQL,
business rules. That works for a demo and collapses for a real product. shaapi
splits responsibilities into **layers**, each with exactly one job:

```
   HTTP request
        │
        ▼
┌──────────────┐   "What URL? What HTTP shape?"      api/v1/*.py   (router)
│   Router     │   Validates input, returns ResponseModel
└──────┬───────┘
       ▼
┌──────────────┐   "What are the business rules?"    service/*.py  (service)
│   Service    │   Transactions, authorization, orchestration
└──────┬───────┘
       ▼
┌──────────────┐   "How do I read/write the data?"   crud/*.py     (CRUD)
│    CRUD      │   Queries, built on sqlalchemy-crud-plus
└──────┬───────┘
       ▼
┌──────────────┐   "What is the data?"               models/*.py   (model)
│    Model     │   SQLAlchemy tables
└──────────────┘

   Pydantic schemas (schema/*.py) validate what crosses the HTTP boundary.
```

Why this matters:

- **Each layer is testable in isolation** — you can unit-test a service without HTTP.
- **Change one layer without breaking others** — swap the DB query, the router stays.
- **New developers find their way instantly** — every feature looks the same.

## A request, end to end

Take `POST /admin/api/v1/todo/` from the [Todo tutorial](create-a-feature.md):

1. **Router** (`api/v1/todo.py`) — FastAPI matches the URL, runs the
   `DependsJwtAuth` dependency (authenticates the user from the JWT), and
   validates the body against the `CreateTodoParam` **schema**.
2. **Service** (`service/todo_service.py`) — opens a transaction
   (`async with async_db_session.begin()`), applies rules (the todo's owner is
   the current user), and calls the CRUD layer.
3. **CRUD** (`crud/crud_todo.py`) — turns intent into SQL via
   `sqlalchemy-crud-plus` and persists the **model**.
4. The router serializes the result through the `GetTodoDetails` **schema** and
   returns a unified `ResponseModel`.

Nothing here is magic — it's plain FastAPI + SQLAlchemy. shaapi just gives the
pieces a home.

## The concepts shaapi teaches

### Pydantic schemas = your contract
Schemas (`app/admin/schema/`) define exactly what comes in and goes out. FastAPI
uses them to validate requests, generate the OpenAPI docs, and serialize
responses. Separating *schemas* (the API contract) from *models* (the database)
is a key professional habit — the two evolve independently.

### Dependency injection
`dependencies=[DependsJwtAuth]` on a route is FastAPI's dependency injection:
reusable, declarative cross-cutting logic (auth, pagination, DB sessions). shaapi
shows you idiomatic DI — `CurrentSession`, `DependsPagination`, `DependsJwtAuth`.

### Async all the way
Routers, services and CRUD are `async`. The database driver (`asyncpg`) and
SQLAlchemy's async engine let the server handle many concurrent requests on a
single worker. shaapi wires the async session lifecycle correctly so you don't
have to.

### Configuration as code
`core/conf.py` (pydantic-settings) centralizes every setting with safe defaults
and `.env` overrides. No scattered `os.getenv` calls.

### Migrations, not guesswork
Your database schema is versioned with Alembic. In dev, tables auto-create for
speed; in prod, migrations make changes explicit and reversible.

## shaapi as a "pre-framework"

| FastAPI gives you | shaapi adds on top |
|---|---|
| Routing, validation, OpenAPI | A place for routers, schemas, services, CRUD |
| Dependency injection | Ready-made deps: auth, pagination, DB session |
| ASGI app | App factory, lifespan, middleware stack |
| (nothing about persistence) | SQLAlchemy + Alembic + Redis wired in |
| (nothing about auth) | JWT + Casbin RBAC, users, roles |
| (nothing about ops) | Docker, migrations, logging, observability |

You keep all of FastAPI's flexibility — shaapi is *additive structure*, not a
walled garden. Any FastAPI tutorial you read still applies.

## Does it scale to big projects?

Yes — that's the point of the structure. As your app grows:

- **More features** → more files under `app/admin/api/v1/` (auto-discovered),
  each with its model/schema/crud/service. The pattern repeats; the project
  stays navigable at 10 or 200 endpoints.
- **More sub-apps** → mount additional sub-applications next to `/admin` (e.g.
  `/client`, `/partner`) for clear domain boundaries.
- **More load** → run multiple API workers, move Postgres/Redis to managed
  services, add Celery for background jobs, turn on observability. The
  Docker setup is built to grow (see [Why Docker?](why-docker.md)).

Start by reading [Architecture](architecture.md), then build your first feature
with the [Todo tutorial](create-a-feature.md).
