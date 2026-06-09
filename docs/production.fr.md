# Production (shaops)

`shaapi ops` — **shaops** — transforme le runbook manuel « mise en prod sur un
VPS » en quelques commandes. Il se contente de **générer des fichiers que tu
exécutes toi-même** sur le serveur ; il ne se connecte jamais à l'extérieur et
ne manipule aucun de tes secrets sur le réseau.

## Sécurisé par défaut

Un projet généré est difficile à déployer *de façon non sécurisée* :

- un **garde-fou de production** refuse de démarrer (hors dev) tant qu'un secret
  par défaut subsiste ;
- le conteneur tourne en utilisateur **non-root** ;
- en production les **datastores ne publient aucun port hôte** — Postgres, Redis
  et MinIO ne sont joignables que sur le réseau Docker interne.

## Le modèle de branches dev / prod

```bash
shaapi new "mon api" --prod
```

Cela crée un dépôt git avec deux branches :

| Branche | Contenu |
| --- | --- |
| `dev` | le projet de développement léger (tu démarres ici) |
| `prod` | le même projet **plus** la config de production |

Le **code applicatif (`backend/`) est identique sur les deux branches** — seule
la config diverge (l'overlay compose de prod, l'exemple d'env, les scripts de
déploiement). On livre en fusionnant `dev` dans `prod` ; le VPS suit `prod`.
Aucun *drift* de code.

> Déjà un projet ? Lance `shaapi ops harden` pour ajouter la config de
> production sur place.

## Ce qu'écrit `shaapi ops harden`

| Fichier | Rôle |
| --- | --- |
| `docker-compose.prod.yml` | overlay : les datastores ne publient **aucun port hôte**, `ENVIRONMENT=prod`, un sidecar de backup Postgres quotidien |
| `.env.prod.example` | le modèle d'env de production (à copier en `.env` sur le serveur) |
| `deploy/provision.sh` | installe Docker Engine + compose sur Ubuntu/Debian |
| `deploy/harden-os.sh` | pare-feu (ufw : refuse tout sauf 22/80/443) + vérif d'exposition des ports |

## Mise en production

```bash
# 1. Sur le serveur (une fois)
ssh root@ton-vps 'bash -s' < deploy/provision.sh    # installe Docker
ssh root@ton-vps 'bash -s' < deploy/harden-os.sh    # pare-feu

# 2. Config (sur le serveur)
cp .env.prod.example .env
shaapi ops secrets --write     # génère + injecte des secrets forts dans .env
#   ... puis renseigne POSTGRES_PASSWORD / MINIO_SECRET_KEY au besoin

# 3. Lancer la stack durcie
shaapi up --prod               # charge docker-compose.prod.yml (datastores fermés)
shaapi db apply                # migrations
shaapi auth init               # premier admin
```

Place un reverse proxy (nginx / Caddy / Traefik) devant, qui termine le TLS sur
443 et transmet à l'API sur `127.0.0.1:8000`.

`shaapi ops checklist` affiche la checklist complète de mise en production.

## Vérifier le durcissement

```bash
shaapi sec ports ton-vps       # Postgres/MinIO doivent être FERMÉS
ss -tulnp | grep -E ':(5432|9000)'   # rien sur 0.0.0.0
```

Voir [Sécurité (shasec)](security.md) pour attaquer ta propre API et confirmer
qu'elle résiste.
