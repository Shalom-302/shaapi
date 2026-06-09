# Sécurité (shasec)

`shaapi sec` — **shasec** — audite un projet shaapi et **attaque une API en
fonctionnement** pour confirmer qu'elle résiste. C'est de la bibliothèque
standard pure (aucune dépendance) et en boîte noire : tu peux le pointer sur
n'importe quelle API HTTP, pas seulement shaapi.

Chaque test produit une **sévérité** ; la commande **renvoie un code ≠ 0 dès
qu'il y a un HIGH/CRITICAL**, pour l'utiliser comme garde-fou en CI.

## Audit statique — `shaapi sec audit`

À lancer dans un projet. Il code en dur la revue de sécurité du code généré :

| Test | Sévérité |
| --- | --- |
| Secrets par défaut encore dans `.env` (`TOKEN_SECRET_KEY`, `POSTGRES_PASSWORD`, …) | CRITICAL |
| `.env` suivi par git | CRITICAL |
| Identifiants committés dans `seeder/json/*` | HIGH |
| Le compose de base publie des ports datastores | HIGH |
| CORS `*` avec credentials | HIGH |
| Conteneur en root | MEDIUM |
| Cookies faibles | MEDIUM |
| Docs non protégées par l'environnement | MEDIUM |
| Géo-IP externe activée | LOW |
| Garde-fou de production présent | PASS |

```bash
shaapi sec audit
```

Sur un projet neuf, il ne signale que les **secrets par défaut de dev** (sains
en dev, fatals en prod — le garde-fou les bloque). Après
`shaapi ops secrets --write`, c'est propre.

## Sondes dynamiques — contre une API en fonctionnement

### `shaapi sec auth <url>`

Attaques d'authentification en boîte noire :

- **Forge de JWT à la clé par défaut** — signe un token avec la
  `TOKEN_SECRET_KEY` publique par défaut et appelle `/auth/me`. Une API sans
  état qui ne vérifie que la signature renverrait `200` ; **shaapi le rejette**
  (`401`) car les tokens sont aussi tracés côté serveur dans Redis.
- **Routes non protégées** — les endpoints protégés appelés sans token ne
  doivent pas renvoyer `200`.
- **Rate-limit du login** — les tentatives rapides doivent finir bridées
  (`429`).

```bash
shaapi sec auth http://localhost:8000/admin/api/v1
```

### `shaapi sec scan <url>`

Signale les en-têtes de sécurité manquants (HSTS, X-Content-Type-Options,
X-Frame-Options, CSP) et la taille de la surface OpenAPI exposée.

### `shaapi sec ports <host>`

Se connecte en TCP aux ports datastores (5432 / 6379 / 9000 / 9001). Ils doivent
être **ouverts en dev** (confort) et **fermés en `--prod`**.

```bash
shaapi sec ports localhost     # dev : Postgres/MinIO ouverts
shaapi sec ports ton-vps       # prod : doivent être fermés
```

## En CI

```bash
shaapi sec audit || exit 1     # échoue le build sur HIGH/CRITICAL
```

## La philosophie

shaapi est conçu pour **résister à shasec** : un token forgé à la clé par défaut
est rejeté, le login est bridé, les routes protégées exigent l'auth, et la
production ferme les datastores. shasec sert à le *prouver* — sur tes branches
`dev` comme `prod`. Voir [Production (shaops)](production.md).
