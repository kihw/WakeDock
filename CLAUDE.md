## 🐳 App Overview
**WakeDock** - Docker management platform: FastAPI backend (5000), Next.js 14+ frontend (3000), Caddy proxy (80/443), PostgreSQL (5432), Redis (6379).

**Production Domain**: https://mtool.ovh with automatic HTTPS/SSL certificates
**Credentials**: admin / e2riv8%uy7tCgbQb4B57

## 📁 Project Structure
```
/Docker/code/wakedock-env/
├── WakeDock/                      # 🎯 Main orchestration repository
│   ├── docker-compose*.yml       # Docker Compose configurations
│   ├── deploy-compose.sh          # Legacy deployment script
│   ├── deploy-multi-repo.sh       # 🚀 Multi-repo deployment script (USE THIS)
│   ├── Makefile                   # Build automation and tasks
│   ├── .env                       # Environment variables with mtool.ovh config
│   ├── CLAUDE.md                  # This file - project instructions
│   ├── README.md                  # Project documentation
│   ├── LICENSE                    # Project license
│   │
│   ├── caddy/                     # 🌐 Reverse proxy configurations
│   │   ├── Caddyfile.domain       # 🔒 Production HTTPS config (mtool.ovh)
│   │   └── Caddyfile.test         # 🛠️ Development HTTP config
│   │
│   ├── config/                    # ⚙️ Configuration files
│   │   ├── config.dev.yml         # Development configuration
│   │   ├── config.example.yml     # Example configuration
│   │   ├── config.full-example.yml# Full configuration example
│   │   ├── config.schema.json     # Configuration schema
│   │   ├── logging.yml            # Logging configuration
│   │   └── secrets.example.yml    # Example secrets
│   │
│   ├── scripts/                   # 🔧 Maintenance and utility scripts
│   │   ├── database/              # Database management scripts
│   │   ├── maintenance/           # Maintenance and backup scripts
│   │   ├── monitoring/            # Monitoring and performance scripts
│   │   ├── setup/                 # Setup and validation scripts
│   │   └── *.sh                   # Various utility scripts
│   │
│   ├── docs/                      # 📚 Documentation
│   │   ├── api/                   # API documentation
│   │   ├── architecture/          # Architecture documentation
│   │   ├── deployment/            # Deployment guides
│   │   ├── development/           # Development guides
│   │   └── operations/            # Operations guides
│   │
│   ├── data/                      # 💾 Persistent data volumes
│   │   ├── caddy/                 # Caddy SSL certificates and data
│   │   ├── caddy-config/          # Caddy configuration cache
│   │   ├── postgres/              # PostgreSQL data
│   │   ├── redis/                 # Redis data
│   │   └── dashboard/             # Dashboard data
│   │
│   ├── logs/                      # 📝 Log files
│   ├── reports/                   # 📊 Analysis and audit reports
│   ├── wakedock-backend/          # Backend symlink/submodule
│   └── wakedock-frontend/         # Frontend symlink/submodule
│
├── wakedock-backend/              # 🐍 Backend FastAPI repository
│   ├── wakedock/                  # Main Python package
│   │   ├── api/                   # FastAPI routes and middleware
│   │   │   ├── auth/              # Authentication routes
│   │   │   └── routes/            # API routes (health, services, system)
│   │   ├── core/                  # Business logic
│   │   │   ├── caddy.py           # Caddy integration
│   │   │   ├── monitoring.py      # System monitoring
│   │   │   └── orchestrator.py    # Docker orchestration
│   │   ├── database/              # Database layer
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   └── migrations/        # Alembic migrations
│   │   ├── security/              # Security features
│   │   │   ├── rate_limit.py      # Rate limiting
│   │   │   └── validation.py      # Input validation
│   │   └── utils/                 # Utility functions
│   ├── tests/                     # 🧪 Comprehensive test suite
│   │   ├── unit/                  # Unit tests
│   │   ├── integration/           # Integration tests
│   │   ├── e2e/                   # End-to-end tests
│   │   └── fixtures/              # Test fixtures
│   ├── scripts/                   # Backend-specific scripts
│   ├── docs/                      # Backend documentation
│   ├── alembic/                   # Database migrations
│   ├── Dockerfile                 # Backend Docker configuration
│   ├── requirements*.txt          # Python dependencies
│   └── pyproject.toml             # Python project configuration
│
└── wakedock-frontend/             # ⚛️ Frontend Next.js 14+ repository
    ├── src/                       # Source code
    │   ├── app/                   # 📱 Next.js App Router
    │   │   ├── login/             # Login page
    │   │   ├── monitoring/        # Monitoring dashboard
    │   │   ├── services/          # Services management
    │   │   ├── settings/          # Settings page
    │   │   └── users/             # User management
    │   ├── components/            # 🧩 React components (.tsx)
    │   │   ├── dashboard/         # Dashboard components
    │   │   ├── forms/             # Form components
    │   │   ├── layout/            # Layout components
    │   │   ├── monitoring/        # Monitoring components
    │   │   ├── services/          # Service components
    │   │   └── ui/                # UI components
    │   ├── lib/                   # 📚 Shared utilities and services
    │   │   ├── api/               # API client services
    │   │   ├── config/            # Configuration
    │   │   ├── stores/            # State management
    │   │   ├── types/             # TypeScript definitions
    │   │   ├── utils/             # Utility functions
    │   │   └── websocket.ts       # WebSocket client
    │   └── routes/                # 🚪 Legacy Svelte routes (migration)
    ├── public/                    # 🌐 Static files
    │   ├── favicon.ico            # Favicon
    │   ├── logo.svg               # WakeDock logo
    │   ├── manifest.json          # PWA manifest
    │   └── *.png                  # Icons and images
    ├── tests/                     # 🧪 Frontend testing
    │   ├── unit/                  # Unit tests
    │   ├── integration/           # Integration tests
    │   ├── e2e/                   # End-to-end tests
    │   └── performance/           # Performance tests
    ├── scripts/                   # Frontend-specific scripts
    ├── stories/                   # 📖 Storybook stories
    ├── static/                    # Static assets
    ├── Dockerfile                 # Frontend Docker configuration
    ├── next.config.js             # Next.js configuration
    ├── package.json               # Node.js dependencies
    ├── tailwind.config.js         # Tailwind CSS configuration
    └── tsconfig.json              # TypeScript configuration
```

## 🛡️ MANDATORY RULES

### 1. 🐳 Deploy via Multi-Repo Script ONLY
```bash
# ✅ CORRECT - ALWAYS use deploy-multi-repo.sh from WakeDock/ directory
cd /Docker/code/wakedock-env/WakeDock/
./deploy-multi-repo.sh

# Clean deployment (rebuild everything)
./deploy-multi-repo.sh --clean

# ❌ NEVER use compose directly
docker-compose up -d
docker compose up -d
```

### 2. 🔍 Debug via Container Logs ONLY
```bash
# ✅ CORRECT - Check service logs
docker-compose logs wakedock-core -f
docker-compose logs wakedock-postgres -f
docker-compose logs wakedock-redis -f
docker-compose logs wakedock-caddy -f

# ✅ CORRECT - Check all services at once
docker-compose ps
docker-compose logs -f

# ❌ NEVER debug locally
docker-compose exec wakedock python -c "import wakedock"
python src/wakedock/main.py
```

### 3. 🌐 Test via Public IP ONLY  
```bash
# ✅ CORRECT
curl "http://YOUR_PUBLIC_IP:80/api/v1/health"

# ❌ NEVER  
curl "http://localhost:8000/health"
```

### 4. 🔄 Multi-Repo Deployment Workflow (MANDATORY)
```bash
# ALWAYS execute after ANY change from WakeDock/ directory
cd /Docker/code/wakedock-env/WakeDock/
./deploy-multi-repo.sh

# Clean deployment (rebuild everything)
./deploy-multi-repo.sh --clean

# Check service status
docker-compose -f docker-compose-local-multi-repo.yml ps

# View logs
docker-compose -f docker-compose-local-multi-repo.yml logs -f
```

## 🔧 Code Standards

### Backend (Python)
- **Async/await** mandatory for I/O
- **Type hints** required
- **Pydantic** for validation
- **FastAPI** dependency injection

### Frontend (TypeScript)
- **TypeScript** mandatory
- **Next.js 14+** with App Router
- **React 18** components (.tsx)
- **Centralized API client**
- **Error boundaries**

### Docker
- **Health checks** in all services
- **Multi-stage builds** for production
- **Non-root users** for security

## 🧪 Testing
```bash
# Tests via Multi-Repo Deployment + Public IP or Domain
export PUBLIC_IP=$(curl -s -4 ifconfig.me)

# Deploy first from WakeDock/ directory
cd /Docker/code/wakedock-env/WakeDock/
./deploy-multi-repo.sh

# Wait for services to be ready
sleep 60

# Test health endpoint (HTTPS)
curl -f "https://mtool.ovh/api/v1/health"

# Test frontend (HTTPS)
curl -f "https://mtool.ovh/"

# Test with public IP (HTTP)
curl -f "http://${PUBLIC_IP}:80/api/v1/health"

# Check all services are running
docker-compose -f docker-compose-local-multi-repo.yml ps
```

## 🔍 Advanced Debugging
```bash
# Debug specific service issues from WakeDock/ directory
cd /Docker/code/wakedock-env/WakeDock/
docker-compose -f docker-compose-local-multi-repo.yml logs wakedock-core --tail 100 -f
docker-compose -f docker-compose-local-multi-repo.yml logs wakedock-caddy --tail 100 -f
docker-compose -f docker-compose-local-multi-repo.yml logs wakedock-dashboard --tail 100 -f

# Check service status and health
docker-compose -f docker-compose-local-multi-repo.yml ps
docker-compose -f docker-compose-local-multi-repo.yml top

# Inspect service details
docker-compose -f docker-compose-local-multi-repo.yml config --services
docker inspect wakedock-core

# Execute commands in containers
docker exec -it wakedock-core bash
docker exec -it wakedock-caddy sh
docker exec -it wakedock-dashboard sh

# Network debugging
docker network ls | grep caddy
docker network inspect caddy_net

# Check file structure in containers
docker exec wakedock-dashboard ls -la /app/public/
docker exec wakedock-caddy cat /etc/caddy/Caddyfile
```

## 📊 Quality Gates
- **80%+ test coverage** 
- **All services healthy in compose**
- **No container restarts**
- **Health checks pass**
- **No console errors**
- **Docker compose deployment success**
- **Caddy SSL automation working in production**

## 🚨 NON-NEGOTIABLE
1. 🐳 **ALWAYS use deploy-multi-repo.sh** - Never direct docker-compose commands
2. 🔍 **NEVER debug locally** - Container logs only
3. 🌐 **ALWAYS test via domain (mtool.ovh) or public IP** - Never localhost
4. 🔄 **ALWAYS use deploy-multi-repo.sh** after ANY change
5. 📊 **ALWAYS check service logs** after deployment
6. 🧪 **NEVER commit without multi-repo tests**
7. 🔒 **ALWAYS verify SSL in production** - Caddy auto-HTTPS must work for mtool.ovh
8. 📁 **ALWAYS work from /Docker/code/wakedock-env/WakeDock/** directory

**Goal**: Production-ready multi-repo Docker management platform with Caddy SSL automation for mtool.ovh domain.

## 🌐 URLs d'Accès
- **🚀 Interface Web**: https://mtool.ovh
- **🔐 Login**: https://mtool.ovh/login  
- **⚙️ API Backend**: https://mtool.ovh/api/v1/
- **🔍 Health Check**: https://mtool.ovh/api/v1/health
- **🔌 WebSocket**: wss://mtool.ovh/ws
- **📊 Admin Caddy**: http://IP:2019 (non-public)

## 🔧 Configuration Multi-Repo
- **Fichier principal**: `docker-compose-local-multi-repo.yml`
- **Configuration Caddy**: `caddy/Caddyfile.domain` (HTTPS avec SSL automatique)
- **Volumes persistants**: `/Docker/code/wakedock-env/WakeDock/data/`
- **Logs**: `/Docker/code/wakedock-env/WakeDock/logs/`

## 📋 TASK MANAGEMENT
- **Source**: All tasks in DESIGN_IMPROVEMENT_PLAN.md
- **Workflow**: Select task → Develop → Mark complete → Deploy/Test
- **Format**: TASK-XXX with file paths
- **Priority**: CRITICAL → HIGH → MEDIUM → LOW
- **Current**: **MAJOR PHASES COMPLETED AHEAD OF SCHEDULE** ✅

## 🎉 DEVELOPMENT PROGRESS STATUS

### ✅ Phase 1: Docker Integration (COMPLETED)
**Tasks TASK-001 to TASK-015** - **100% Complete**
- ✅ Docker client integration with caddy_net network
- ✅ Container lifecycle management (start/stop/restart)
- ✅ Container listing and resource monitoring
- ✅ Log streaming with WebSocket support
- ✅ Service CRUD operations
- ✅ Real-time service status updates

### ✅ Phase 2: Authentication & Security (COMPLETED)
**Tasks TASK-011 to TASK-013** - **100% Complete**
- ✅ JWT token validation with rotation system
- ✅ Session management with timeout handling
- ✅ Password reset functionality
- ✅ Advanced security features (IDS, rate limiting)
- ✅ Session timeout middleware
- ✅ Comprehensive security dashboard

### ✅ Phase 3: Monitoring & Observability (COMPLETED)
**Tasks TASK-016 to TASK-018** - **100% Complete**
- ✅ Real-time metrics collection with WebSocket broadcasting
- ✅ Comprehensive Prometheus metrics export
- ✅ System resource monitoring with alerts
- ✅ Docker container metrics and health checks
- ✅ Auto-shutdown based on resource usage
- ✅ Advanced monitoring dashboard

## 🚀 PRODUCTION-READY FEATURES

### 📊 Monitoring & Metrics
```bash
# System Overview
curl "http://docker-container:8000/api/v1/system/overview"

# Prometheus Metrics
curl "http://docker-container:8000/api/v1/metrics"

# Health Checks
curl "http://docker-container:8000/api/v1/health"
curl "http://docker-container:8000/api/v1/system/health"
```

### 🔐 Security Features
- JWT rotation with configurable intervals
- Session timeout management
- Intrusion detection system
- Rate limiting and IP blocking
- Security event logging
- Password reset with token validation

### 🐳 Docker Management
- Full container lifecycle management
- Real-time resource monitoring
- Log streaming with WebSocket
- Service auto-shutdown optimization
- Network management (caddy_net)
- Health check integration

### 📡 Real-time Updates
- WebSocket connections for live updates
- System metrics broadcasting
- Container status notifications
- Service health monitoring
- Resource usage alerts

## 📈 NEXT PHASE PRIORITIES
Based on current progress, potential next steps:
1. **Phase 4**: Advanced Analytics & Reporting
2. **Phase 5**: Multi-node Orchestration
3. **Phase 6**: CI/CD Pipeline Integration
4. **Phase 7**: Performance Optimization