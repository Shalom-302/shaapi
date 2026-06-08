# Démarrage rapide

## Qu'est-ce que shaapi ?

`shaapi` est un CLI qui génère en quelques secondes un **backend FastAPI épuré et
prêt pour la production** — comme `django-admin startproject` pour Django. Vous
obtenez un projet propre et structuré en couches, avec auth, base de données,
migrations, RBAC, stockage de fichiers et un workflow Docker en une commande.
Vous codez vos fonctionnalités au lieu de câbler de l'infrastructure.

## Prérequis

- Python ≥ 3.11
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose (pour le
  workflow en une commande)

## Installation

```bash
pip install shaapi
```

## Créer un projet

```bash
shaapi create-project "mon api"
```

Quelques questions vous sont posées :

```
shaapi creating project mon_api
? Include monitoring (Prometheus/Grafana/Tempo/Loki)?  No
? Initialize a git repository?                          Yes
```

Pour ignorer les questions avec `-y`, ou tout préciser :

```bash
shaapi create-project "mon api" -y                 # valeurs par défaut
shaapi create-project "mon api" --monitoring --no-git
shaapi create-project "mon api" --path ./projets
```

Le nom du projet est transformé en *slug* sûr (`mon api` → `mon_api`), utilisé
pour le dossier, les conteneurs Docker, la base de données et le titre de l'app.

## Lancer

```bash
cd mon_api
./docker-run.sh up
```

L'image de l'API est construite et tout démarre (API, Postgres, Redis, MinIO) :

- API → http://localhost:8000
- Santé → http://localhost:8000/health
- Swagger → http://localhost:8000/admin/api/v1/docs
- ReDoc → http://localhost:8000/admin/api/v1/redocs

En développement, le code source est **monté en volume avec hot-reload** :
modifiez votre code, le serveur recharge instantanément, sans rebuild.

## Commandes du quotidien

```bash
./docker-run.sh up                    # démarrer (build si besoin)
./docker-run.sh up --monitoring       # + Prometheus/Grafana/Tempo/Loki
./docker-run.sh logs                  # suivre tous les logs
./docker-run.sh api-logs              # suivre les logs de l'API
./docker-run.sh restart-api           # redémarrer seulement l'API
./docker-run.sh shell                 # shell dans le conteneur API
./docker-run.sh db                    # psql dans Postgres
./docker-run.sh migrate               # alembic upgrade head
./docker-run.sh makemigrations "msg"  # générer une migration
./docker-run.sh down                  # tout arrêter
```

## Configuration

Tout se configure via `.env` (créé automatiquement depuis `.env.template` au
premier lancement). Chaque valeur a un défaut raisonnable dans
`backend/core/conf.py` : l'app démarre sans configuration, vous ne surchargez
que ce qui change. **Changez les secrets avant la production.**

## Étapes suivantes

- [Architecture](architecture.md) — comment le projet est organisé
- [Créer une fonctionnalité](creer-une-fonctionnalite.md) — une API Todo en minutes
- [Déploiement](deploiement.md) — passer en production
