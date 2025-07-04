## 🐳 App Overview
**WakeDock** - Docker management platform: FastAPI backend (8000), SvelteKit frontend (3000), Caddy proxy (80/443), PostgreSQL (5432), Redis (6379).

## 📁 Project Structure
```
wakedock/
├── src/wakedock/         # Backend Python FastAPI
├── dashboard/            # Frontend SvelteKit  
├── caddy/               # Reverse proxy config
├── scripts/             # Maintenance scripts
└── docker-compose.yml   # Orchestration
```

## 🛡️ MANDATORY RULES

### 1. 🐳 Debug via Docker ONLY
```bash
# ✅ CORRECT
docker-compose exec wakedock python -c "import wakedock"
docker-compose logs -f wakedock

# ❌ NEVER
python src/wakedock/main.py
```

### 2. 🌐 Test via Public IP ONLY  
```bash
# ✅ CORRECT
curl "http://YOUR_PUBLIC_IP:8000/api/v1/health"

# ❌ NEVER  
curl "http://localhost:8000/health"
```

### 3. 🔄 Docker Workflow at END (MANDATORY)
```bash
# ALWAYS execute after ANY change
docker-compose down
docker-compose build --no-cache  
docker-compose up -d
./scripts/health-check.sh
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
# Tests via Docker + Public IP
export PUBLIC_IP=$(curl -s ifconfig.me)
docker-compose exec wakedock pytest
curl -f "http://${PUBLIC_IP}:8000/health"
```

## 📊 Quality Gates
- **80%+ test coverage** 
- **Health checks pass**
- **No console errors**
- **Docker build success**

## 🚨 NON-NEGOTIABLE
1. 🐳 **NEVER debug locally** - Docker only
2. 🌐 **NEVER test localhost** - Public IP only  
3. 🔄 **ALWAYS full Docker workflow** at end
4. 📊 **ALWAYS health check** after changes
5. 🧪 **NEVER commit without tests**

**Goal**: Production-ready Docker management platform.