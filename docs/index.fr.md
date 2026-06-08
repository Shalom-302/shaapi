---
title: shaapi
hide:
  - navigation
---

# shaapi

**Générez des backends FastAPI épurés et complets — comme `django-admin`, mais pour FastAPI.**

shaapi vous donne en quelques secondes un projet FastAPI propre et prêt pour la
production : SQLAlchemy async + Alembic, PostgreSQL, Redis, auth JWT, RBAC
Casbin, stockage de fichiers et un workflow Docker en une commande. Arrêtez de
câbler de l'infra — codez vos fonctionnalités.

<div class="grid cards" markdown>

-   :material-rocket-launch: **Démarrage immédiat**

    ---

    `pip install shaapi` → `shaapi create-project` → une API qui tourne en moins d'une minute.

-   :material-layers-triple: **Architecture propre**

    ---

    Models · schemas · CRUD · services · routers. Le même découpage que dans de
    vraies bases de code de production — parfait pour apprendre.

-   :material-docker: **Docker d'abord**

    ---

    Image slim multi-stage, hot-reload en dev, migrations en prod, un seul
    `docker-run.sh` pour tout piloter.

-   :material-school: **Apprendre en lisant**

    ---

    Un vrai backend bien organisé. Les étudiants apprennent FastAPI *façon
    production* en explorant un projet qui tourne vraiment.

</div>

## Démarrage rapide

```bash
pip install shaapi
shaapi create-project "mon api"
cd mon_api
./docker-run.sh up
```

→ API sur **http://localhost:8000** · Swagger sur **http://localhost:8000/admin/api/v1/docs**

## Ce qu'il y a dedans

- **FastAPI** (async) avec une architecture en couches
- **SQLAlchemy 2 + Alembic** — création auto en dev, migrations en prod
- **PostgreSQL + Redis** (cache & limitation de débit)
- **Auth JWT + RBAC Casbin** — utilisateurs, rôles, permissions
- **Stockage de fichiers** — MinIO / S3 / GCS
- **Docker** — image slim multi-stage construite avec [uv], hot-reload, `docker-run.sh`
- **Observabilité optionnelle** — Prometheus, Grafana, Tempo, Loki

Sur la stack la plus récente : **SQLAlchemy 2.0** · **Pydantic v2** · **FastAPI**.

## Par où continuer ?

<div class="grid cards" markdown>

-   [:material-flag-checkered: **Démarrage**](getting-started.md)

    Installer, créer un projet, le lancer.

-   [:material-school: **Apprendre FastAPI avec shaapi**](learn-fastapi.md)

    Comprendre l'architecture — et pourquoi elle passe à l'échelle.

-   [:material-sitemap: **Architecture**](architecture.md)

    Les couches, le lifespan, la configuration.

-   [:material-puzzle: **Créer une fonctionnalité**](create-a-feature.md)

    Une API Todo authentifiée complète, pas à pas.

-   [:material-docker: **Pourquoi Docker ?**](why-docker.md)

    Ce que ça apporte, et comment monter en charge.

-   [:material-cloud-upload: **Déployer**](deployment.md)

    Mettre en production sur un VPS avec TLS.

</div>

---

shaapi est open source (MIT) — [GitHub](https://github.com/Shalom-302/shaapi) ·
[PyPI](https://pypi.org/project/shaapi/)

[uv]: https://github.com/astral-sh/uv
