# Référence CLI

`shaapi` est deux outils en un :

- un **générateur** — `shaapi new "mon api"` crée un projet ;
- un **runner de projet** — depuis un projet généré, `shaapi up`,
  `shaapi db apply`, `shaapi auth init`… pilotent **directement** `docker
  compose`, donc les mêmes commandes marchent sur **Windows, macOS et Linux**
  (sans bash, sans le « `./docker-run.sh` n'est pas reconnu »).

```bash
pip install shaapi
shaapi --help          # liste toutes les commandes
shaapi <groupe> --help  # ex. shaapi db --help
```

## Conventions

- **`--path, -p`** — presque toutes les commandes runner acceptent `-p <dir>`
  pour cibler un dossier de projet. Par défaut `.`, et shaapi remonte jusqu'à la
  racine du projet (le dossier avec `backend/` + `pyproject.toml`) : vous pouvez
  donc lancer les commandes depuis n'importe quel sous-dossier.
- **La stack doit tourner** — les commandes `db`, `auth`, `storage` et `shell`
  font un `exec` dans un conteneur. Si la stack est arrêtée, elles échouent
  immédiatement avec *« Start the stack first with `shaapi up` »* au lieu d'une
  erreur Docker cryptique.
- **Options globales** — `shaapi --version` (`-V`) affiche la version ; `--help`
  est disponible sur chaque commande et groupe.

---

## Génération

### `shaapi new`

Créer un nouveau projet.

```bash
shaapi new "mon api"
shaapi new "mon api" -y                      # valeurs par défaut, sans questions
shaapi new "mon api" --prod                  # + config de production sur une branche `prod`
shaapi new "mon api" --monitoring --no-git
shaapi new "mon api" --path ./projets
```

| Option | Description |
| --- | --- |
| `--path, -p` | Où créer le projet (défaut `.`). |
| `--prod` | Génère aussi la config de production sur une branche git `prod` (même code, seule la config diverge). |
| `--monitoring / --no-monitoring` | Inclure la stack Prometheus/Grafana/Tempo/Loki. |
| `--git / --no-git` | Initialiser un dépôt git. |
| `--yes, -y` | Accepter les défauts, ignorer les questions. |

Le nom du projet devient un *slug* sûr (`mon api` → `mon_api`) utilisé pour le
dossier, les conteneurs Docker, la base de données et le titre de l'app.

!!! note "Alias"
    `shaapi create-project` est un alias caché et déprécié de `shaapi new`.

---

## Cycle de vie

### `shaapi up`

Construire et démarrer toute la stack (API, Postgres, Redis, MinIO). En mode dev,
le code est monté en volume pour le hot-reload.

```bash
shaapi up
shaapi up --monitoring     # + Prometheus/Grafana/Tempo/Loki
shaapi up --prod           # production : charge docker-compose.prod.yml (datastores non exposés)
```

| Option | Description |
| --- | --- |
| `--monitoring` | Ajoute la stack d'observabilité (projet généré avec monitoring requis). |
| `--prod` | Mode production — charge `docker-compose.prod.yml` (les datastores ne publient aucun port hôte), sans montage de dev. |
| `--path, -p` | Dossier du projet. |

### `shaapi down`

Arrêter et supprimer les conteneurs de la stack.

```bash
shaapi down
shaapi down --monitoring   # arrête aussi la stack de monitoring
```

### `shaapi logs`

Suivre les logs des conteneurs (Ctrl-C pour arrêter).

```bash
shaapi logs        # tous les services
shaapi logs api    # un seul service
```

### `shaapi restart`

Redémarrer tous les conteneurs, ou un seul service.

```bash
shaapi restart
shaapi restart api
```

### `shaapi ps`

Afficher l'état des conteneurs.

### `shaapi shell`

Ouvrir un shell `bash` dans le conteneur `api`.

### `shaapi redis`

Ouvrir `redis-cli` dans le conteneur Redis.

---

## Base de données (`db`)

Les migrations s'appuient sur Alembic et s'exécutent dans le conteneur `api`.

### `shaapi db generate`

Générer automatiquement une migration à partir des changements de modèles.

```bash
shaapi db generate --message "add posts table"
shaapi db generate -m "add posts table"
```

| Option | Description |
| --- | --- |
| `--message, -m` | Message de migration (**requis**). |
| `--path, -p` | Dossier du projet. |

!!! tip "Les nouveaux modèles sont auto-détectés"
    Déposez un `backend/models/<nom>.py` définissant une sous-classe de `Base` :
    il est pris en compte automatiquement — plus besoin d'éditer
    `backend/models/__init__.py`.

### `shaapi db apply`

Appliquer les migrations en attente (`alembic upgrade head`).

### `shaapi db preview`

Afficher le SQL que `shaapi db apply` exécuterait, **sans l'exécuter**.

### `shaapi db pending`

Afficher la révision actuelle de la base vs le dernier *head* (un écart = des
migrations en attente).

### `shaapi db shell`

Ouvrir `psql` dans le conteneur Postgres (user/base lus depuis `.env`).

---

## Auth (`auth`)

### `shaapi auth init`

Créer un utilisateur admin (avec le rôle `admin`) pour vous connecter à Swagger.
Demande l'email et le mot de passe s'ils ne sont pas fournis.

```bash
shaapi auth init
shaapi auth init --email vous@exemple.com --password "s3cret"
```

| Option | Description |
| --- | --- |
| `--email, -e` | Email admin (login). Demandé si omis. |
| `--password, -w` | Mot de passe admin. Demandé (masqué) si omis. |
| `--path, -p` | Dossier du projet. |

---

## Stockage (`storage`)

### `shaapi storage init`

S'assurer que le bucket de stockage objet configuré (MinIO / S3) existe.

```bash
shaapi storage init
```

---

## Production (`ops`)

**shaops** génère les artefacts de production durcis — des fichiers que **tu**
exécutes sur le serveur (il ne se connecte jamais à l'extérieur).

### `shaapi ops harden`

Écrit `docker-compose.prod.yml` (les datastores ne publient aucun port hôte,
`ENVIRONMENT=prod`, un sidecar de backup Postgres quotidien),
`.env.prod.example` et les scripts `deploy/` (`provision.sh` : installe Docker ;
`harden-os.sh` : ufw + vérification d'exposition des ports).

### `shaapi ops secrets`

Génère des secrets forts. `--write` les injecte dans le `.env` du projet.

```bash
shaapi ops secrets            # les afficher
shaapi ops secrets --write    # les injecter dans .env
```

### `shaapi ops checklist`

Affiche la checklist de mise en production.

!!! tip "Workflow à deux branches"
    `shaapi new "mon api" --prod` crée une branche `dev` et une branche `prod`
    au **code applicatif identique** — seule la config de prod diverge. On livre
    en fusionnant `dev` dans `prod` ; le VPS suit `prod`.

---

## Sécurité (`sec`)

**shasec** audite un projet et sonde une API en fonctionnement. Chaque résultat
porte une sévérité, et la commande **renvoie un code ≠ 0 dès qu'il y a un
HIGH/CRITICAL** (compatible CI). Pur stdlib — aucune dépendance.

### `shaapi sec audit`

Audit statique du projet : secrets par défaut, identifiants committés, ports
datastores exposés, conteneur root, cookies faibles, docs non protégées, géo-IP
externe, et présence du garde-fou de production.

### `shaapi sec auth <url>`

Sondes d'authentification en boîte noire : forge un JWT avec la clé par défaut,
détecte les routes non protégées, vérifie le rate-limit du login.

```bash
shaapi sec auth http://localhost:8000/admin/api/v1
```

### `shaapi sec scan <url>`

Signale les en-têtes de sécurité manquants et la surface OpenAPI exposée.

### `shaapi sec ports <host>`

Vérifie l'accessibilité TCP des ports datastores (5432 / 6379 / 9000 / 9001) sur
un hôte — ouverts en dev, fermés en `--prod`.

```bash
shaapi sec ports localhost
```

---

## Plugins

### `shaapi list-plugins`

Lister les plugins ajoutables à un projet.

### `shaapi add`

Ajouter un plugin au projet courant — le copie dans `backend/plugins/<nom>/`,
injecte ses dépendances Python dans `pyproject.toml` et régénère `uv.lock`.

```bash
shaapi add payment
```

Rechargez ensuite l'API avec `shaapi restart api`.

### `shaapi remove`

Supprimer un plugin installé.

```bash
shaapi remove payment
```

---

## Meta

### `shaapi version`

Afficher la version installée de shaapi (équivalent à `shaapi --version`).

---

## Équivalence `docker-run.sh`

Sous Linux/macOS, le script shell fourni `./docker-run.sh` pilote la même stack
si vous préférez un script simple. Correspondance :

| `shaapi` | `./docker-run.sh` |
| --- | --- |
| `shaapi up` | `./docker-run.sh up` |
| `shaapi up --monitoring` | `./docker-run.sh up --monitoring` |
| `shaapi up --prod` | `./docker-run.sh up --prod` |
| `shaapi down` | `./docker-run.sh down` |
| `shaapi logs` | `./docker-run.sh logs` |
| `shaapi logs api` | `./docker-run.sh api-logs` |
| `shaapi restart api` | `./docker-run.sh restart-api` |
| `shaapi shell` | `./docker-run.sh shell` |
| `shaapi db shell` | `./docker-run.sh db` |
| `shaapi redis` | `./docker-run.sh redis` |
| `shaapi db apply` | `./docker-run.sh migrate` |
| `shaapi db generate -m "msg"` | `./docker-run.sh makemigrations "msg"` |

`shaapi` est le défaut multiplateforme ; `./docker-run.sh` en est l'équivalent
Unix uniquement.
