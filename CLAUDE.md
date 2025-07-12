## 🐳 App Overview
**WakeDock** - Docker management platform: FastAPI backend (8000), SvelteKit frontend (3000), Caddy proxy (80/443), PostgreSQL (5432), Redis (6379).

## 📁 Project Structure
```
wakedock/
├── src/wakedock/         # Backend Python FastAPI
├── dashboard/            # Frontend SvelteKit  
├── caddy/               # Reverse proxy configurations
│   ├── Caddyfile.compose # Development HTTP config
│   ├── Caddyfile.prod   # Production HTTPS config
│   └── Caddyfile.domains # Legacy swarm config
├── scripts/             # Maintenance scripts
├── docker-compose.yml   # Main orchestration file
├── deploy-compose.sh    # Primary deployment script
├── docker-swarm.yml     # Legacy swarm stack (deprecated)
└── deploy-swarm.sh      # Legacy swarm script (deprecated)
```

## 🛡️ MANDATORY RULES

### 1. 🐳 Deploy via Docker Compose ONLY
```bash
# ✅ CORRECT - ALWAYS use deploy-compose.sh
./deploy-compose.sh

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

### 4. 🔄 Docker Compose Workflow at END (MANDATORY)
```bash
# ALWAYS execute after ANY change
./deploy-compose.sh

# Development mode (HTTP only)
./deploy-compose.sh --dev

# Production mode (HTTPS with SSL)
./deploy-compose.sh --prod

# Clean deployment (rebuild everything)
./deploy-compose.sh --clean
```

## 🔧 Code Standards

### Backend (Python)
- **Async/await** mandatory for I/O
- **Type hints** required
- **Pydantic** for validation
- **FastAPI** dependency injection

### Frontend (TypeScript)
- **TypeScript** mandatory
- **Svelte reactive statements** 
- **Centralized API client**
- **Error boundaries**

### Docker
- **Health checks** in all services
- **Multi-stage builds** for production
- **Non-root users** for security

## 🧪 Testing
```bash
# Tests via Docker Compose + Public IP
export PUBLIC_IP=$(curl -s ifconfig.me)
# Deploy first
./deploy-compose.sh --dev

# Wait for services to be ready
sleep 30

# Test health endpoint
curl -f "http://${PUBLIC_IP}:80/api/v1/health"

# Test config endpoint
curl -f "http://${PUBLIC_IP}:80/api/config"

# Check all services are running
docker-compose ps
```

## 🔍 Advanced Debugging
```bash
# Debug specific service issues
docker-compose logs wakedock-core --tail 100 -f
docker-compose logs wakedock-caddy --tail 100 -f
docker-compose logs wakedock-dashboard --tail 100 -f

# Check service status and health
docker-compose ps
docker-compose top

# Inspect service details
docker-compose config --services
docker inspect wakedock-core

# Execute commands in containers
docker-compose exec wakedock-core bash
docker-compose exec wakedock-caddy caddy version

# Network debugging
docker network ls | grep caddy
docker network inspect caddy_net
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
1. 🐳 **ALWAYS use deploy-compose.sh** - Never direct docker-compose commands
2. 🔍 **NEVER debug locally** - Container logs only
3. 🌐 **NEVER test localhost** - Public IP only  
4. 🔄 **ALWAYS use deploy-compose.sh** after ANY change
5. 📊 **ALWAYS check service logs** after deployment
6. 🧪 **NEVER commit without compose tests**
7. 🔒 **ALWAYS verify SSL in production** - Caddy auto-HTTPS must work

**Goal**: Production-ready Docker Compose management platform with Caddy SSL automation.

## 📋 TASK MANAGEMENT
- **Source**: All tasks in PROJECT_COMPLETION_PLAN.md
- **Workflow**: Select task → Develop → Mark complete → Deploy/Test
- **Format**: TASK-XXX with file paths
- **Priority**: CRITICAL → HIGH → MEDIUM → LOW
- **Current**: Phase 1 Docker Integration (TASK-001 to TASK-015)