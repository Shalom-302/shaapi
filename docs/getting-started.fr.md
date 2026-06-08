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
shaapi new "mon api"
```

Quelques questions vous sont posées :

```
shaapi creating project mon_api
? Include monitoring (Prometheus/Grafana/Tempo/Loki)?  No
? Initialize a git repository?                          Yes
```

Pour ignorer les questions avec `-y`, ou tout préciser :

```bash
shaapi new "mon api" -y                 # valeurs par défaut
shaapi new "mon api" --monitoring --no-git
shaapi new "mon api" --path ./projets
```

Le nom du projet est transformé en *slug* sûr (`mon api` → `mon_api`), utilisé
pour le dossier, les conteneurs Docker, la base de données et le titre de l'app.

## Lancer

```bash
cd mon_api
shaapi up                # build + démarrage de toute la stack (multiplateforme, sans bash)
```

> `shaapi` pilote directement `docker compose` : les mêmes commandes marchent sur
> **Windows, macOS et Linux**. Sous Unix, vous pouvez aussi utiliser le script
> shell fourni `./docker-run.sh` — il pilote la même stack.

L'image de l'API est construite et tout démarre (API, Postgres, Redis, MinIO) :

- API → http://localhost:8000
- Santé → http://localhost:8000/health
- Swagger → http://localhost:8000/admin/api/v1/docs
- ReDoc → http://localhost:8000/admin/api/v1/redocs

En développement, le code source est **monté en volume avec hot-reload** :
modifiez votre code, le serveur recharge instantanément, sans rebuild.

Une fois la stack démarrée, créez un compte admin (pour vous connecter à Swagger)
et le bucket de stockage :

```bash
shaapi auth init         # interactif : email + mot de passe
shaapi storage init      # crée le bucket MinIO/S3
```

## Commandes du quotidien

```bash
shaapi up                          # démarrer (build si besoin)
shaapi up --monitoring             # + Prometheus/Grafana/Tempo/Loki
shaapi logs                        # suivre tous les logs
shaapi logs api                    # suivre les logs de l'API
shaapi restart api                 # redémarrer seulement l'API
shaapi shell                       # shell dans le conteneur API
shaapi db shell                    # psql dans Postgres
shaapi db apply                    # alembic upgrade head
shaapi db generate --message "msg" # générer une migration
shaapi down                        # tout arrêter
```

Voilà l'essentiel — consultez la **[référence CLI](cli-reference.md)** pour
toutes les commandes, options et les équivalents `docker-run.sh`.

## Configuration

Tout se configure via `.env` (créé automatiquement depuis `.env.template` au
premier lancement). Chaque valeur a un défaut raisonnable dans
`backend/core/conf.py` : l'app démarre sans configuration, vous ne surchargez
que ce qui change. **Changez les secrets avant la production.**

## Étapes suivantes

- [Référence CLI](cli-reference.md) — toutes les commandes et options
- [Architecture](architecture.md) — comment le projet est organisé
- [Créer une fonctionnalité](create-a-feature.md) — une API Todo en minutes
- [Déploiement](deployment.md) — passer en production
