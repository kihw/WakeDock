# 🛡️ RÈGLES STRICTES DE DÉVELOPPEMENT - WAKEDOCK

## 📋 APERÇU DU PROJE### 3. 🌐 TESTS VIA DOMAINE CADDY CONFIGURÉ UNIQUEMENT
```bash
# ✅ CORRECT - Tests via domaine Caddy configuré
# Utiliser la variable DOMAIN du fichier .env
curl "http://${DOMAIN}/api/v1/health"
curl "http://${DOMAIN}/"

# ✅ CORRECT - Alternative avec IP publique si pas de domaine
export PUBLIC_IP=$(curl -s ifconfig.me)
curl "http://${PUBLIC_IP}:80/api/v1/health"
curl "http://${PUBLIC_IP}:80/"

# ❌ INTERDIT - Tests locaux bypass Caddy
curl "http://localhost:8000"
curl "http://127.0.0.1:3000"
curl "http://wakedock-*:*"
```** - Plateforme de gestion Docker moderne avec : Backend FastAPI (8000), Frontend SvelteKit (3000), Proxy Caddy (80/443), PostgreSQL (5432), Redis (6379).

## 🏗️ ARCHITECTURE STRICTE

### 🎯 STACK TECHNOLOGIQUE OBLIGATOIRE
```yaml
Backend:
  - FastAPI 0.104+ (ASYNC/AWAIT UNIQUEMENT)
  - Python 3.8-3.12 (Type hints OBLIGATOIRES)
  - SQLAlchemy 2.0+ (ORM ASYNC)
  - Pydantic 2.5+ (Validation stricte)
  - PostgreSQL 15+ (Production)
  - Redis 5.0+ (Cache/Sessions)

Frontend:
  - SvelteKit (SSR/SPA hybride)
  - TypeScript STRICT MODE UNIQUEMENT
  - Vite (Build/Dev server)
  - TailwindCSS (Styling atomique)
  - Lucide Icons (Cohérence visuelle)

Infrastructure:
  - Docker Compose v2 UNIQUEMENT
  - Caddy 2+ (Reverse proxy/SSL)
  - Linux containers UNIQUEMENT
```

## 🚨 RÈGLES NON-NÉGOCIABLES

### 1. 🐳 DÉPLOIEMENT DOCKER COMPOSE EXCLUSIF
```bash
# ✅ CORRECT - TOUJOURS utiliser deploy-compose.sh
./deploy-compose.sh

# ✅ DÉVELOPPEMENT
./deploy-compose.sh --dev

# ✅ PRODUCTION
./deploy-compose.sh --prod

# ✅ NETTOYAGE COMPLET
./deploy-compose.sh --clean

# ❌ INTERDIT - Commandes directes
docker-compose up -d
docker compose up -d
docker run ...
docker build ...
```

### 2. 🔍 DEBUG VIA LOGS CONTAINERS UNIQUEMENT
```bash
# ✅ CORRECT - Logs des services
docker-compose logs wakedock-core -f
docker-compose logs wakedock-postgres -f
docker-compose logs wakedock-redis -f
docker-compose logs wakedock-caddy -f
docker-compose logs wakedock-dashboard -f

# ✅ CORRECT - Vue d'ensemble
docker-compose ps
docker-compose top

# ❌ INTERDIT - Debug local
python src/wakedock/main.py
npm run dev
curl localhost:8000
```

### 3. 🌐 TESTS VIA IP PUBLIQUE UNIQUEMENT
```bash
# ✅ CORRECT - Tests sur IP publique
export PUBLIC_IP=$(curl -s ifconfig.me)
curl "http://${PUBLIC_IP}:80/api/v1/health"
curl "http://${PUBLIC_IP}:80/"

# ❌ INTERDIT - Tests locaux
curl "http://localhost:8000"
curl "http://127.0.0.1:3000"
curl "http://wakedock-core:8000"
```

### 4. 🔄 WORKFLOW OBLIGATOIRE APRÈS CHANGEMENTS
```bash
# SÉQUENCE OBLIGATOIRE après TOUT changement
1. ./deploy-compose.sh --clean
2. Attendre 60 secondes
3. docker-compose ps (vérifier tous services UP)
4. docker-compose logs -f (vérifier absence d'erreurs)
5. curl "http://${DOMAIN}/api/v1/health" ou curl "http://${PUBLIC_IP}:80/api/v1/health"
6. Tests fonctionnels complets
```

## 📝 STANDARDS DE CODE STRICTS

### 🐍 BACKEND PYTHON - RÈGLES ABSOLUES

#### Type Hints Obligatoires
```python
# ✅ CORRECT
async def create_service(
    service_data: ServiceCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db_session)
) -> ServiceResponse:
    pass

# ❌ INTERDIT
def create_service(service_data, user, db):
    pass
```

#### Async/Await Obligatoire pour I/O
```python
# ✅ CORRECT
async def get_services(db: AsyncSession) -> List[Service]:
    result = await db.execute(select(Service))
    return result.scalars().all()

# ❌ INTERDIT
def get_services(db: Session):
    return db.query(Service).all()
```

#### Validation Pydantic Stricte
```python
# ✅ CORRECT
class ServiceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    image: str = Field(..., regex=r'^[a-zA-Z0-9\-_\/\.]+:[a-zA-Z0-9\-_\.]+$')
    ports: List[PortConfig] = Field(default_factory=list)
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

# ❌ INTERDIT
class ServiceCreateRequest(BaseModel):
    name: str
    image: str
```

#### Gestion d'Erreurs Centralisée
```python
# ✅ CORRECT
from wakedock.api.middleware.error_handler import WakeDockException

async def delete_service(service_id: str) -> None:
    try:
        service = await get_service_by_id(service_id)
        if not service:
            raise WakeDockException(
                message="Service not found",
                error_code="SERVICE_NOT_FOUND",
                status_code=404
            )
        await docker_client.remove_container(service.container_id)
    except DockerException as e:
        raise WakeDockException(
            message="Failed to remove container",
            error_code="DOCKER_ERROR",
            status_code=500,
            details=str(e)
        )

# ❌ INTERDIT
def delete_service(service_id):
    service = get_service(service_id)
    if not service:
        return {"error": "not found"}
```

### 🎨 FRONTEND TYPESCRIPT - RÈGLES ABSOLUES

#### TypeScript Strict Mode
```typescript
// ✅ CORRECT - tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noImplicitThis": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}

// ✅ CORRECT - Types explicites
interface Service {
  readonly id: string;
  readonly name: string;
  readonly status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  readonly ports: ReadonlyArray<Port>;
  readonly environment: ReadonlyMap<string, string>;
}

// ❌ INTERDIT
let service: any;
function getData(): any {}
```

#### Architecture de Composants Atomique
```typescript
// ✅ CORRECT - Structure modulaire
src/lib/components/
├── ui/
│   ├── atoms/          # Composants de base
│   │   ├── Button.svelte
│   │   ├── Input.svelte
│   │   └── Badge.svelte
│   ├── molecules/      # Combinaisons d'atomes
│   │   ├── ServiceForm.svelte
│   │   └── DataTable.svelte
│   └── organisms/      # Sections complexes
│       ├── Dashboard.svelte
│       └── ServiceList.svelte
├── layout/             # Mise en page
└── features/           # Fonctionnalités métier
```

#### Stores Svelte Typés
```typescript
// ✅ CORRECT
interface ServiceState {
  readonly services: ReadonlyArray<Service>;
  readonly loading: boolean;
  readonly error: string | null;
}

const { subscribe, update, set } = writable<ServiceState>({
  services: [],
  loading: false,
  error: null
});

export const serviceStore = {
  subscribe,
  async loadServices(): Promise<void> {
    update(state => ({ ...state, loading: true, error: null }));
    try {
      const services = await api.getServices();
      update(state => ({ ...state, services, loading: false }));
    } catch (error) {
      update(state => ({ 
        ...state, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Unknown error'
      }));
    }
  }
};

// ❌ INTERDIT
const serviceStore = writable({});
```

### 🛠️ DOCKER ET INFRASTRUCTURE

#### Dockerfile Multi-stage Obligatoire
```dockerfile
# ✅ CORRECT
FROM python:3.11-slim as base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["uvicorn", "wakedock.main:app", "--host", "0.0.0.0", "--reload"]

FROM base as production
COPY . .
RUN adduser --disabled-password --gecos '' appuser
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python /app/health_check.py
CMD ["uvicorn", "wakedock.main:app", "--host", "0.0.0.0", "--workers", "4"]

# ❌ INTERDIT
FROM python:3.11
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

#### Health Checks Obligatoires
```yaml
# ✅ CORRECT - docker-compose.yml
services:
  wakedock:
    healthcheck:
      test: ["CMD", "python", "/app/health_check.py"]
      interval: 15s
      timeout: 10s
      retries: 3
      start_period: 45s
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

# ❌ INTERDIT
services:
  wakedock:
    depends_on:
      - postgres
      - redis
```

## 🔒 SÉCURITÉ STRICTE

### Authentication & Authorization
```python
# ✅ CORRECT - JWT avec rotation obligatoire
@router.post("/auth/login")
async def login(
    credentials: UserLogin,
    request: Request,
    session_service: SessionTimeoutService = Depends(get_session_timeout_service)
) -> TokenResponse:
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        await audit_service.log_failed_login(request.client.host, credentials.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = await jwt_manager.create_access_token(user.id)
    refresh_token = await jwt_manager.create_refresh_token(user.id)
    
    await session_service.create_session(user.id, request.client.host)
    await audit_service.log_successful_login(user.id, request.client.host)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt.access_token_expire_minutes * 60
    )
```

### Rate Limiting Obligatoire
```python
# ✅ CORRECT - Configuration rate limiting
RATE_LIMIT_RULES = {
    'auth:login': RateLimitRule(requests=5, window=300),        # 5 tentatives/5min
    'service:create': RateLimitRule(requests=10, window=60),    # 10 créations/min
    'service:start_stop': RateLimitRule(requests=20, window=60), # 20 actions/min
    'api:general': RateLimitRule(requests=100, window=60)       # 100 req/min
}
```

## 📊 TESTS ET QUALITÉ

### Coverage Obligatoire
```bash
# ✅ Seuils minimums
Backend: >= 85% coverage
Frontend: >= 80% coverage
Integration: >= 90% des endpoints critiques
E2E: >= 95% des workflows utilisateur principaux
```

### Tests Structure
```python
# ✅ CORRECT - Tests backend
tests/
├── unit/
│   ├── test_services.py
│   ├── test_auth.py
│   └── test_docker_client.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_database.py
└── e2e/
    ├── test_service_lifecycle.py
    └── test_user_workflows.py

# ✅ CORRECT - Tests frontend  
dashboard/tests/
├── unit/
│   ├── components/
│   └── stores/
├── integration/
│   └── api/
└── e2e/
    └── workflows/
```

## 🔄 CI/CD PIPELINE STRICT

### Pre-commit Hooks Obligatoires
```yaml
# ✅ .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      
  - repo: https://github.com/psf/black
    hooks:
      - id: black
      
  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
      
  - repo: https://github.com/pycqa/flake8
    hooks:
      - id: flake8
```

### Pipeline GitHub Actions
```yaml
# ✅ CORRECT - .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Backend
        run: |
          ./deploy-compose.sh --dev
          sleep 60
          docker-compose exec -T wakedock-core pytest --cov=wakedock --cov-report=xml
          
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Frontend
        run: |
          cd dashboard
          npm ci
          npm run test:coverage
          npm run build
          
  integration-tests:
    needs: [backend-tests, frontend-tests]
    runs-on: ubuntu-latest
    steps:
      - name: Full Stack Tests
        run: |
          ./deploy-compose.sh --prod
          sleep 90
          export PUBLIC_IP=$(curl -s ifconfig.me)
          pytest tests/e2e/ --base-url="http://${PUBLIC_IP}"
```

## 🚫 INTERDICTIONS ABSOLUES

### 🚨 CODE INTERDIT
```bash
# ❌ DÉVELOPPEMENT LOCAL
python main.py
npm run dev
flask run
node server.js

# ❌ TESTS LOCALHOST
curl localhost:*
wget 127.0.0.1:*
http://wakedock-*:*

# ❌ COMMANDES DOCKER DIRECTES
docker run
docker build
docker exec
docker-compose up (sans deploy-compose.sh)

# ❌ MODIFICATIONS MANUELLES
vim docker-compose.yml (en production)
edit /etc/caddy/Caddyfile
systemctl restart docker
```

### 🚨 PATTERNS CODE INTERDITS
```python
# ❌ BACKEND
def func():                    # Pas de type hints
try: pass except: pass         # Exception catching générique
time.sleep()                   # Blocking I/O
threading.Thread()             # Pas de threads manuels
os.system()                    # Commands système dangereuses

# ❌ FRONTEND
any, unknown types             # Types non stricts
@ts-ignore                     # Suppression d'erreurs TS
innerHTML = userInput          // XSS vulnerability
eval(), Function()             // Code execution
```

## ✅ VALIDATION CONTINUE

### Checklist Obligatoire AVANT Commit
```bash
# 1. Tests locaux
./scripts/run-tests.sh

# 2. Déploiement propre
./deploy-compose.sh --clean

# 3. Vérification santé
docker-compose ps | grep -v Up && echo "FAILED" || echo "OK"

# 4. Tests endpoints
export DOMAIN=$(grep DOMAIN .env | cut -d'=' -f2)
curl -f "http://${DOMAIN}/api/v1/health" || echo "HEALTH FAILED"

# 5. Vérification logs
docker-compose logs --tail 100 | grep -i error && echo "ERRORS FOUND"

# 6. Performance check
export DOMAIN=$(grep DOMAIN .env | cut -d'=' -f2)
curl -w "%{time_total}" -s "http://${DOMAIN}/" -o /dev/null
```

### Métriques Qualité Obligatoires
```yaml
Code Quality Gates:
  - Couverture tests: Backend ≥85%, Frontend ≥80%
  - Complexité cyclomatique: ≤10 par fonction
  - Duplication code: ≤3%
  - Dépendances vulnérables: 0
  - Temps réponse API: ≤200ms (95e percentile)
  - Temps chargement page: ≤2s
  - Score Lighthouse: ≥90
  - Accessibility: WCAG 2.1 AA
```

## 🎯 OBJECTIF FINAL
**Plateforme Docker robuste, sécurisée et performante avec déploiement Docker Compose exclusif, SSL automatique via Caddy, et surveillance continue de la qualité.**

---

## 🔗 LIENS RAPIDES
- **Déploiement**: `./deploy-compose.sh --help`
- **Logs**: `docker-compose logs -f`
- **Santé**: `export DOMAIN=$(grep DOMAIN .env | cut -d'=' -f2) && curl http://${DOMAIN}/api/v1/health`
- **Tests**: `pytest tests/` + `npm test`
- **Documentation**: `/docs/`

**⚠️ VIOLATION DE CES RÈGLES = REFUS AUTOMATIQUE DE LA PR**
