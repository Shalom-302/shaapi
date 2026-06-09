# Déploiement

shaapi propose un workflow orienté dev (montage du code + hot-reload) et un mode
production (image figée, sans montage). Ce guide vous mène à un déploiement de
production sur un VPS.

!!! tip "Laissez shaops faire"
    `shaapi ops` génère pour vous l'overlay de production durci, des secrets
    forts et les scripts de provisionnement/pare-feu du VPS — voir
    [Production (shaops)](production.md). Cette page explique ce qui se passe
    sous le capot.

## Dev vs prod, en une image

| | Dev (défaut) | Prod (`--prod`) |
|---|---|---|
| Code source | monté (`.:/app`) | figé dans l'image |
| Reload | oui (`--reload`) | non |
| Schéma | auto-créé (`DB_AUTO_CREATE=true`) | migrations Alembic |
| Commande | `shaapi up` | `shaapi up --prod` |

## 1. Checklist de production

Avant de déployer, éditez `.env` :

```env
ENVIRONMENT=prod
DB_AUTO_CREATE=false

# Secrets forts et uniques — jamais les défauts de dev
TOKEN_SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(32))">
OPERA_LOG_ENCRYPT_SECRET_KEY=<python -c "import os;print(os.urandom(32).hex())">

# Vrais identifiants base / redis / stockage
POSTGRES_PASSWORD=<mot-de-passe-fort>
MINIO_ACCESS_KEY=<clé>
MINIO_SECRET_KEY=<secret>

# Origine(s) de votre front-end pour le CORS — dans backend/core/conf.py ou env
```

Assurez-vous d'avoir une migration initiale versionnée et votre schéma capturé :

```bash
shaapi db generate --message "initial"   # si vous avez ajouté des modèles
```

`shaapi` est le runner multiplateforme (sans bash). Sous un shell Unix, le script
`./docker-run.sh` en est l'équivalent (`./docker-run.sh makemigrations "initial"`).

## 2. Provisionner un VPS

N'importe quelle machine Linux avec Docker convient (exemple Ubuntu) :

```bash
# Sur le serveur
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # se reconnecter ensuite
git clone <votre-depot> mon_api && cd mon_api
pip install shaapi                      # runner multiplateforme (ou ./docker-run.sh)
cp .env.template .env && nano .env      # appliquer la checklist ci-dessus
```

## 3. Démarrer en mode production

```bash
shaapi up --prod
```

L'image slim est construite et la stack tourne **sans** le montage de dev, en
servant le code figé. L'entrypoint exécute `alembic upgrade head` au démarrage :
votre schéma est migré automatiquement.

Commandes utiles une fois la stack lancée :

```bash
shaapi logs              # suivre les logs de la stack
shaapi db apply          # relancer les migrations si besoin
shaapi down              # arrêter la stack
```

## 4. TLS / reverse proxy

Placez un reverse proxy devant l'API (port 8000) pour terminer le HTTPS. Avec
[Caddy](https://caddyserver.com), un `Caddyfile` de deux lignes suffit :

```
api.exemple.com {
    reverse_proxy localhost:8000
}
```

Caddy obtient et renouvelle les certificats Let's Encrypt automatiquement.
Traefik ou nginx font tout aussi bien l'affaire.

## 5. Observabilité (optionnel)

```bash
shaapi up --prod --monitoring
```

Ajoute Prometheus, Tempo, Loki et Grafana, et reconstruit l'image de l'API avec
l'extra monitoring et `OBSERVABILITY_ENABLED=true`.

- Grafana → `http://<hôte>:3000`
- Prometheus → `http://<hôte>:9090`

Gardez ces ports derrière un pare-feu / une authentification en production.

## 6. Sauvegardes de la base

L'approche la plus simple : un `pg_dump` planifié :

```bash
# crontab -e  → tous les jours à 02h00
0 2 * * * docker compose -f /chemin/mon_api/docker-compose.yml exec -T postgres \
  pg_dump -U postgres shaapi | gzip > /backups/db-$(date +\%F).sql.gz
```

Pour des sauvegardes automatiques avec rotation, ajoutez un service
`prodrigestivill/postgres-backup-local` à votre compose.

## 7. Mises à jour

```bash
git pull
shaapi up --prod        # rebuild seulement si deps/code ont changé
```

Les dépendances étant épinglées dans `uv.lock`, les builds sont reproductibles.

---

Voilà : un déploiement reproductible, piloté par migrations et terminé en TLS.
Combinez-le avec l'[architecture](architecture.md) pour durcir davantage
(workers, Postgres/Redis externes, gestionnaire de secrets).
