# Apprendre FastAPI avec shaapi

FastAPI est un *framework web* fantastique — mais un framework n'est pas une
*application*. Dès qu'on démarre un vrai projet, on tombe sur des questions
auxquelles FastAPI ne répond pas à votre place :

- Où mettre le code base de données ? La logique métier ? La validation ?
- Comment structurer l'auth, les permissions, la config, les migrations ?
- Comment garder tout ça organisé quand le projet atteint 50+ endpoints ?

C'est le vide que shaapi comble. Voyez-le comme un **pré-framework** : une couche
opiniâtre et complète *par-dessus* FastAPI, qui répond à ces questions avec des
patterns éprouvés en production — tout en restant 100 % du FastAPI standard en
dessous.

Si vous apprenez FastAPI, lire un projet shaapi vous montre comment les vrais
backends sont réellement organisés.

## L'idée centrale : la séparation des responsabilités

Une app FastAPI naïve met tout dans un seul fichier : routing, validation, SQL,
règles métier. Ça marche pour une démo et s'effondre pour un vrai produit. shaapi
découpe les responsabilités en **couches**, chacune avec un seul rôle :

```
   Requête HTTP
        │
        ▼
┌──────────────┐   « Quelle URL ? Quelle forme HTTP ? »  api/v1/*.py  (router)
│   Router     │   Valide l'entrée, renvoie un ResponseModel
└──────┬───────┘
       ▼
┌──────────────┐   « Quelles règles métier ? »           service/*.py (service)
│   Service    │   Transactions, autorisation, orchestration
└──────┬───────┘
       ▼
┌──────────────┐   « Comment lire/écrire les données ? »  crud/*.py    (CRUD)
│    CRUD      │   Requêtes, basé sur sqlalchemy-crud-plus
└──────┬───────┘
       ▼
┌──────────────┐   « Qu'est-ce que la donnée ? »          models/*.py  (model)
│    Model     │   Tables SQLAlchemy
└──────────────┘

   Les schémas Pydantic (schema/*.py) valident ce qui franchit la frontière HTTP.
```

Pourquoi c'est important :

- **Chaque couche se teste isolément** — on teste un service sans passer par HTTP.
- **On change une couche sans casser les autres** — on remplace la requête, le router ne bouge pas.
- **Les nouveaux arrivants s'y retrouvent tout de suite** — chaque feature se ressemble.

## Une requête, de bout en bout

Prenons `POST /admin/api/v1/todo/` du [tutoriel Todo](create-a-feature.md) :

1. **Router** (`api/v1/todo.py`) — FastAPI matche l'URL, exécute la dépendance
   `DependsJwtAuth` (authentifie l'utilisateur via le JWT), et valide le corps
   contre le **schéma** `CreateTodoParam`.
2. **Service** (`service/todo_service.py`) — ouvre une transaction
   (`async with async_db_session.begin()`), applique les règles (le propriétaire
   du todo = l'utilisateur courant) et appelle la couche CRUD.
3. **CRUD** (`crud/crud_todo.py`) — transforme l'intention en SQL via
   `sqlalchemy-crud-plus` et persiste le **model**.
4. Le router sérialise le résultat via le **schéma** `GetTodoDetails` et renvoie
   un `ResponseModel` unifié.

Rien de magique ici — c'est du FastAPI + SQLAlchemy classique. shaapi donne juste
une place à chaque pièce.

## Les concepts que shaapi enseigne

### Les schémas Pydantic = votre contrat
Les schémas (`app/admin/schema/`) définissent exactement ce qui entre et sort.
FastAPI les utilise pour valider les requêtes, générer la doc OpenAPI et
sérialiser les réponses. Séparer *schémas* (contrat d'API) et *models* (base de
données) est un réflexe professionnel clé — les deux évoluent indépendamment.

### L'injection de dépendances
`dependencies=[DependsJwtAuth]` sur une route, c'est l'injection de dépendances
de FastAPI : une logique transversale réutilisable et déclarative (auth,
pagination, sessions DB). shaapi montre une DI idiomatique — `CurrentSession`,
`DependsPagination`, `DependsJwtAuth`.

### L'async de bout en bout
Routers, services et CRUD sont `async`. Le driver (`asyncpg`) et le moteur async
de SQLAlchemy permettent de gérer de nombreuses requêtes concurrentes sur un
seul worker. shaapi câble correctement le cycle de vie de la session async.

### La configuration comme du code
`core/conf.py` (pydantic-settings) centralise chaque réglage avec des défauts
sûrs et des surcharges via `.env`. Fini les `os.getenv` éparpillés.

### Les migrations, pas l'à-peu-près
Le schéma de votre base est versionné avec Alembic. En dev, les tables se créent
automatiquement pour la vitesse ; en prod, les migrations rendent les
changements explicites et réversibles.

## shaapi, un « pré-framework »

| Ce que FastAPI fournit | Ce que shaapi ajoute par-dessus |
|---|---|
| Routing, validation, OpenAPI | Une place pour routers, schémas, services, CRUD |
| Injection de dépendances | Des deps prêtes : auth, pagination, session DB |
| Une app ASGI | Factory d'app, lifespan, pile de middlewares |
| (rien sur la persistance) | SQLAlchemy + Alembic + Redis câblés |
| (rien sur l'auth) | JWT + RBAC Casbin, utilisateurs, rôles |
| (rien sur l'ops) | Docker, migrations, logging, observabilité |

Vous gardez toute la flexibilité de FastAPI — shaapi est une *structure
additive*, pas une cage. Tout tutoriel FastAPI que vous lisez reste valable.

## Est-ce que ça passe à l'échelle ?

Oui — c'est tout l'intérêt de la structure. Quand l'app grandit :

- **Plus de features** → plus de fichiers sous `app/admin/api/v1/`
  (auto-découverts), chacun avec son model/schema/crud/service. Le pattern se
  répète ; le projet reste lisible à 10 comme à 200 endpoints.
- **Plus de sous-apps** → montez d'autres sous-applications à côté de `/admin`
  (ex. `/client`, `/partner`) pour des frontières de domaine claires.
- **Plus de charge** → plusieurs workers API, Postgres/Redis managés, Celery pour
  les tâches de fond, observabilité activée. Le setup Docker est fait pour
  grandir (voir [Pourquoi Docker ?](why-docker.md)).

Commencez par lire l'[Architecture](architecture.md), puis construisez votre
première feature avec le [tutoriel Todo](create-a-feature.md).
