# Pourquoi Docker ?

shaapi est pensé Docker d'abord. Voici le *pourquoi* — utile que vous appreniez
ou que vous évaluiez l'outil pour un vrai projet.

## Le problème que Docker résout

Un backend, ce n'est pas que du Python. Il faut PostgreSQL, Redis, du stockage
objet, les bonnes bibliothèques système, la bonne version de Python… Sans Docker,
chaque développeur (et chaque serveur) doit tout installer et tout faire
correspondre à la main. D'où le classique *« ça marche sur ma machine »*.

Avec shaapi, toute la stack est décrite en code :

```bash
shaapi up
```

Une seule commande donne à **chaque** développeur — et à la production — la
*même* API, base de données, cache et stockage. L'onboarding d'un nouveau
contributeur passe d'une journée à une minute.

## Ce que ça apporte

- **Reproductibilité** — `uv.lock` épingle les versions exactes ; l'image est
  reconstructible à l'identique.
- **Parité dev/prod** — la même image tourne en local et en production.
- **Isolation** — aucune installation globale ne pollue votre machine.
- **Tout inclus** — Postgres, Redis et MinIO démarrent avec l'API, déjà câblés.

## Comment shaapi utilise Docker

### Une image slim multi-stage
Le `Dockerfile` construit en deux étapes :

1. **builder** — installe les dépendances avec [uv] dans un virtualenv isolé.
2. **runtime** — une image minimale `python:3.11-slim` qui ne copie que le venv
   construit et l'app. Aucun outil de build n'arrive en production → image plus
   petite et plus sûre.

### Dev et prod : même image, comportement différent

| | Dev (défaut) | Prod (`--prod`) |
|---|---|---|
| Code source | **monté** (`.:/app`) | figé dans l'image |
| Reload | oui (`uvicorn --reload`) | non |
| Schéma | créé automatiquement | migrations Alembic |

En dev, le code est monté dans le conteneur : modifier un fichier **recharge** le
serveur instantanément, sans rebuild. (shaapi garde le virtualenv dans
`/opt/venv`, *hors* du `/app` monté, pour que le montage n'écrase jamais vos
dépendances — un détail subtil mais crucial.)

En prod, on build une fois et on sert le code figé, migrations appliquées au
démarrage.

### `docker-compose`, expliqué
Le `docker-compose.yml` de base déclare les services et leurs connexions :

- `api` — votre app FastAPI
- `postgres`, `redis`, `minio` — avec **healthchecks**, pour que l'API ne démarre
  qu'une fois ses dépendances réellement prêtes
- un réseau privé pour que les services se parlent par leur nom

`docker-compose.override.yml` ajoute le montage de dev automatiquement ;
`docker-compose.monitoring.yml` ajoute la stack d'observabilité optionnelle.

`shaapi` est le wrapper multiplateforme au-dessus de tout ça : il pilote
directement `docker compose` et fonctionne sur **Windows, macOS et Linux**, sans
bash :

```bash
shaapi up | down | logs | restart api
shaapi shell | db shell | redis
shaapi db apply | db generate --message "msg"
shaapi up --monitoring        # + Prometheus/Grafana/Tempo/Loki
shaapi up --prod              # mode production
```

Sous Unix, le script shell fourni `./docker-run.sh` est l'équivalent pour ceux
qui le préfèrent — il pilote la même stack.

## Utilisable pour un gros projet ?

Tout à fait — le setup Docker est fait pour grandir :

- **Scaler l'API** — plusieurs workers `api` derrière un load balancer / reverse
  proxy. L'image est stateless.
- **Externaliser l'état** — pointez `POSTGRES_HOST` / `REDIS_HOST` vers des
  services managés (RDS, ElastiCache…) au lieu des conteneurs embarqués.
- **Tâches de fond** — ajoutez un service worker Celery réutilisant la même image.
- **Observabilité** — `--monitoring` apporte métriques, traces et logs pour
  déboguer sous charge.
- **CI/CD** — le build reproductible s'intègre dans n'importe quel pipeline.

Le même `shaapi up` qu'un étudiant lance sur son portable est la fondation
qu'une équipe fait tourner en production. C'est tout l'intérêt.

Voir [Déploiement](deployment.md) pour un parcours concret VPS + TLS.

[uv]: https://github.com/astral-sh/uv
