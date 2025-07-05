# 🧪 TESTING & QUALITÉ - WakeDock

**Priorité: 🟡 MOYENNE**  
**Timeline: 2-3 semaines**  
**Équipe: QA Lead + Test Engineer + DevOps + Backend Dev + Frontend Dev**

## 📋 Vue d'Ensemble

Ce document détaille la stratégie complète de testing et d'amélioration de la qualité pour WakeDock. L'audit révèle une couverture de tests insuffisante, des processus CI/CD basiques, et un manque de tests d'intégration robustes nécessitant une refonte complète de la stratégie qualité.

---

## 🎯 OBJECTIFS QUALITÉ

### 📊 Métriques Cibles

```yaml
Code Coverage:
  - Unit Tests: >90% business logic
  - Integration Tests: >80% API endpoints
  - E2E Tests: >70% user journeys
  - Security Tests: 100% critical paths

Quality Gates:
  - Code Complexity: <10 cyclomatic complexity
  - Duplication: <3% code duplication
  - Security Vulnerabilities: 0 critical, <5 high
  - Performance: <200ms API P95, <3s page load

CI/CD Pipeline:
  - Build Time: <10 minutes
  - Test Execution: <15 minutes
  - Deployment Time: <5 minutes
  - Pipeline Success Rate: >95%
```

---

## 🧪 STRATÉGIE DE TESTING COMPLÈTE

### 1. Testing Pyramid Architecture

```
                    🔺 E2E Tests (10%)
                   User journeys complets
                  Browser automation tests
                 Cross-platform validation
              
              🔶 Integration Tests (20%)
             API endpoint tests complets
            Database integration tests
           Service communication tests
          External dependencies mocking
         
        🔷 Unit Tests (70%)
       Business logic pure functions
      Domain models and repositories
     Services and use cases isolation
    Component behavior verification
   Fast execution and isolation
```

### 2. Backend Testing Strategy

```python
# tests/conftest.py - Configuration globale
import pytest
import asyncio
import asyncpg
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def event_loop():
    """Event loop pour tests asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def postgres_container():
    """Container PostgreSQL pour tests"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session") 
async def redis_container():
    """Container Redis pour tests"""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis

@pytest.fixture(scope="session")
async def test_database(postgres_container):
    """Database de test isolée"""
    
    # Configuration database test
    database_url = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    
    engine = create_async_engine(database_url, echo=False)
    
    # Migrations test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_database):
    """Session database pour chaque test"""
    
    async_session = sessionmaker(
        test_database, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_client(db_session, redis_container):
    """Client HTTP test avec dependencies mockées"""
    
    from wakedock.main import app
    from wakedock.dependencies import get_database, get_cache
    
    # Override dependencies
    app.dependency_overrides[get_database] = lambda: db_session
    app.dependency_overrides[get_cache] = lambda: MockRedisClient()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Cleanup overrides
    app.dependency_overrides.clear()

# Test factories avec Faker
# tests/factories.py
import factory
from factory import Faker, LazyAttribute
from wakedock.database.models import User, Service, ServiceStatus

class UserFactory(factory.Factory):
    """Factory pour création utilisateurs test"""
    
    class Meta:
        model = User
    
    username = Faker("user_name")
    email = Faker("email")
    full_name = Faker("name")
    is_active = True
    is_verified = True
    role = "user"
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        
        from wakedock.security.auth.password import hash_password
        self.password_hash = hash_password(extracted or "testpass123")

class ServiceFactory(factory.Factory):
    """Factory pour création services test"""
    
    class Meta:
        model = Service
    
    name = Faker("slug")
    image = "nginx:latest"
    status = ServiceStatus.STOPPED
    ports = factory.LazyFunction(lambda: [{"host": 8080, "container": 80}])
    environment = factory.LazyFunction(dict)
    volumes = factory.LazyFunction(list)
    
    @factory.post_generation
    def owner(self, create, extracted, **kwargs):
        if extracted:
            self.user_id = extracted.id

# Unit Tests - Domain Models
# tests/unit/domain/test_user_model.py
import pytest
from wakedock.domain.user import User, UserRole
from wakedock.security.auth.password import verify_password

class TestUserModel:
    """Tests unitaires modèle User"""
    
    def test_user_creation(self):
        """Test création utilisateur valide"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
    
    def test_password_hashing(self):
        """Test hachage mot de passe"""
        user = User(username="test", email="test@example.com")
        user.set_password("password123")
        
        assert user.password_hash is not None
        assert user.password_hash != "password123"
        assert verify_password("password123", user.password_hash)
        assert not verify_password("wrongpassword", user.password_hash)
    
    def test_user_permissions(self):
        """Test système permissions"""
        
        # User normal
        user = User(username="user", email="user@example.com", role=UserRole.USER)
        assert not user.can_manage_users()
        assert user.can_create_services()
        
        # Admin
        admin = User(username="admin", email="admin@example.com", role=UserRole.ADMIN)
        assert admin.can_manage_users()
        assert admin.can_create_services()
        assert admin.can_access_system_settings()

# Unit Tests - Services
# tests/unit/services/test_docker_service.py
@pytest.mark.asyncio
class TestDockerService:
    """Tests unitaires service Docker"""
    
    @pytest.fixture
    def mock_docker_client(self):
        """Mock client Docker"""
        return Mock(spec=DockerClient)
    
    @pytest.fixture
    def docker_service(self, mock_docker_client, db_session):
        """Service Docker avec dépendances mockées"""
        return DockerService(
            docker_client=mock_docker_client,
            db_session=db_session,
            cache=Mock(),
            event_bus=Mock()
        )
    
    async def test_deploy_service_success(self, docker_service, mock_docker_client):
        """Test déploiement service réussi"""
        
        # Given
        service_config = ServiceConfig(
            name="test-nginx",
            image="nginx:latest",
            ports=[{"host": 8080, "container": 80}]
        )
        
        mock_container = Mock()
        mock_container.id = "container123"
        mock_docker_client.deploy_container.return_value = mock_container
        
        # When
        result = await docker_service.deploy_service(service_config)
        
        # Then
        assert result.success is True
        assert result.service.name == "test-nginx"
        assert result.service.container_id == "container123"
        assert result.service.status == ServiceStatus.RUNNING
        
        mock_docker_client.deploy_container.assert_called_once_with(service_config)
    
    async def test_deploy_service_failure(self, docker_service, mock_docker_client):
        """Test échec déploiement service"""
        
        # Given
        service_config = ServiceConfig(name="test", image="invalid:image")
        mock_docker_client.deploy_container.side_effect = DockerException("Image not found")
        
        # When & Then
        with pytest.raises(DockerException):
            await docker_service.deploy_service(service_config)
    
    async def test_service_logs_retrieval(self, docker_service, mock_docker_client):
        """Test récupération logs service"""
        
        # Given
        service_id = "service123"
        expected_logs = ["Log line 1", "Log line 2", "Log line 3"]
        mock_docker_client.get_container_logs.return_value = expected_logs
        
        # When
        logs = await docker_service.get_service_logs(service_id, lines=100)
        
        # Then
        assert logs == expected_logs
        mock_docker_client.get_container_logs.assert_called_once_with(
            service_id, lines=100
        )

# Integration Tests - API Endpoints
# tests/integration/api/test_services_api.py
@pytest.mark.integration
class TestServicesAPI:
    """Tests intégration API Services"""
    
    async def test_create_service_complete_flow(self, test_client, admin_user, db_session):
        """Test création service - flow complet"""
        
        # Login admin
        login_response = await test_client.post("/api/v1/auth/login", data={
            "username": admin_user.username,
            "password": "testpass123"
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Création service
        service_data = {
            "name": "test-webapp",
            "image": "nginx:latest",
            "ports": [{"host": 8080, "container": 80}],
            "environment": {"ENV": "test"},
            "restart_policy": "unless-stopped"
        }
        
        create_response = await test_client.post(
            "/api/v1/services",
            json=service_data,
            headers=headers
        )
        
        assert create_response.status_code == 201
        created_service = create_response.json()
        service_id = created_service["id"]
        
        # Vérification données
        assert created_service["name"] == "test-webapp"
        assert created_service["status"] == "stopped"
        assert created_service["ports"] == service_data["ports"]
        
        # Démarrage service
        start_response = await test_client.post(
            f"/api/v1/services/{service_id}/start",
            headers=headers
        )
        
        assert start_response.status_code == 200
        
        # Vérification statut
        status_response = await test_client.get(
            f"/api/v1/services/{service_id}",
            headers=headers
        )
        
        service_status = status_response.json()
        assert service_status["status"] in ["starting", "running"]
        
        # Cleanup
        await test_client.delete(f"/api/v1/services/{service_id}", headers=headers)
    
    async def test_service_permissions(self, test_client, regular_user, admin_user):
        """Test permissions service selon rôle utilisateur"""
        
        # User normal ne peut pas accéder aux services d'autres users
        user_token = await self._get_auth_token(test_client, regular_user)
        admin_token = await self._get_auth_token(test_client, admin_user)
        
        # Admin crée un service
        service_data = {"name": "admin-service", "image": "nginx:latest"}
        admin_response = await test_client.post(
            "/api/v1/services",
            json=service_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        service_id = admin_response.json()["id"]
        
        # User normal ne peut pas le voir
        user_response = await test_client.get(
            f"/api/v1/services/{service_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert user_response.status_code == 403
        
        # Admin peut le voir
        admin_view_response = await test_client.get(
            f"/api/v1/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert admin_view_response.status_code == 200
    
    async def _get_auth_token(self, client, user):
        """Helper obtention token auth"""
        response = await client.post("/api/v1/auth/login", data={
            "username": user.username,
            "password": "testpass123"
        })
        return response.json()["access_token"]

# Performance Tests
# tests/performance/test_api_performance.py
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.performance
class TestAPIPerformance:
    """Tests performance API"""
    
    async def test_concurrent_requests_performance(self, test_client, admin_token):
        """Test performance requêtes concurrentes"""
        
        async def make_request():
            start = time.time()
            response = await test_client.get(
                "/api/v1/system/overview",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            return time.time() - start, response.status_code
        
        # 50 requêtes concurrentes
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        response_times = [r[0] for r in results]
        status_codes = [r[1] for r in results]
        
        # Vérifications performance
        assert all(code == 200 for code in status_codes), "Some requests failed"
        assert statistics.mean(response_times) < 0.5, "Average response time too high"
        assert max(response_times) < 2.0, "Maximum response time too high"
        assert statistics.stdev(response_times) < 0.3, "Response time variance too high"
    
    async def test_database_query_performance(self, db_session):
        """Test performance requêtes base de données"""
        
        # Créer données test
        users = [UserFactory.build() for _ in range(100)]
        services = [ServiceFactory.build() for _ in range(500)]
        
        db_session.add_all(users + services)
        await db_session.commit()
        
        # Test requête complexe
        start = time.time()
        
        query = """
        SELECT u.username, COUNT(s.id) as service_count
        FROM users u
        LEFT JOIN services s ON u.id = s.user_id
        WHERE u.is_active = true
        GROUP BY u.id, u.username
        ORDER BY service_count DESC
        """
        
        result = await db_session.execute(text(query))
        rows = result.fetchall()
        
        query_time = time.time() - start
        
        assert query_time < 0.1, f"Query too slow: {query_time:.3f}s"
        assert len(rows) > 0, "Query returned no results"
```

---

### 3. Frontend Testing Strategy

```typescript
// tests/setup.ts - Configuration Vitest
import { vi } from 'vitest';
import { beforeAll, afterEach } from 'vitest';
import '@testing-library/jest-dom';

// Mock APIs globales
beforeAll(() => {
  // Mock fetch
  global.fetch = vi.fn();
  
  // Mock WebSocket
  global.WebSocket = vi.fn().mockImplementation(() => ({
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    send: vi.fn(),
    close: vi.fn(),
    readyState: 1
  }));
  
  // Mock IntersectionObserver
  global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn()
  }));
});

afterEach(() => {
  vi.clearAllMocks();
});

// tests/unit/components/Button.test.ts
import { render, fireEvent, screen } from '@testing-library/svelte';
import { vi } from 'vitest';
import Button from '$lib/components/ui/atoms/Button/Button.svelte';

describe('Button Component', () => {
  it('renders with correct text and variant', () => {
    render(Button, { 
      props: { 
        variant: 'primary' 
      },
      slots: {
        default: 'Click me'
      }
    });
    
    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('btn-primary');
  });
  
  it('emits click event when clicked', async () => {
    const { component } = render(Button);
    const clickSpy = vi.fn();
    
    component.$on('click', clickSpy);
    
    const button = screen.getByRole('button');
    await fireEvent.click(button);
    
    expect(clickSpy).toHaveBeenCalledTimes(1);
  });
  
  it('shows loading state correctly', () => {
    render(Button, { 
      props: { loading: true },
      slots: { default: 'Loading button' }
    });
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument(); // Loading spinner
  });
  
  it('supports all size variants', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(Button, { 
        props: { size },
        slots: { default: `${size} button` }
      });
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass(`btn-${size}`);
      
      unmount();
    });
  });
});

// tests/unit/stores/auth.test.ts
import { get } from 'svelte/store';
import { vi, beforeEach, afterEach } from 'vitest';
import { authStore } from '$lib/stores/auth';
import * as api from '$lib/api';

// Mock API
vi.mock('$lib/api', () => ({
  auth: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn()
  }
}));

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store state
    authStore.logout();
    vi.clearAllMocks();
  });
  
  it('initializes with default state', () => {
    const state = get(authStore);
    
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });
  
  it('handles successful login', async () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com'
    };
    
    const mockResponse = {
      access_token: 'fake-jwt-token',
      user: mockUser
    };
    
    vi.mocked(api.auth.login).mockResolvedValue(mockResponse);
    vi.mocked(api.auth.getCurrentUser).mockResolvedValue(mockUser);
    
    await authStore.login('testuser', 'password123');
    
    const state = get(authStore);
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe('fake-jwt-token');
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });
  
  it('handles login failure', async () => {
    const mockError = new Error('Invalid credentials');
    vi.mocked(api.auth.login).mockRejectedValue(mockError);
    
    await expect(authStore.login('wrong', 'password')).rejects.toThrow();
    
    const state = get(authStore);
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.error).toBe('Invalid credentials');
  });
  
  it('handles logout correctly', async () => {
    // Setup authenticated state
    const mockUser = { id: 1, username: 'test' };
    authStore.updateUser(mockUser);
    
    await authStore.logout();
    
    const state = get(authStore);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(api.auth.logout).toHaveBeenCalledTimes(1);
  });
});

// tests/integration/pages/dashboard.test.ts
import { render, screen, waitFor } from '@testing-library/svelte';
import { vi } from 'vitest';
import Dashboard from '../../../src/routes/+page.svelte';
import { authStore } from '$lib/stores/auth';
import { dashboardStore } from '$lib/stores/dashboard';

// Mock stores
vi.mock('$lib/stores/auth');
vi.mock('$lib/stores/dashboard');

describe('Dashboard Page', () => {
  beforeEach(() => {
    // Mock authenticated user
    vi.mocked(authStore).mockReturnValue({
      subscribe: vi.fn((callback) => {
        callback({
          user: { id: 1, username: 'admin' },
          isAuthenticated: true,
          isLoading: false,
          error: null
        });
        return () => {};
      })
    });
    
    // Mock dashboard data
    vi.mocked(dashboardStore).mockReturnValue({
      subscribe: vi.fn((callback) => {
        callback({
          data: {
            services: { total: 5, running: 3, stopped: 2 },
            system: { cpu_usage: 45, memory_usage: 60, disk_usage: 30 }
          },
          isLoading: false,
          error: null
        });
        return () => {};
      }),
      initialize: vi.fn(),
      refresh: vi.fn()
    });
  });
  
  it('renders dashboard with system overview', async () => {
    render(Dashboard);
    
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText(/5.*total/i)).toBeInTheDocument();
      expect(screen.getByText(/3.*running/i)).toBeInTheDocument();
      expect(screen.getByText(/45.*CPU/i)).toBeInTheDocument();
    });
  });
  
  it('shows loading state initially', () => {
    vi.mocked(dashboardStore).mockReturnValue({
      subscribe: vi.fn((callback) => {
        callback({
          data: null,
          isLoading: true,
          error: null
        });
        return () => {};
      }),
      initialize: vi.fn(),
      refresh: vi.fn()
    });
    
    render(Dashboard);
    
    expect(screen.getByTestId('dashboard-skeleton')).toBeInTheDocument();
  });
  
  it('handles error state', () => {
    vi.mocked(dashboardStore).mockReturnValue({
      subscribe: vi.fn((callback) => {
        callback({
          data: null,
          isLoading: false,
          error: 'Failed to load dashboard data'
        });
        return () => {};
      }),
      initialize: vi.fn(),
      refresh: vi.fn()
    });
    
    render(Dashboard);
    
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });
});
```

---

### 4. E2E Testing avec Playwright

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/e2e-results.xml' }],
    ['json', { outputFile: 'test-results/e2e-results.json' }]
  ],
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    }
  ],
  
  webServer: {
    command: 'npm run preview',
    port: 3000,
    reuseExistingServer: !process.env.CI
  }
});

// tests/e2e/auth-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });
  
  test('complete login flow', async ({ page }) => {
    // Navigate to login
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/login');
    
    // Fill login form
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'admin123');
    
    // Submit login
    await page.click('[data-testid="submit-login"]');
    
    // Verify successful login
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });
  
  test('handles invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('[data-testid="username-input"]', 'invalid');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    await page.click('[data-testid="submit-login"]');
    
    // Verify error message
    await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-error"]')).toContainText('Invalid credentials');
    
    // Verify still on login page
    await expect(page).toHaveURL('/login');
  });
  
  test('logout flow', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'admin123');
    await page.click('[data-testid="submit-login"]');
    
    // Wait for dashboard
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    
    // Open user menu and logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    
    // Verify redirected to login
    await expect(page).toHaveURL('/login');
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });
});

// tests/e2e/service-management.spec.ts
test.describe('Service Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'admin123');
    await page.click('[data-testid="submit-login"]');
    await expect(page).toHaveURL('/');
  });
  
  test('create and manage service', async ({ page }) => {
    // Navigate to services
    await page.click('[data-testid="nav-services"]');
    await expect(page).toHaveURL('/services');
    
    // Create new service
    await page.click('[data-testid="create-service-button"]');
    
    // Fill service form
    await page.fill('[data-testid="service-name"]', 'test-nginx');
    await page.fill('[data-testid="service-image"]', 'nginx:latest');
    await page.fill('[data-testid="service-port-host"]', '8080');
    await page.fill('[data-testid="service-port-container"]', '80');
    
    // Submit form
    await page.click('[data-testid="submit-service"]');
    
    // Verify service created
    await expect(page.locator('[data-testid="service-list"]')).toContainText('test-nginx');
    await expect(page.locator('[data-testid="service-status"]')).toContainText('stopped');
    
    // Start service
    await page.click('[data-testid="start-service-button"]');
    
    // Wait for status change
    await expect(page.locator('[data-testid="service-status"]')).toContainText('running');
    
    // View service logs
    await page.click('[data-testid="view-logs-button"]');
    await expect(page.locator('[data-testid="logs-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="logs-content"]')).not.toBeEmpty();
    
    // Close logs modal
    await page.click('[data-testid="close-logs"]');
    
    // Stop service
    await page.click('[data-testid="stop-service-button"]');
    await expect(page.locator('[data-testid="service-status"]')).toContainText('stopped');
    
    // Delete service
    await page.click('[data-testid="delete-service-button"]');
    await page.click('[data-testid="confirm-delete"]');
    
    // Verify service removed
    await expect(page.locator('[data-testid="service-list"]')).not.toContainText('test-nginx');
  });
  
  test('service permissions by role', async ({ page }) => {
    // Test as regular user
    await page.goto('/logout');
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'user');
    await page.fill('[data-testid="password-input"]', 'userpass');
    await page.click('[data-testid="submit-login"]');
    
    await page.goto('/services');
    
    // Regular user should see limited options
    await expect(page.locator('[data-testid="create-service-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="admin-actions"]')).not.toBeVisible();
  });
});

// tests/e2e/performance.spec.ts
test.describe('Performance Tests', () => {
  test('page load performance', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    
    // Wait for main content to load
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });
  
  test('large dataset rendering', async ({ page }) => {
    // Login and navigate to services with many items
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'admin123');
    await page.click('[data-testid="submit-login"]');
    
    const startTime = Date.now();
    await page.goto('/services');
    
    // Wait for service list to load (with 100+ services)
    await expect(page.locator('[data-testid="service-list"]')).toBeVisible();
    
    const renderTime = Date.now() - startTime;
    
    // Large list should render within 2 seconds
    expect(renderTime).toBeLessThan(2000);
  });
});
```

---

## 🚀 CI/CD PIPELINE MODERNE

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "18"
  POSTGRES_VERSION: "15"

jobs:
  # Job 1: Code Quality & Security
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev,test
      
      - name: Code formatting check
        run: poetry run black --check src tests
      
      - name: Import sorting check  
        run: poetry run isort --check-only src tests
      
      - name: Linting
        run: poetry run ruff check src tests
      
      - name: Type checking
        run: poetry run mypy src
      
      - name: Security scan
        run: poetry run bandit -r src -f json -o security-report.json
      
      - name: Upload security report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: security-report
          path: security-report.json

  # Job 2: Backend Tests
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: wakedock_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with test
      
      - name: Run unit tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/wakedock_test
          REDIS_URL: redis://localhost:6379
        run: |
          poetry run pytest tests/unit -v \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --junit-xml=test-results/unit-tests.xml
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/wakedock_test
          REDIS_URL: redis://localhost:6379
        run: |
          poetry run pytest tests/integration -v \
            --junit-xml=test-results/integration-tests.xml
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: backend-test-results
          path: |
            test-results/
            htmlcov/
            coverage.xml

  # Job 3: Frontend Tests
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: dashboard/package-lock.json
      
      - name: Install dependencies
        working-directory: dashboard
        run: npm ci
      
      - name: Lint
        working-directory: dashboard
        run: npm run lint
      
      - name: Type check
        working-directory: dashboard
        run: npm run check
      
      - name: Unit tests
        working-directory: dashboard
        run: |
          npm run test:unit -- \
            --coverage \
            --reporter=junit \
            --outputFile=test-results/unit-tests.xml
      
      - name: Build application
        working-directory: dashboard
        run: npm run build
      
      - name: Upload frontend artifacts
        uses: actions/upload-artifact@v3
        with:
          name: frontend-build
          path: dashboard/build/

  # Job 4: E2E Tests
  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: dashboard/package-lock.json
      
      - name: Install dependencies
        working-directory: dashboard
        run: npm ci
      
      - name: Install Playwright browsers
        working-directory: dashboard
        run: npx playwright install
      
      - name: Setup test environment
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 30  # Wait for services to be ready
      
      - name: Run E2E tests
        working-directory: dashboard
        run: |
          npm run test:e2e -- \
            --reporter=junit \
            --output-dir=test-results/
      
      - name: Upload E2E results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: e2e-test-results
          path: |
            dashboard/test-results/
            dashboard/playwright-report/
      
      - name: Cleanup
        if: always()
        run: docker-compose -f docker-compose.test.yml down

  # Job 5: Performance Tests
  performance-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup test environment
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 30
      
      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      
      - name: Run load tests
        run: |
          k6 run tests/performance/load-test.js \
            --out junit=test-results/performance-results.xml
      
      - name: Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun --config=.lighthouserc.js
      
      - name: Upload performance results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: performance-results
          path: test-results/

  # Job 6: Security Tests
  security-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup test environment
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 30
      
      - name: OWASP ZAP Scan
        uses: zaproxy/action-full-scan@v0.7.0
        with:
          target: 'http://localhost:3000'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a'
          issue_title: 'OWASP ZAP Security Scan'
          token: ${{ github.token }}
      
      - name: Container security scan
        run: |
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy image wakedock:latest \
            --format sarif --output trivy-results.sarif
      
      - name: Upload security scan results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: trivy-results.sarif

  # Job 7: Build & Deploy
  build-deploy:
    runs-on: ubuntu-latest
    needs: [quality-check, backend-tests, frontend-tests, e2e-tests]
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker images
        run: |
          # Backend
          docker buildx build \
            --platform linux/amd64,linux/arm64 \
            --tag ghcr.io/${{ github.repository }}/wakedock:latest \
            --tag ghcr.io/${{ github.repository }}/wakedock:${{ github.sha }} \
            --push \
            -f Dockerfile .
          
          # Frontend
          docker buildx build \
            --platform linux/amd64,linux/arm64 \
            --tag ghcr.io/${{ github.repository }}/wakedock-dashboard:latest \
            --tag ghcr.io/${{ github.repository }}/wakedock-dashboard:${{ github.sha }} \
            --push \
            -f dashboard/Dockerfile ./dashboard
      
      - name: Deploy to staging
        if: github.ref == 'refs/heads/main'
        run: |
          # Déploiement automatique en staging
          echo "Deploying to staging environment..."
          # Ici: kubectl apply, docker-compose, ou autre mécanisme de déploiement

  # Job 8: Quality Gates
  quality-gates:
    runs-on: ubuntu-latest
    needs: [quality-check, backend-tests, frontend-tests, e2e-tests, performance-tests, security-tests]
    if: always()
    
    steps:
      - name: Download test artifacts
        uses: actions/download-artifact@v3
        with:
          path: artifacts/
      
      - name: Quality Gate - Test Coverage
        run: |
          # Vérifier couverture minimale
          coverage=$(grep -oP 'line-rate="\K[^"]*' artifacts/backend-test-results/coverage.xml)
          if (( $(echo "$coverage < 0.90" | bc -l) )); then
            echo "❌ Test coverage below 90%: $coverage"
            exit 1
          fi
          echo "✅ Test coverage: $coverage"
      
      - name: Quality Gate - Performance
        run: |
          # Vérifier métriques performance
          if grep -q "failed" artifacts/performance-results/performance-results.xml; then
            echo "❌ Performance tests failed"
            exit 1
          fi
          echo "✅ Performance tests passed"
      
      - name: Quality Gate - Security
        run: |
          # Vérifier scan sécurité
          if grep -q "Critical" artifacts/security-report/security-report.json; then
            echo "❌ Critical security vulnerabilities found"
            exit 1
          fi
          echo "✅ No critical security issues"
      
      - name: Update quality badges
        if: github.ref == 'refs/heads/main'
        run: |
          # Mise à jour badges README
          echo "Updating quality badges..."
```

---

### 2. Quality Gates et Monitoring

```python
# scripts/quality-gates.py
import json
import xml.etree.ElementTree as ET
import sys
from pathlib import Path
from typing import Dict, Any, List

class QualityGate:
    """Quality Gate pour validation automatique"""
    
    def __init__(self, config_file: str = "quality-gates.json"):
        with open(config_file) as f:
            self.config = json.load(f)
        
        self.results = {}
        self.passed = True
    
    def check_test_coverage(self, coverage_file: str) -> Dict[str, Any]:
        """Vérification couverture tests"""
        
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        line_rate = float(root.get('line-rate', 0))
        branch_rate = float(root.get('branch-rate', 0))
        
        min_line_coverage = self.config['coverage']['min_line_coverage']
        min_branch_coverage = self.config['coverage']['min_branch_coverage']
        
        result = {
            "line_coverage": line_rate * 100,
            "branch_coverage": branch_rate * 100,
            "line_passed": line_rate >= min_line_coverage / 100,
            "branch_passed": branch_rate >= min_branch_coverage / 100
        }
        
        if not (result["line_passed"] and result["branch_passed"]):
            self.passed = False
        
        return result
    
    def check_performance_metrics(self, results_dir: str) -> Dict[str, Any]:
        """Vérification métriques performance"""
        
        results_path = Path(results_dir)
        
        # Lecture résultats k6
        k6_results = results_path / "k6-results.json"
        lighthouse_results = results_path / "lighthouse-results.json"
        
        performance_data = {"k6": {}, "lighthouse": {}}
        
        if k6_results.exists():
            with open(k6_results) as f:
                k6_data = json.load(f)
            
            # Métriques API
            avg_response_time = k6_data.get("metrics", {}).get("http_req_duration", {}).get("avg", 0)
            p95_response_time = k6_data.get("metrics", {}).get("http_req_duration", {}).get("p(95)", 0)
            error_rate = k6_data.get("metrics", {}).get("http_req_failed", {}).get("rate", 0)
            
            performance_data["k6"] = {
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "error_rate": error_rate,
                "passed": (
                    avg_response_time < self.config["performance"]["max_avg_response_time"] and
                    p95_response_time < self.config["performance"]["max_p95_response_time"] and
                    error_rate < self.config["performance"]["max_error_rate"]
                )
            }
        
        if lighthouse_results.exists():
            with open(lighthouse_results) as f:
                lighthouse_data = json.load(f)
            
            # Métriques frontend
            performance_score = lighthouse_data.get("categories", {}).get("performance", {}).get("score", 0)
            fcp = lighthouse_data.get("audits", {}).get("first-contentful-paint", {}).get("numericValue", 0)
            lcp = lighthouse_data.get("audits", {}).get("largest-contentful-paint", {}).get("numericValue", 0)
            
            performance_data["lighthouse"] = {
                "performance_score": performance_score * 100,
                "first_contentful_paint": fcp,
                "largest_contentful_paint": lcp,
                "passed": (
                    performance_score >= self.config["performance"]["min_lighthouse_score"] / 100 and
                    fcp <= self.config["performance"]["max_fcp"] and
                    lcp <= self.config["performance"]["max_lcp"]
                )
            }
        
        if not all(data.get("passed", True) for data in performance_data.values()):
            self.passed = False
        
        return performance_data
    
    def check_security_scan(self, security_file: str) -> Dict[str, Any]:
        """Vérification scan sécurité"""
        
        with open(security_file) as f:
            security_data = json.load(f)
        
        # Compter vulnérabilités par sévérité
        vulnerabilities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for result in security_data.get("results", []):
            for issue in result.get("issues", []):
                severity = issue.get("severity", "low").lower()
                if severity in vulnerabilities:
                    vulnerabilities[severity] += 1
        
        # Vérification limites
        max_critical = self.config["security"]["max_critical_vulnerabilities"]
        max_high = self.config["security"]["max_high_vulnerabilities"]
        
        result = {
            **vulnerabilities,
            "passed": (
                vulnerabilities["critical"] <= max_critical and
                vulnerabilities["high"] <= max_high
            )
        }
        
        if not result["passed"]:
            self.passed = False
        
        return result
    
    def check_code_quality(self, reports_dir: str) -> Dict[str, Any]:
        """Vérification qualité code"""
        
        reports_path = Path(reports_dir)
        
        # SonarQube results
        sonar_file = reports_path / "sonar-results.json"
        quality_data = {}
        
        if sonar_file.exists():
            with open(sonar_file) as f:
                sonar_data = json.load(f)
            
            # Métriques qualité
            complexity = sonar_data.get("measures", {}).get("complexity", 0)
            duplication = sonar_data.get("measures", {}).get("duplicated_lines_density", 0)
            maintainability = sonar_data.get("measures", {}).get("sqale_rating", "A")
            
            quality_data = {
                "complexity": complexity,
                "duplication": duplication,
                "maintainability_rating": maintainability,
                "passed": (
                    complexity <= self.config["code_quality"]["max_complexity"] and
                    duplication <= self.config["code_quality"]["max_duplication"] and
                    maintainability in ["A", "B"]
                )
            }
            
            if not quality_data["passed"]:
                self.passed = False
        
        return quality_data
    
    def generate_report(self) -> str:
        """Génération rapport qualité"""
        
        report = {
            "timestamp": "2024-01-15T10:30:00Z",
            "overall_status": "PASSED" if self.passed else "FAILED",
            "gates": self.results,
            "summary": {
                "total_gates": len(self.results),
                "passed_gates": sum(1 for r in self.results.values() if r.get("passed", False)),
                "failed_gates": sum(1 for r in self.results.values() if not r.get("passed", True))
            }
        }
        
        return json.dumps(report, indent=2)

# Configuration quality gates
# quality-gates.json
{
  "coverage": {
    "min_line_coverage": 90,
    "min_branch_coverage": 80
  },
  "performance": {
    "max_avg_response_time": 200,
    "max_p95_response_time": 500,
    "max_error_rate": 0.01,
    "min_lighthouse_score": 90,
    "max_fcp": 1500,
    "max_lcp": 2500
  },
  "security": {
    "max_critical_vulnerabilities": 0,
    "max_high_vulnerabilities": 5
  },
  "code_quality": {
    "max_complexity": 10,
    "max_duplication": 3.0
  }
}
```

---

## 📊 MONITORING QUALITÉ CONTINU

### Dashboards et Métriques

```python
# src/wakedock/monitoring/quality_metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

class QualityMetricsCollector:
    """Collecteur métriques qualité"""
    
    def __init__(self):
        # Métriques tests
        self.test_executions = Counter(
            'wakedock_test_executions_total',
            'Total test executions',
            ['test_type', 'status']
        )
        
        self.test_duration = Histogram(
            'wakedock_test_duration_seconds',
            'Test execution duration',
            ['test_type']
        )
        
        self.code_coverage = Gauge(
            'wakedock_code_coverage_percent',
            'Code coverage percentage',
            ['coverage_type']
        )
        
        # Métriques qualité code
        self.code_complexity = Gauge(
            'wakedock_code_complexity',
            'Code complexity metrics',
            ['component']
        )
        
        self.vulnerability_count = Gauge(
            'wakedock_vulnerabilities_total',
            'Security vulnerabilities count',
            ['severity']
        )
        
        # Métriques performance
        self.build_duration = Histogram(
            'wakedock_build_duration_seconds',
            'Build duration',
            ['stage']
        )
        
        self.deployment_success_rate = Gauge(
            'wakedock_deployment_success_rate',
            'Deployment success rate'
        )
    
    def record_test_execution(self, test_type: str, duration: float, status: str):
        """Enregistrer exécution test"""
        self.test_executions.labels(test_type=test_type, status=status).inc()
        self.test_duration.labels(test_type=test_type).observe(duration)
    
    def update_coverage(self, line_coverage: float, branch_coverage: float):
        """Mise à jour couverture"""
        self.code_coverage.labels(coverage_type='line').set(line_coverage)
        self.code_coverage.labels(coverage_type='branch').set(branch_coverage)
    
    def test_timing_decorator(self, test_type: str):
        """Décorateur timing tests"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "failure"
                    raise
                finally:
                    duration = time.time() - start_time
                    self.record_test_execution(test_type, duration, status)
            
            return wrapper
        return decorator

# Usage dans les tests
quality_metrics = QualityMetricsCollector()

@quality_metrics.test_timing_decorator("integration")
async def test_api_endpoint():
    # Test implementation
    pass
```

---

## 🚀 PLAN D'EXÉCUTION TESTING

### Phase 1 - Foundation (Semaine 1)
- [ ] Setup infrastructure testing (containers, fixtures)
- [ ] Configuration CI/CD pipeline complet
- [ ] Tests unitaires backend core (>80% coverage)
- [ ] Tests composants frontend critiques

### Phase 2 - Integration & E2E (Semaine 2)
- [ ] Tests intégration API complets
- [ ] Tests E2E user journeys principaux
- [ ] Tests performance load/stress
- [ ] Tests sécurité automatisés

### Phase 3 - Quality Gates (Semaine 2-3)
- [ ] Quality gates automatiques
- [ ] Monitoring qualité continu
- [ ] Dashboard métriques qualité
- [ ] Alerting échecs qualité

### Phase 4 - Optimisation (Semaine 3)
- [ ] Optimisation temps exécution tests
- [ ] Parallélisation tests
- [ ] Tests flaky reduction
- [ ] Documentation testing complète

---

## 📈 MÉTRIQUES SUCCÈS

```yaml
Targets Testing:
  - Unit Test Coverage: >90% business logic
  - Integration Test Coverage: >80% endpoints
  - E2E Test Coverage: >70% user journeys  
  - Test Execution Time: <15 minutes total
  - Test Flakiness Rate: <2%
  - Pipeline Success Rate: >95%

Quality Metrics:
  - Code Complexity: <10 cyclomatic average
  - Code Duplication: <3%
  - Security Vulnerabilities: 0 critical
  - Performance Regression: 0% vs baseline
  - Technical Debt Ratio: <5%

Process Metrics:
  - Deployment Frequency: Multiple/day
  - Lead Time: <4 hours
  - Mean Time to Recovery: <30 minutes
  - Change Failure Rate: <15%
```

---

**📞 Contact:** QA Team  
**📅 Review:** Daily test reports  
**🚨 Escalation:** Tech Lead pour échecs quality gates critiques**