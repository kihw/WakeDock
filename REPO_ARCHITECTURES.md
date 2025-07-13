# 🏗️ Arborescences des Trois Dépôts WakeDock

## 📁 1. wakedock/ (Dépôt Principal - Orchestration)

```
wakedock/
├── 📄 README.md                     # Documentation principale avec liens vers les autres dépôts
├── 📄 CONTRIBUTING.md               # Guide de contribution
├── 📄 LICENSE                       # Licence du projet
├── 📄 CHANGELOG.md                  # Historique des changements
├── 📄 docker-compose.yml            # Orchestration des services (build depuis GitHub)
├── 📄 docker-compose.prod.yml       # Configuration production
├── 📄 .env.example                  # Variables d'environnement exemple
├── 🔧 deploy-compose.sh             # Script de déploiement principal
├── 🔧 Makefile                      # Commandes de gestion du projet
├── 📁 caddy/                        # Configuration du reverse proxy
│   ├── 📄 Caddyfile.compose         # Config Caddy pour développement
│   ├── 📄 Caddyfile.prod            # Config Caddy pour production
│   └── 📄 Caddyfile.test            # Config Caddy pour tests
├── 📁 config/                       # Configuration générale
│   ├── 📄 config.example.yml        # Configuration exemple
│   ├── 📄 config.schema.json        # Schéma de validation config
│   ├── 📄 secrets.example.yml       # Secrets exemple
│   └── 📄 logging.yml               # Configuration des logs
├── 📁 scripts/                      # Scripts d'administration
│   ├── 📄 README.md
│   ├── 🔧 cleanup-migration-guide.sh
│   ├── 🔧 migration-helper.sh
│   ├── 🔧 start.sh
│   ├── 📁 setup/
│   ├── 📁 maintenance/
│   ├── 📁 monitoring/
│   └── 📁 database/
├── 📁 docs/                         # Documentation générale
│   ├── 📄 index.md
│   ├── 📁 architecture/             # Architecture système
│   ├── 📁 deployment/               # Guide de déploiement
│   └── 📁 operations/               # Guide d'exploitation
├── 📁 .github/                      # GitHub Actions et templates
│   ├── 📁 workflows/
│   └── 📁 ISSUE_TEMPLATE/
├── 📁 .vscode/                      # Configuration VS Code
│   ├── 📄 tasks.json
│   ├── 📄 launch.json
│   └── 🔧 debug.sh
└── 📁 data/                         # Données persistantes (volumes)
    ├── 📁 caddy/
    ├── 📁 caddy-config/
    └── 📁 dashboard/
```

## 📁 2. wakedock-backend/ (Backend FastAPI)

```
wakedock-backend/
├── 📄 README.md                     # Documentation backend
├── 📄 CHANGELOG.md                  # Historique des changements backend
├── 📄 Dockerfile                    # Build container backend
├── 🔧 docker-entrypoint.sh          # Point d'entrée container
├── 🔧 health_check.py               # Vérification santé service
├── 🔧 create_admin_user.py          # Création utilisateur admin
├── 🔧 fix_cache.py                  # Utilitaire cache
├── 🔧 manage.py                     # Script de gestion
├── 🔧 manage.sh                     # Script de gestion shell
├── 📄 requirements.txt              # Dépendances Python de base
├── 📄 requirements-dev.txt          # Dépendances développement
├── 📄 requirements-prod.txt         # Dépendances production
├── 📄 pyproject.toml                # Configuration projet Python
├── 📄 pytest.ini                   # Configuration tests
├── 📄 tox.ini                       # Configuration tox
├── 📄 alembic.ini                   # Configuration migrations DB
├── 📁 wakedock/                     # Code source principal
│   ├── 📄 __init__.py
│   ├── 📄 main.py                   # Point d'entrée FastAPI
│   ├── 📁 api/                      # Routes et endpoints
│   │   ├── 📄 __init__.py
│   │   ├── 📁 v1/
│   │   ├── 📁 middleware/
│   │   └── 📁 dependencies/
│   ├── 📁 core/                     # Configuration et utilitaires core
│   │   ├── 📄 config.py
│   │   ├── 📄 security.py
│   │   ├── 📄 database.py
│   │   └── 📄 redis.py
│   ├── 📁 models/                   # Modèles SQLAlchemy
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 user.py
│   │   └── 📄 service.py
│   ├── 📁 services/                 # Logique métier
│   │   ├── 📄 __init__.py
│   │   ├── 📄 docker_service.py
│   │   ├── 📄 user_service.py
│   │   └── 📄 auth_service.py
│   ├── 📁 schemas/                  # Schémas Pydantic
│   │   ├── 📄 __init__.py
│   │   ├── 📄 user.py
│   │   └── 📄 service.py
│   └── 📁 utils/                    # Utilitaires
│       ├── 📄 __init__.py
│       ├── 📄 docker_client.py
│       └── 📄 logging.py
├── 📁 tests/                        # Tests backend
│   ├── 📄 conftest.py
│   ├── 📄 test_security_services.py
│   ├── 📁 unit/
│   ├── 📁 integration/
│   ├── 📁 api/
│   ├── 📁 e2e/
│   └── 📁 fixtures/
├── 📁 alembic/                      # Migrations base de données
│   ├── 📄 env.py
│   ├── 📄 script.py.mako
│   └── 📁 versions/
├── 📁 docs/                         # Documentation backend
│   ├── 📄 api.md
│   ├── 📄 development.md
│   └── 📄 deployment.md
└── 📁 scripts/                      # Scripts spécifiques backend
    ├── 📄 init_db.py
    └── 📄 seed_data.py
```

## 📁 3. wakedock-frontend/ (Frontend SvelteKit)

```
wakedock-frontend/
├── 📄 README.md                     # Documentation frontend
├── 📄 CHANGELOG.md                  # Historique des changements frontend
├── 📄 Dockerfile                    # Build container frontend
├── 📄 package.json                  # Dépendances Node.js
├── 📄 package-lock.json             # Lock file des dépendances
├── 📄 svelte.config.js              # Configuration SvelteKit
├── 📄 vite.config.js                # Configuration Vite
├── 📄 vite.performance.config.js    # Config Vite optimisée
├── 📄 tailwind.config.js            # Configuration TailwindCSS
├── 📄 tsconfig.json                 # Configuration TypeScript
├── 📄 playwright.config.ts          # Configuration tests E2E
├── 📄 vitest.config.ts              # Configuration tests unitaires
├── 📄 eslint.config.js              # Configuration ESLint
├── 📄 postcss.config.js             # Configuration PostCSS
├── 🔧 manage.sh                     # Script de gestion Unix
├── 🔧 manage.ps1                    # Script de gestion PowerShell
├── 📁 src/                          # Code source frontend
│   ├── 📄 app.html                  # Template HTML principal
│   ├── 📄 app.css                   # Styles globaux
│   ├── 📄 app.d.ts                  # Types TypeScript globaux
│   ├── 📄 App.svelte                # Composant racine
│   ├── 📄 main.ts                   # Point d'entrée client
│   ├── 📄 service-worker.ts         # Service Worker
│   ├── 📄 hooks.server.ts           # Hooks serveur SvelteKit
│   ├── 📁 lib/                      # Bibliothèque de composants
│   │   ├── 📁 components/
│   │   │   ├── 📁 ui/               # Composants UI réutilisables
│   │   │   │   ├── 📁 atoms/        # Composants atomiques
│   │   │   │   ├── 📁 molecules/    # Composants moléculaires
│   │   │   │   └── 📁 organisms/    # Composants organismes
│   │   │   ├── 📁 layout/           # Composants de mise en page
│   │   │   └── 📁 features/         # Composants métier
│   │   ├── 📁 stores/               # Stores Svelte
│   │   ├── 📁 utils/                # Utilitaires
│   │   ├── 📁 types/                # Types TypeScript
│   │   └── 📁 api/                  # Client API
│   ├── 📁 routes/                   # Routes SvelteKit
│   │   ├── 📄 +layout.svelte
│   │   ├── 📄 +page.svelte
│   │   ├── 📁 dashboard/
│   │   ├── 📁 services/
│   │   ├── 📁 auth/
│   │   └── 📁 api/
│   └── 📁 test/                     # Utilitaires de test
├── 📁 static/                       # Assets statiques
│   ├── 📄 favicon.ico
│   ├── 📄 favicon.png
│   ├── 📁 icons/
│   └── 📁 images/
├── 📁 tests/                        # Tests frontend
│   ├── 📁 unit/                     # Tests unitaires
│   ├── 📁 integration/              # Tests d'intégration
│   └── 📁 e2e/                      # Tests end-to-end
├── 📁 scripts/                      # Scripts spécifiques frontend
│   ├── 📄 optimize-images.js
│   ├── 📄 replace-console-logs.js
│   └── 🔧 production-cleanup.sh
├── 📁 docs/                         # Documentation frontend
│   ├── 📄 components.md
│   ├── 📄 development.md
│   └── 📄 deployment.md
└── 📁 build/                        # Build output (généré)
    ├── 📄 index.js
    └── 📁 client/
```

## 🔗 Intégration et Communication

### Variables d'Environnement Clés

**wakedock-backend:**
- `PORT=5000`
- `DATABASE_URL=postgresql://...`
- `REDIS_URL=redis://...`

**wakedock-frontend:**
- `PORT=3000`
- `WAKEDOCK_API_URL=http://wakedock-backend:5000`
- `VITE_API_BASE_URL=/api/v1`

### Communication Inter-Services

```yaml
# Backend expose l'API sur le port 5000
wakedock-backend:5000 -> API REST + WebSocket

# Frontend expose l'interface sur le port 3000  
wakedock-frontend:3000 -> Interface utilisateur

# Caddy fait le reverse proxy
caddy:80/443 -> Routage vers backend et frontend
```

## 🚀 Commandes de Développement

### Dépôt Principal (wakedock/)
```bash
# Déploiement complet
./deploy-compose.sh --dev

# Nettoyage et redéploiement
./deploy-compose.sh --clean

# Vérification des services
docker-compose ps
```

### Backend (wakedock-backend/)
```bash
# Tests
pytest tests/ -v

# Démarrage local (développement uniquement)
uvicorn wakedock.main:app --reload --port 5000
```

### Frontend (wakedock-frontend/)
```bash
# Tests
npm test

# Build
npm run build

# Démarrage local (développement uniquement)
npm run dev -- --port 3000
```
