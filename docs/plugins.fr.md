# Plugins

shaapi livre un cœur minimal et vous laisse ajouter des fonctionnalités
**seulement quand vous en avez besoin** — l'inverse des frameworks qui chargent
tous les modules au démarrage.

Un plugin est un *blueprint* autonome. `shaapi add <nom>` le copie dans votre
projet sous `backend/plugins/<nom>/` ; ensuite c'est *votre* code (lisez-le,
modifiez-le). Son router est auto-découvert — **rien ne se charge tant que vous
ne l'ajoutez pas**, donc votre build ne contient que ce que vous avez choisi.

## Commandes

```bash
shaapi list-plugins          # voir le catalogue
shaapi add advanced_auth     # copier un plugin dans backend/plugins/
shaapi remove advanced_auth  # le retirer
```

`add` injecte aussi les dépendances Python du plugin dans votre
`pyproject.toml` et régénère `uv.lock`, pour que ça build directement. Après
ajout, rechargez l'API (`./docker-run.sh restart-api`) ou rebuildez.

En développement, les tables du plugin se créent automatiquement au démarrage.
En production, générez une migration : `./docker-run.sh makemigrations "add <plugin>"`.

## Plugins disponibles (v0.2.0)

| Plugin | Rôle | Endpoints (sous `/admin/api/v1`) |
|---|---|---|
| `webhooks` | Abonnements + émission d'événements signés HMAC vers des URLs | `/webhooks` |
| `advanced_audit` | Piste d'audit applicative (qui a fait quoi, sur quoi) | `/audit/logs` |
| `advanced_auth` | Auth multi-facteur TOTP par-dessus les utilisateurs intégrés | `/auth/mfa` |
| `user_analytics` | Suivi d'événements, stats agrégées | `/analytics` |
| `payment` | Paiements via un provider pluggable (Stripe inclus) | `/payments` |

Tous les endpoints sont protégés par JWT. Chaque plugin expose aussi un service
appelable depuis votre code (ex. `audit_service.record(...)`,
`webhook_service.emit(...)`).

!!! note "D'autres à venir"
    C'est un lot de départ. Dites-nous quels plugins il vous faut ensuite — le
    catalogue grandit selon les besoins réels de la communauté.

## Écrire votre propre plugin

Un plugin n'est qu'un dossier sous `backend/plugins/<nom>/` qui expose un
`router` dans son module `router` — exactement comme la
[fonctionnalité du tutoriel](create-a-feature.md) :

```
backend/plugins/monplugin/
├── __init__.py        # from backend.plugins.monplugin.router import router
├── models.py          # modèles SQLAlchemy
├── schemas.py         # schémas Pydantic
├── service.py         # logique métier
└── router.py          # APIRouter nommé `router`
```

C'est tout ce dont l'auto-découverte a besoin. Une fois le dossier présent,
l'API le charge au redémarrage suivant.
