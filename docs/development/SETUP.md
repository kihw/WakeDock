# WakeDock Development Setup

## Prerequisites

### Required Software

- **Docker** 20.10+ and Docker Compose v2
- **Python** 3.11+ (for backend development)
- **Node.js** 18+ and npm/yarn (for frontend development)
- **Git** for version control

### System Requirements

- **Linux/macOS/Windows** with WSL2
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space
- **Network**: Internet access for dependencies

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/wakedock.git
cd wakedock
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Development Mode

```bash
# Start all services in development mode
./dev.sh

# Or manually with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 4. Access Services

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Backend Development

### Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt
```

### Database Setup

```bash
# Initialize database
python manage.py init-db

# Run migrations
python manage.py migrate

# Create admin user
python manage.py create-user --admin
```

### Running Backend

```bash
# Development server with auto-reload
python manage.py dev

# Or with uvicorn directly
uvicorn wakedock.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Backend

```bash
# Run all tests
python manage.py test

# Or with pytest directly
pytest tests/

# Run specific test file
pytest tests/test_api.py

# Coverage report
pytest --cov=wakedock tests/
```

## Frontend Development

### Node.js Environment

```bash
cd dashboard

# Install dependencies
npm install
# or
yarn install
```

### Development Server

```bash
# Start development server
npm run dev
# or
yarn dev

# Build for production
npm run build
# or
yarn build
```

### Testing Frontend

```bash
# Run unit tests
npm run test
# or
yarn test

# Run e2e tests
npm run test:e2e
# or
yarn test:e2e

# Run tests in watch mode
npm run test:watch
# or
yarn test:watch
```

## Development Workflow

### Code Quality

#### Backend (Python)

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
pylint src/

# Type checking
mypy src/
```

#### Frontend (TypeScript/Svelte)

```bash
cd dashboard

# Format code
npm run format
# or
prettier --write src/

# Lint code
npm run lint
# or
eslint src/

# Type checking
npm run check
# or
svelte-check
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/your-feature-name
```

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build/tooling changes

## Database Management

### Migrations

```bash
# Generate new migration
python manage.py make-migration "Description of changes"

# Apply migrations
python manage.py migrate

# Rollback migration
python manage.py migrate --revision <revision_id>
```

### Database Operations

```bash
# Reset database (development only)
python manage.py reset-db

# Backup database
python manage.py backup

# Restore database
python manage.py restore backup.sql
```

## Docker Development

### Building Images

```bash
# Build backend image
docker build -t wakedock-api .

# Build frontend image
cd dashboard
docker build -t wakedock-dashboard .
```

### Custom Compose Overrides

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'
services:
  wakedock:
    environment:
      - DEBUG=true
    volumes:
      - ./custom-config:/app/config
```

## Configuration

### Environment Variables

#### Backend Configuration

```bash
# Database
DATABASE_URL=sqlite:///wakedock.db
# or
DATABASE_URL=postgresql://user:pass@localhost/wakedock

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key
CORS_ORIGINS=http://localhost:3000,http://localhost:4173

# Docker
DOCKER_SOCKET_PATH=/var/run/docker.sock

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=/app/logs/wakedock.log
```

#### Frontend Configuration

```bash
# API Base URL
VITE_API_BASE_URL=http://localhost:8000

# WebSocket URL
VITE_WS_URL=ws://localhost:8000/ws

# Environment
NODE_ENV=development
```

### Config Files

#### Backend (`config/config.yml`)

```yaml
wakedock:
  host: 0.0.0.0
  port: 8000
  data_path: /app/data
  debug: true

database:
  url: sqlite:///wakedock.db
  echo: false

logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

docker:
  socket_path: /var/run/docker.sock
  timeout: 60

security:
  cors_origins:
    - http://localhost:3000
    - http://localhost:4173
```

## Testing

### Backend Testing

#### Unit Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from wakedock.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

#### Integration Tests

```python
# tests/integration/test_containers.py
import pytest
from wakedock.core.orchestrator import DockerOrchestrator

@pytest.fixture
def orchestrator():
    return DockerOrchestrator()

def test_list_containers(orchestrator):
    containers = orchestrator.list_containers()
    assert isinstance(containers, list)
```

### Frontend Testing

#### Unit Tests (Vitest)

```typescript
// src/lib/utils/validation.test.ts
import { describe, it, expect } from 'vitest'
import { validateEmail } from './validation'

describe('validateEmail', () => {
  it('should validate correct email', () => {
    const result = validateEmail('test@example.com')
    expect(result.isValid).toBe(true)
  })

  it('should reject invalid email', () => {
    const result = validateEmail('invalid-email')
    expect(result.isValid).toBe(false)
  })
})
```

#### E2E Tests (Playwright)

```typescript
// tests/e2e/login.test.ts
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  await page.goto('/')
  await page.click('[data-testid=login-button]')
  await page.fill('[data-testid=username]', 'admin')
  await page.fill('[data-testid=password]', 'password')
  await page.click('[data-testid=submit]')
  await expect(page).toHaveURL('/dashboard')
})
```

## Debugging

### Backend Debugging

#### VS Code Launch Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/manage.py",
      "args": ["dev"],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

#### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_function():
    logger.debug("Debug information here")
```

### Frontend Debugging

#### Browser DevTools

- Use React DevTools for component inspection
- Network tab for API call debugging
- Console for JavaScript errors

#### VS Code Extensions

- Svelte for VS Code
- TypeScript Hero
- ESLint
- Prettier

## Performance Optimization

### Backend Performance

```python
# Use async/await for I/O operations
async def get_containers():
    async with aiohttp.ClientSession() as session:
        # Non-blocking HTTP requests
        pass

# Database query optimization
from sqlalchemy.orm import selectinload
query = select(Container).options(selectinload(Container.ports))
```

### Frontend Performance

```typescript
// Code splitting
const LazyComponent = lazy(() => import('./HeavyComponent.svelte'))

// Memoization
import { writable, derived } from 'svelte/store'
const expensiveComputation = derived(input, ($input) => {
  // Expensive calculation
  return result
})
```

## Deployment

### Local Production Build

```bash
# Build all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check dashboard
curl http://localhost:3000/

# Check all services
docker-compose ps
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### Docker Permission Issues

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Restart shell or logout/login
```

#### Database Connection Issues

```bash
# Check database file permissions
ls -la wakedock.db

# Reset database
rm wakedock.db
python manage.py init-db
```

#### Frontend Build Issues

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Contributing

### Code Review Process

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Submit pull request
6. Address review feedback
7. Merge when approved

### Documentation Updates

- Update relevant documentation
- Include API changes in docs
- Add examples for new features
- Update changelog

For more information, see the [Contributing Guide](../../CONTRIBUTING.md).
