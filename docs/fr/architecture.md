# Architecture

shaapi suit une architecture en couches propre, inspirée de
*fastapi-best-architecture*, réduite à un noyau épuré.

## Organisation du projet

```
mon_api/
├── docker-compose.yml            # stack de base (api, postgres, redis, minio)
├── docker-compose.override.yml   # dev : montage du code + hot-reload
├── docker-compose.monitoring.yml # observabilité optionnelle
├── docker-run.sh                 # wrapper d'orchestration
├── Dockerfile                    # image slim multi-stage (build avec uv)
├── pyproject.toml                # dépendances (uv)
├── .env / .env.template          # configuration
└── backend/
    ├── main.py                   # point d'entrée (app parent + lifespan)
    ├── core/
    │   ├── conf.py               # settings (pydantic-settings)
    │   ├── registrar.py          # factory : middleware, routers, lifespan
    │   └── path_conf.py
    ├── app/admin/                # la sous-application « admin »
    │   ├── api/v1/               # routers (auto-découverts)
    │   ├── schema/               # schémas Pydantic
    │   └── service/              # logique métier
    ├── models/                   # modèles SQLAlchemy
    ├── crud/                     # accès aux données (CRUDBase)
    ├── common/                   # sécurité, réponses, exceptions, stockage…
    ├── middleware/               # JWT, i18n, opera-log, state, trace…
    ├── database/                 # clients Postgres + Redis
    └── alembic/                  # migrations
```

## Les couches

Une requête traverse des couches claires, chacune avec une responsabilité :

```
HTTP → router (api/v1) → service → crud → model (BDD)
              │             │        │
           schéma        règles    accès
         validation      métier   données
```

- **models/** — modèles déclaratifs SQLAlchemy 2 (les tables).
- **schema/** — modèles Pydantic v2 pour valider requêtes/réponses.
- **crud/** — classes d'accès aux données héritant de `CRUDBase`
  (`sqlalchemy-crud-plus`) : `select_model`, `create_model`, `update_model`…
- **service/** — logique métier, transactions (`async_db_session.begin()`),
  contrôles d'autorisation.
- **api/v1/** — routers FastAPI renvoyant un `ResponseModel` unifié.

## Auto-découverte des routers

Tout fichier `*.py` dans `app/admin/api/v1/` qui définit un `router` est **chargé
automatiquement** (`backend/app/__init__.py`). On ajoute un fichier, on a des
endpoints — aucun registre central à éditer.

## L'app et son lifespan

`backend/main.py` construit une app FastAPI **parente** légère qui monte les
sous-apps (actuellement `/admin`). C'est le parent qui porte le **lifespan**
(création des tables en dev, ouverture de Redis, init du rate limiter), car
Starlette n'exécute pas le lifespan des sous-applications *montées*.

## Configuration

`core/conf.py` définit tous les réglages avec des défauts de dev sûrs : l'app
démarre avec un `.env` vide. On surcharge via variables d'environnement / `.env`.
Flags clés :

| Réglage                 | Défaut  | Signification                                       |
|-------------------------|---------|-----------------------------------------------------|
| `ENVIRONMENT`           | `dev`   | `dev` active le reload ; `prod` sert le code figé   |
| `DB_AUTO_CREATE`        | `true`  | Création auto des tables au démarrage (dev). Off en prod. |
| `OBSERVABILITY_ENABLED` | `false` | Prometheus/OpenTelemetry (optionnel)                |

## Base de données & migrations

- **Dev** : les tables sont créées automatiquement au démarrage
  (`DB_AUTO_CREATE=true`) pour un premier lancement sans friction.
- **Prod** : `DB_AUTO_CREATE=false` et migrations Alembic
  (`alembic upgrade head`, lancé automatiquement par l'entrypoint). On crée une
  migration avec `./docker-run.sh makemigrations "message"`.

Les migrations font foi et sont versionnées dans votre dépôt.

## Inclus d'office

- **Auth** : JWT (access + refresh), register/login, `DependsJwtAuth`.
- **RBAC** : politiques Casbin ; utilisateurs, rôles, permissions.
- **Stockage** : MinIO / S3 / GCS via une interface commune.
- **Observabilité** (optionnelle) : métriques Prometheus, traces OpenTelemetry,
  Grafana + Tempo + Loki.
- **Transversal** : identifiants de requête, journaux d'opérations et de
  connexion, i18n, rate limiting, réponses et gestion d'erreurs unifiées.

## Stack technique

FastAPI · SQLAlchemy 2 (async) · Pydantic v2 · Alembic · PostgreSQL · Redis ·
Casbin · MinIO · uv · Docker. Voir [Créer une fonctionnalité](creer-une-fonctionnalite.md).
