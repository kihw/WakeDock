#!/bin/bash

# WakeDock Development Script
# Enhanced version with linting, formatting, security, and comprehensive development tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.11"
NODE_VERSION="18"
COMPOSE_FILE="docker-compose.yml"
DEV_COMPOSE_FILE="docker-compose.dev.yml"

echo -e "${BLUE}🐳 WakeDock Development Environment${NC}"
echo -e "${BLUE}====================================${NC}"

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Function to show help
show_help() {
    echo -e "${CYAN}Usage: $0 [command]${NC}"
    echo ""
    echo -e "${CYAN}Development Commands:${NC}"
    echo "  setup           - Initial setup and installation"
    echo "  install         - Install all dependencies"
    echo "  start           - Start all services"
    echo "  stop            - Stop all services"
    echo "  restart         - Restart all services"
    echo "  dev             - Start in development mode with hot-reload"
    echo "  logs            - Show logs"
    echo "  shell           - Access container shell"
    echo ""
    echo -e "${CYAN}Build Commands:${NC}"
    echo "  build           - Build Docker images"
    echo "  build-prod      - Build production images"
    echo "  clean           - Clean up containers and volumes"
    echo "  prune           - Clean up Docker system"
    echo ""
    echo -e "${CYAN}Code Quality Commands:${NC}"
    echo "  lint            - Run all linters"
    echo "  lint-py         - Run Python linting (flake8, pylint, mypy)"
    echo "  lint-js         - Run JavaScript/TypeScript linting (eslint)"
    echo "  format          - Format all code"
    echo "  format-py       - Format Python code (black, isort)"
    echo "  format-js       - Format JavaScript/TypeScript code (prettier)"
    echo "  type-check      - Run type checking"
    echo ""
    echo -e "${CYAN}Testing Commands:${NC}"
    echo "  test            - Run all tests"
    echo "  test-py         - Run Python tests"
    echo "  test-js         - Run JavaScript tests"
    echo "  test-integration - Run integration tests"
    echo "  test-e2e        - Run end-to-end tests"
    echo "  coverage        - Generate test coverage report"
    echo ""
    echo -e "${CYAN}Security Commands:${NC}"
    echo "  security        - Run all security checks"
    echo "  security-py     - Run Python security checks (bandit, safety)"
    echo "  security-js     - Run JavaScript security checks (audit)"
    echo "  security-docker - Run Docker security checks"
    echo ""
    echo -e "${CYAN}Database Commands:${NC}"
    echo "  db-migrate      - Run database migrations"
    echo "  db-reset        - Reset database"
    echo "  db-seed         - Seed database with test data"
    echo "  db-backup       - Create database backup"
    echo "  db-restore      - Restore database backup"
    echo ""
    echo -e "${CYAN}Utility Commands:${NC}"
    echo "  check           - Check development environment"
    echo "  docs            - Generate documentation"
    echo "  version         - Show version information"
    echo "  help            - Show this help"
    echo ""
}

# Environment check functions
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    log_success "Docker is running"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$PYTHON_VER" != "$PYTHON_VERSION" ]; then
        log_warning "Python version $PYTHON_VER found, recommended: $PYTHON_VERSION"
    else
        log_success "Python $PYTHON_VERSION is installed"
    fi
}

check_node() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    
    NODE_VER=$(node --version | sed 's/v//' | cut -d'.' -f1)
    if [ "$NODE_VER" -lt "$NODE_VERSION" ]; then
        log_warning "Node.js version $NODE_VER found, recommended: $NODE_VERSION+"
    else
        log_success "Node.js $NODE_VER is installed"
    fi
}

check_environment() {
    log_step "Checking development environment..."
    check_docker
    check_python
    check_node
    
    # Check for required files
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    if [ ! -f "dashboard/package.json" ]; then
        log_error "dashboard/package.json not found"
        exit 1
    fi
    
    log_success "Environment check passed"
}

# Setup and installation functions
setup() {
    log_step "Setting up development environment..."
    
    check_environment
    
    # Create necessary directories
    mkdir -p data logs caddy/data caddy/config backups temp
    
    # Copy config if not exists
    if [ ! -f "config/config.yml" ]; then
        cp config/config.example.yml config/config.yml
        log_success "Created config/config.yml from example"
    fi
    
    # Copy environment file
    if [ ! -f ".env" ]; then
        cp .env.example .env
        log_success "Created .env from example"
    fi
    
    # Set up Python environment
    setup_python_env
    
    # Set up Node.js environment
    setup_node_env
    
    # Set up pre-commit hooks
    setup_hooks
    
    log_success "Setup complete!"
}

setup_python_env() {
    log_step "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Created Python virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    log_success "Python dependencies installed"
}

setup_node_env() {
    log_step "Setting up Node.js environment..."
    
    if [ -d "dashboard" ]; then
        cd dashboard
        npm install
        cd ..
        log_success "Dashboard dependencies installed"
    fi
}

setup_hooks() {
    log_step "Setting up development hooks..."
    
    # Install pre-commit if it exists
    if [ -f ".pre-commit-config.yaml" ]; then
        source venv/bin/activate
        pre-commit install
        log_success "Pre-commit hooks installed"
    fi
}

install() {
    log_step "Installing dependencies..."
    setup_python_env
    setup_node_env
    log_success "All dependencies installed"
}

# Service management functions
start() {
    log_step "Starting WakeDock services..."
    check_docker
    
    # Create network if it doesn't exist
    docker network create wakedock-network 2>/dev/null || true
    
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        log_success "Backend is healthy"
    else
        log_warning "Backend health check failed"
    fi
    
    log_success "WakeDock started!"
    echo ""
    echo -e "${CYAN}🌐 Access points:${NC}"
    echo "  Dashboard: http://admin.localhost"
    echo "  API:       http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo ""
    echo -e "${CYAN}📊 Useful commands:${NC}"
    echo "  View logs: $0 logs"
    echo "  Stop services: $0 stop"
}

stop() {
    log_step "Stopping WakeDock services..."
    docker-compose down
    log_success "WakeDock stopped!"
}

restart() {
    log_step "Restarting WakeDock services..."
    stop
    start
}

dev() {
    log_step "Starting development mode..."
    check_docker
    
    # Set development environment variables
    export WAKEDOCK_DEBUG=true
    export WAKEDOCK_LOG_LEVEL=DEBUG
    export WAKEDOCK_RELOAD=true
    
    # Create network if it doesn't exist
    docker network create wakedock-network 2>/dev/null || true
    
    # Start services with development overrides
    if [ -f "$DEV_COMPOSE_FILE" ]; then
        docker-compose -f $COMPOSE_FILE -f $DEV_COMPOSE_FILE up -d
    else
        docker-compose up -d
    fi
    
    log_success "Development mode started!"
    echo ""
    echo -e "${CYAN}🔧 Development features enabled:${NC}"
    echo "  - Debug mode"
    echo "  - Auto-reload"
    echo "  - Verbose logging"
    echo "  - Hot module replacement"
    echo "  - API docs at http://localhost:8000/docs"
    echo ""
    echo -e "${CYAN}📊 Development commands:${NC}"
    echo "  View logs: $0 logs"
    echo "  Run tests: $0 test"
    echo "  Check code: $0 lint"
}

logs() {
    log_step "Showing logs (Ctrl+C to exit)..."
    if [ "$2" ]; then
        docker-compose logs -f "$2"
    else
        docker-compose logs -f
    fi
}

shell() {
    local service="${2:-wakedock-backend}"
    log_step "Accessing $service shell..."
    docker-compose exec "$service" /bin/bash
}

# Build functions
build() {
    log_step "Building Docker images..."
    check_docker
    docker-compose build --no-cache
    log_success "Build complete!"
}

build_prod() {
    log_step "Building production Docker images..."
    check_docker
    docker-compose -f docker-compose.prod.yml build --no-cache
    log_success "Production build complete!"
}

clean() {
    log_step "Cleaning up containers and volumes..."
    
    read -p "This will remove containers and volumes. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        log_success "Cleanup complete!"
    else
        log_warning "Cleanup cancelled"
    fi
}

prune() {
    log_step "Cleaning up Docker system..."
    
    read -p "This will remove unused Docker resources. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -f
        docker volume prune -f
        log_success "Docker system cleaned!"
    else
        log_warning "Docker cleanup cancelled"
    fi
}

# Code quality functions
lint() {
    log_step "Running all linters..."
    lint_py
    lint_js
    log_success "All linting complete!"
}

lint_py() {
    log_step "Running Python linters..."
    
    if [ ! -d "venv" ]; then
        log_error "Virtual environment not found. Run '$0 setup' first."
        return 1
    fi
    
    source venv/bin/activate
    
    log_info "Running flake8..."
    flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
    
    log_info "Running pylint..."
    pylint src/ --disable=C0114,C0115,C0116 --max-line-length=88
    
    log_info "Running mypy..."
    mypy src/ --ignore-missing-imports
    
    log_success "Python linting complete!"
}

lint_js() {
    log_step "Running JavaScript/TypeScript linters..."
    
    if [ -d "dashboard" ]; then
        cd dashboard
        log_info "Running ESLint..."
        npm run lint
        cd ..
        log_success "JavaScript linting complete!"
    else
        log_warning "Dashboard directory not found"
    fi
}

format() {
    log_step "Formatting all code..."
    format_py
    format_js
    log_success "All formatting complete!"
}

format_py() {
    log_step "Formatting Python code..."
    
    if [ ! -d "venv" ]; then
        log_error "Virtual environment not found. Run '$0 setup' first."
        return 1
    fi
    
    source venv/bin/activate
    
    log_info "Running black..."
    black src/ tests/ --line-length=88
    
    log_info "Running isort..."
    isort src/ tests/ --profile black
    
    log_success "Python formatting complete!"
}

format_js() {
    log_step "Formatting JavaScript/TypeScript code..."
    
    if [ -d "dashboard" ]; then
        cd dashboard
        log_info "Running Prettier..."
        npm run format
        cd ..
        log_success "JavaScript formatting complete!"
    else
        log_warning "Dashboard directory not found"
    fi
}

type_check() {
    log_step "Running type checking..."
    
    # Python type checking
    if [ -d "venv" ]; then
        source venv/bin/activate
        log_info "Running mypy for Python..."
        mypy src/ --ignore-missing-imports
    fi
    
    # TypeScript type checking
    if [ -d "dashboard" ]; then
        cd dashboard
        log_info "Running TypeScript compiler..."
        npm run type-check
        cd ..
    fi
    
    log_success "Type checking complete!"
}

# Testing functions
test() {
    log_step "Running all tests..."
    test_py
    test_js
    log_success "All tests complete!"
}

test_py() {
    log_step "Running Python tests..."
    
    if [ ! -d "venv" ]; then
        log_error "Virtual environment not found. Run '$0 setup' first."
        return 1
    fi
    
    source venv/bin/activate
    
    if [ -f "pytest.ini" ] || [ -d "tests" ]; then
        log_info "Running pytest..."
        python -m pytest tests/ -v --tb=short
        log_success "Python tests complete!"
    else
        log_warning "No Python tests found"
    fi
}

test_js() {
    log_step "Running JavaScript tests..."
    
    if [ -d "dashboard" ]; then
        cd dashboard
        if [ -f "package.json" ] && grep -q "\"test\"" package.json; then
            log_info "Running npm test..."
            npm test
            log_success "JavaScript tests complete!"
        else
            log_warning "No JavaScript tests configured"
        fi
        cd ..
    else
        log_warning "Dashboard directory not found"
    fi
}

test_integration() {
    log_step "Running integration tests..."
    
    # Start services if not running
    if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
        log_info "Starting services for integration tests..."
        start
        sleep 10
    fi
    
    source venv/bin/activate
    
    if [ -d "tests/integration" ]; then
        python -m pytest tests/integration/ -v --tb=short
        log_success "Integration tests complete!"
    else
        log_warning "No integration tests found"
    fi
}

test_e2e() {
    log_step "Running end-to-end tests..."
    
    # Start services if not running
    if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
        log_info "Starting services for e2e tests..."
        start
        sleep 10
    fi
    
    if [ -d "dashboard" ]; then
        cd dashboard
        if [ -f "package.json" ] && grep -q "\"test:e2e\"" package.json; then
            npm run test:e2e
            log_success "End-to-end tests complete!"
        else
            log_warning "No e2e tests configured"
        fi
        cd ..
    else
        log_warning "Dashboard directory not found"
    fi
}

coverage() {
    log_step "Generating test coverage report..."
    
    source venv/bin/activate
    
    if [ -d "tests" ]; then
        log_info "Running Python coverage..."
        python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
        log_success "Coverage report generated in htmlcov/"
    fi
    
    if [ -d "dashboard" ]; then
        cd dashboard
        if [ -f "package.json" ] && grep -q "\"test:coverage\"" package.json; then
            log_info "Running JavaScript coverage..."
            npm run test:coverage
        fi
        cd ..
    fi
    
    log_success "Coverage reports complete!"
}

# Security functions
security() {
    log_step "Running all security checks..."
    security_py
    security_js
    security_docker
    log_success "All security checks complete!"
}

security_py() {
    log_step "Running Python security checks..."
    
    source venv/bin/activate
    
    log_info "Running bandit security linter..."
    bandit -r src/ -f json -o security-report.json || true
    bandit -r src/
    
    log_info "Running safety check..."
    safety check
    
    log_success "Python security checks complete!"
}

security_js() {
    log_step "Running JavaScript security checks..."
    
    if [ -d "dashboard" ]; then
        cd dashboard
        log_info "Running npm audit..."
        npm audit
        cd ..
        log_success "JavaScript security checks complete!"
    else
        log_warning "Dashboard directory not found"
    fi
}

security_docker() {
    log_step "Running Docker security checks..."
    
    if command -v docker-bench-security &> /dev/null; then
        log_info "Running Docker Bench Security..."
        docker run --rm --net host --pid host --userns host --cap-add audit_control \
            -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
            -v /var/lib:/var/lib:ro \
            -v /var/run/docker.sock:/var/run/docker.sock:ro \
            -v /usr/lib/systemd:/usr/lib/systemd:ro \
            -v /etc:/etc:ro --label docker_bench_security \
            docker/docker-bench-security
    else
        log_warning "Docker Bench Security not installed"
    fi
    
    log_info "Running Dockerfile linting..."
    if command -v hadolint &> /dev/null; then
        hadolint Dockerfile
        hadolint Dockerfile.prod
    else
        log_warning "Hadolint not installed"
    fi
    
    log_success "Docker security checks complete!"
}

# Database functions
db_migrate() {
    log_step "Running database migrations..."
    
    if docker-compose ps | grep -q wakedock-backend; then
        docker-compose exec wakedock-backend python -m alembic upgrade head
        log_success "Database migrations complete!"
    else
        log_error "Backend service not running. Start services first."
    fi
}

db_reset() {
    log_step "Resetting database..."
    
    read -p "This will destroy all data. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down
        docker volume rm wakedock_postgres_data 2>/dev/null || true
        docker-compose up -d postgres
        sleep 10
        db_migrate
        log_success "Database reset complete!"
    else
        log_warning "Database reset cancelled"
    fi
}

db_seed() {
    log_step "Seeding database with test data..."
    
    if docker-compose ps | grep -q wakedock-backend; then
        docker-compose exec wakedock-backend python -m scripts.seed_db
        log_success "Database seeded!"
    else
        log_error "Backend service not running. Start services first."
    fi
}

db_backup() {
    log_step "Creating database backup..."
    
    local backup_file="backup-$(date +%Y%m%d-%H%M%S).sql"
    
    if docker-compose ps | grep -q postgres; then
        docker-compose exec postgres pg_dump -U wakedock wakedock > "backups/$backup_file"
        log_success "Database backup created: backups/$backup_file"
    else
        log_error "Database service not running. Start services first."
    fi
}

db_restore() {
    local backup_file="$2"
    
    if [ -z "$backup_file" ]; then
        log_error "Please specify backup file: $0 db-restore <backup-file>"
        return 1
    fi
    
    if [ ! -f "backups/$backup_file" ]; then
        log_error "Backup file not found: backups/$backup_file"
        return 1
    fi
    
    log_step "Restoring database from backup..."
    
    read -p "This will overwrite current data. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if docker-compose ps | grep -q postgres; then
            docker-compose exec -T postgres psql -U wakedock wakedock < "backups/$backup_file"
            log_success "Database restored from: backups/$backup_file"
        else
            log_error "Database service not running. Start services first."
        fi
    else
        log_warning "Database restore cancelled"
    fi
}

# Utility functions
check() {
    log_step "Checking development environment..."
    
    check_environment
    
    # Check service health
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        log_success "Backend service is healthy"
    else
        log_warning "Backend service is not responding"
    fi
    
    # Check database connection
    if docker-compose exec postgres pg_isready -U wakedock > /dev/null 2>&1; then
        log_success "Database is accessible"
    else
        log_warning "Database is not accessible"
    fi
    
    # Check for common issues
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Run '$0 setup' first."
    fi
    
    if [ ! -d "venv" ]; then
        log_warning "Python virtual environment not found. Run '$0 setup' first."
    fi
    
    log_success "Environment check complete!"
}

docs() {
    log_step "Generating documentation..."
    
    source venv/bin/activate
    
    # Generate API documentation
    if [ -d "src" ]; then
        log_info "Generating API documentation..."
        python -m pydoc-markdown -I src -m wakedock --render-toc > docs/api-reference.md
    fi
    
    # Generate code documentation
    if command -v sphinx-build &> /dev/null; then
        log_info "Building Sphinx documentation..."
        sphinx-build -b html docs/source docs/build/html
    fi
    
    log_success "Documentation generated!"
}

version() {
    log_step "Version information:"
    
    echo -e "${CYAN}WakeDock Development Environment${NC}"
    echo "================================"
    
    if [ -f "pyproject.toml" ]; then
        echo -n "Version: "
        grep -m1 version pyproject.toml | cut -d'"' -f2
    fi
    
    echo -n "Python: "
    python3 --version
    
    echo -n "Node.js: "
    node --version
    
    echo -n "Docker: "
    docker --version
    
    echo -n "Docker Compose: "
    docker-compose --version
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo ""
        echo -e "${YELLOW}Python packages:${NC}"
        pip list | head -10
    fi
}

# Main command handling
case "${1:-help}" in
    # Setup commands
    setup)
        setup
        ;;
    install)
        install
        ;;
    check)
        check
        ;;
        
    # Service management
    start)
        start
        ;;
    stop) 
        stop
        ;;
    restart)
        restart
        ;;
    dev)
        dev
        ;;
    logs)
        logs "$@"
        ;;
    shell)
        shell "$@"
        ;;
        
    # Build commands
    build)
        build
        ;;
    build-prod)
        build_prod
        ;;
    clean)
        clean
        ;;
    prune)
        prune
        ;;
        
    # Code quality
    lint)
        lint
        ;;
    lint-py)
        lint_py
        ;;
    lint-js)
        lint_js
        ;;
    format)
        format
        ;;
    format-py)
        format_py
        ;;
    format-js)
        format_js
        ;;
    type-check)
        type_check
        ;;
        
    # Testing
    test)
        test
        ;;
    test-py)
        test_py
        ;;
    test-js)
        test_js
        ;;
    test-integration)
        test_integration
        ;;
    test-e2e)
        test_e2e
        ;;
    coverage)
        coverage
        ;;
        
    # Security
    security)
        security
        ;;
    security-py)
        security_py
        ;;
    security-js)
        security_js
        ;;
    security-docker)
        security_docker
        ;;
        
    # Database
    db-migrate)
        db_migrate
        ;;
    db-reset)
        db_reset
        ;;
    db-seed)
        db_seed
        ;;
    db-backup)
        db_backup
        ;;
    db-restore)
        db_restore "$@"
        ;;
        
    # Utilities
    docs)
        docs
        ;;
    version)
        version
        ;;
    help|*)
        show_help
        ;;
esac
