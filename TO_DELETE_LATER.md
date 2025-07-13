# 🗑️ Fichiers et Dossiers à Supprimer Après Migration Multi-Repo

Ce fichier liste tous les fichiers et dossiers qui devront être supprimés du dépôt principal `wakedock/` après la migration vers une architecture multi-dépôts.

## 📁 Dossiers Complets à Supprimer

### Backend (déplacé vers wakedock-backend/)
```
src/
├── wakedock/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── ...
```

### Frontend (déplacé vers wakedock-frontend/)
```
dashboard/
├── src/
├── static/
├── tests/
├── scripts/
├── build/
├── package.json
├── package-lock.json
├── svelte.config.js
├── vite.config.js
├── tailwind.config.js
├── tsconfig.json
├── playwright.config.ts
├── vitest.config.ts
├── eslint.config.js
├── postcss.config.js
├── Dockerfile
├── README.md
├── CHANGELOG.md
├── manage.sh
├── manage.ps1
└── ...
```

### Tests Spécifiques
```
tests/
├── unit/                    # Tests unitaires backend → wakedock-backend/tests/
├── integration/             # Tests d'intégration backend → wakedock-backend/tests/
├── api/                     # Tests API → wakedock-backend/tests/
└── fixtures/                # Fixtures backend → wakedock-backend/tests/
```

## 📄 Fichiers Individuels à Supprimer

### Backend
- `Dockerfile` (racine - remplacé par docker-compose avec build context)
- `requirements.txt` → wakedock-backend/
- `requirements-dev.txt` → wakedock-backend/
- `requirements-prod.txt` → wakedock-backend/
- `pyproject.toml` → wakedock-backend/
- `pytest.ini` → wakedock-backend/
- `tox.ini` → wakedock-backend/
- `alembic.ini` → wakedock-backend/
- `health_check.py` → wakedock-backend/
- `docker-entrypoint.sh` → wakedock-backend/
- `create_admin_user.py` → wakedock-backend/
- `fix_cache.py` → wakedock-backend/
- `manage.py` → wakedock-backend/
- `manage.sh` → wakedock-backend/

### Documentation Spécifique
- `docs/api/` → wakedock-backend/docs/
- `docs/development/backend/` → wakedock-backend/docs/

## 📋 Fichiers à Conserver dans wakedock/ (Dépôt Principal)

### Configuration et Orchestration
- `docker-compose.yml` (modifié pour utiliser les nouveaux dépôts)
- `docker-compose.prod.yml`
- `.env.example`
- `deploy-compose.sh`

### Configuration Caddy
- `caddy/`
  - `Caddyfile.compose`
  - `Caddyfile.prod`
  - `Caddyfile.test`

### Configuration Générale
- `config/`
  - `config.example.yml`
  - `config.schema.json`
  - `secrets.example.yml`
  - `logging.yml`

### Documentation Générale
- `README.md` (mise à jour avec les nouveaux dépôts)
- `CONTRIBUTING.md`
- `LICENSE`
- `CHANGELOG.md`
- `docs/` (documentation générale, déploiement, architecture)

### Scripts et Outils
- `scripts/` (scripts généraux de déploiement et maintenance)
- `.github/` (workflows CI/CD pour l'orchestration)
- `.vscode/` (configuration VS Code pour l'orchestration)

### Makefile et Utilitaires
- `Makefile` (adapté pour l'orchestration)

## 🎯 Structure Finale des Trois Dépôts

### 1. wakedock/ (Principal - Orchestration)
```
wakedock/
├── docker-compose.yml
├── docker-compose.prod.yml
├── deploy-compose.sh
├── .env.example
├── caddy/
├── config/
├── scripts/
├── docs/
├── .github/
├── .vscode/
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── CHANGELOG.md
└── Makefile
```

### 2. wakedock-backend/
```
wakedock-backend/
├── Dockerfile
├── wakedock/
├── tests/
├── requirements*.txt
├── pyproject.toml
├── pytest.ini
├── alembic.ini
├── health_check.py
├── docker-entrypoint.sh
├── manage.py
├── README.md
└── docs/
```

### 3. wakedock-frontend/
```
wakedock-frontend/
├── Dockerfile
├── src/
├── static/
├── tests/
├── package.json
├── svelte.config.js
├── vite.config.js
├── tailwind.config.js
├── tsconfig.json
├── README.md
└── docs/
```

## 🔄 Étapes de Migration

1. **Créer les nouveaux dépôts** `wakedock-backend` et `wakedock-frontend`
2. **Copier les fichiers** selon cette liste vers les nouveaux dépôts
3. **Tester les builds** individuels des nouveaux dépôts
4. **Mettre à jour** le `docker-compose.yml` principal
5. **Tester l'orchestration** complète
6. **Supprimer les fichiers** listés ci-dessus du dépôt principal
7. **Mettre à jour** la documentation et les README

## ⚠️ Attention

**NE PAS SUPPRIMER** ces fichiers tant que :
- Les nouveaux dépôts ne sont pas créés et testés
- Le docker-compose.yml principal n'est pas validé
- Les tests d'intégration ne passent pas
- La documentation n'est pas mise à jour
