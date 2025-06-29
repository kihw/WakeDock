#!/bin/bash

# WakeDock Dashboard Management Script
# Provides convenient commands for development and deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Helper functions
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

show_help() {
    cat << EOF
WakeDock Dashboard Management Script

Usage: $0 <command> [options]

Commands:
  setup               Set up development environment
  dev                 Start development server
  build               Build for production
  test                Run tests
  test:watch          Run tests in watch mode
  test:coverage       Run tests with coverage
  lint                Run linting
  lint:fix            Fix linting issues
  format              Format code
  type-check          Run TypeScript type checking
  clean               Clean build artifacts and dependencies
  docker:build        Build Docker image
  docker:dev          Start development with Docker
  docker:prod         Start production with Docker
  docker:test         Run tests in Docker
  docker:clean        Clean Docker resources
  deploy:staging      Deploy to staging
  deploy:prod         Deploy to production
  health              Check application health
  logs                Show application logs
  backup              Backup application data
  restore             Restore application data
  update              Update dependencies
  security            Run security audit
  performance         Run performance tests
  help                Show this help message

Examples:
  $0 setup            # Set up development environment
  $0 dev              # Start development server
  $0 test:coverage    # Run tests with coverage report
  $0 docker:build     # Build production Docker image
  $0 deploy:prod      # Deploy to production

Environment Variables:
  NODE_ENV            Set environment (development|production|test)
  API_URL            Set API URL for development
  DOCKER_TAG         Set Docker image tag
  DEPLOY_ENV         Set deployment environment

For more information, see README.md and DEPLOYMENT.md
EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    local node_version=$(node --version | sed 's/v//')
    local required_version="18.0.0"
    
    if ! [[ "$(printf '%s\n' "$required_version" "$node_version" | sort -V | head -n1)" = "$required_version" ]]; then
        log_error "Node.js version $node_version is too old. Please install Node.js 18+ first."
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed."
        exit 1
    fi
    
    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        log_info "Docker is available"
    else
        log_warning "Docker is not installed (optional for local development)"
    fi
    
    log_success "Prerequisites check passed"
}

# Setup development environment
setup() {
    log_info "Setting up development environment..."
    
    check_prerequisites
    
    # Install dependencies
    log_info "Installing dependencies..."
    npm ci
    
    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        cp .env.example .env
        log_warning "Please update .env with your configuration"
    fi
    
    # Create directories
    mkdir -p logs test-results coverage
    
    log_success "Development environment setup complete"
    log_info "Next steps:"
    log_info "1. Update .env with your configuration"
    log_info "2. Run '$0 dev' to start development server"
}

# Development server
dev() {
    log_info "Starting development server..."
    check_prerequisites
    
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating from template..."
        cp .env.example .env
    fi
    
    npm run dev
}

# Build for production
build() {
    log_info "Building for production..."
    check_prerequisites
    
    # Run type checking first
    npm run type-check
    
    # Run tests
    npm run test:run
    
    # Build
    npm run build
    
    log_success "Production build complete"
}

# Run tests
test() {
    log_info "Running tests..."
    check_prerequisites
    
    case "${1:-run}" in
        "watch")
            npm run test:watch
            ;;
        "coverage")
            npm run test:coverage
            ;;
        "run"|*)
            npm run test:run
            ;;
    esac
}

# Linting
lint() {
    log_info "Running linting..."
    check_prerequisites
    
    if [ "$1" = "fix" ]; then
        npm run lint:fix
    else
        npm run lint
    fi
}

# Format code
format() {
    log_info "Formatting code..."
    check_prerequisites
    
    npm run format
}

# Type checking
type_check() {
    log_info "Running TypeScript type checking..."
    check_prerequisites
    
    npm run type-check
}

# Clean
clean() {
    log_info "Cleaning build artifacts and dependencies..."
    
    # Remove build artifacts
    rm -rf build .svelte-kit dist coverage test-results
    
    # Remove node_modules if requested
    if [ "$1" = "all" ]; then
        rm -rf node_modules package-lock.json
        log_info "Removed node_modules and package-lock.json"
    fi
    
    # Clean Docker resources if requested
    if [ "$1" = "docker" ] || [ "$2" = "docker" ]; then
        docker_clean
    fi
    
    log_success "Cleanup complete"
}

# Docker operations
docker_build() {
    log_info "Building Docker image..."
    
    local tag="${DOCKER_TAG:-wakedock-dashboard:latest}"
    local dockerfile="${1:-Dockerfile.prod}"
    
    docker build -f "$dockerfile" -t "$tag" .
    log_success "Docker image built: $tag"
}

docker_dev() {
    log_info "Starting development environment with Docker..."
    
    docker-compose -f docker-compose.dev.yml up -d
    log_success "Development environment started"
    log_info "Dashboard: http://localhost:3000"
    log_info "Use '$0 logs' to view logs"
}

docker_prod() {
    log_info "Starting production environment with Docker..."
    
    docker-compose -f docker-compose.yml up -d
    log_success "Production environment started"
}

docker_test() {
    log_info "Running tests in Docker..."
    
    docker-compose -f docker-compose.dev.yml run --rm test-runner npm run test:run
}

docker_clean() {
    log_info "Cleaning Docker resources..."
    
    # Stop and remove containers
    docker-compose -f docker-compose.yml down -v 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    log_success "Docker resources cleaned"
}

# Deployment
deploy() {
    local env="$1"
    
    if [ -z "$env" ]; then
        log_error "Please specify deployment environment (staging|prod)"
        exit 1
    fi
    
    case "$env" in
        "staging")
            deploy_staging
            ;;
        "prod"|"production")
            deploy_production
            ;;
        *)
            log_error "Unknown environment: $env"
            exit 1
            ;;
    esac
}

deploy_staging() {
    log_info "Deploying to staging..."
    
    # Build and test
    build
    
    # Deploy with Docker
    docker_build
    
    # Push to registry (if configured)
    if [ -n "$DOCKER_REGISTRY" ]; then
        docker tag wakedock-dashboard:latest "$DOCKER_REGISTRY/wakedock-dashboard:staging"
        docker push "$DOCKER_REGISTRY/wakedock-dashboard:staging"
    fi
    
    log_success "Staging deployment complete"
}

deploy_production() {
    log_info "Deploying to production..."
    
    # Confirm production deployment
    read -p "Are you sure you want to deploy to production? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Production deployment cancelled"
        exit 0
    fi
    
    # Build and test
    build
    
    # Build production Docker image
    docker_build "Dockerfile.prod"
    
    # Tag with version
    local version=$(npm run --silent version)
    docker tag wakedock-dashboard:latest "wakedock-dashboard:$version"
    
    # Push to registry (if configured)
    if [ -n "$DOCKER_REGISTRY" ]; then
        docker tag wakedock-dashboard:latest "$DOCKER_REGISTRY/wakedock-dashboard:latest"
        docker tag wakedock-dashboard:latest "$DOCKER_REGISTRY/wakedock-dashboard:$version"
        docker push "$DOCKER_REGISTRY/wakedock-dashboard:latest"
        docker push "$DOCKER_REGISTRY/wakedock-dashboard:$version"
    fi
    
    log_success "Production deployment complete"
}

# Health check
health() {
    log_info "Checking application health..."
    
    local url="${HEALTH_URL:-http://localhost:3000/health}"
    
    if curl -f "$url" > /dev/null 2>&1; then
        log_success "Application is healthy"
    else
        log_error "Application health check failed"
        exit 1
    fi
}

# Show logs
show_logs() {
    local service="${1:-dashboard}"
    
    if docker ps --format '{{.Names}}' | grep -q "wakedock-$service"; then
        docker logs -f "wakedock-$service"
    elif [ -f "logs/$service.log" ]; then
        tail -f "logs/$service.log"
    else
        log_error "No logs found for service: $service"
        exit 1
    fi
}

# Backup data
backup() {
    log_info "Creating backup..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    if docker ps --format '{{.Names}}' | grep -q "wakedock-postgres"; then
        docker exec wakedock-postgres pg_dump -U wakedock wakedock > "$backup_dir/database.sql"
    fi
    
    # Backup configuration
    cp -r config "$backup_dir/" 2>/dev/null || true
    cp .env "$backup_dir/" 2>/dev/null || true
    
    log_success "Backup created: $backup_dir"
}

# Update dependencies
update() {
    log_info "Updating dependencies..."
    
    # Update npm dependencies
    npm update
    
    # Run security audit
    npm audit fix || log_warning "Some security issues remain"
    
    # Update Docker images
    if command -v docker &> /dev/null; then
        docker-compose pull 2>/dev/null || true
    fi
    
    log_success "Dependencies updated"
}

# Security audit
security() {
    log_info "Running security audit..."
    
    # npm audit
    npm audit
    
    # Check for outdated dependencies
    npm outdated || true
    
    log_info "Security audit complete"
}

# Main command handler
main() {
    case "${1:-help}" in
        "setup")
            setup
            ;;
        "dev")
            dev
            ;;
        "build")
            build
            ;;
        "test")
            test "$2"
            ;;
        "test:watch")
            test "watch"
            ;;
        "test:coverage")
            test "coverage"
            ;;
        "lint")
            lint "$2"
            ;;
        "lint:fix")
            lint "fix"
            ;;
        "format")
            format
            ;;
        "type-check")
            type_check
            ;;
        "clean")
            clean "$2"
            ;;
        "docker:build")
            docker_build "$2"
            ;;
        "docker:dev")
            docker_dev
            ;;
        "docker:prod")
            docker_prod
            ;;
        "docker:test")
            docker_test
            ;;
        "docker:clean")
            docker_clean
            ;;
        "deploy:staging")
            deploy "staging"
            ;;
        "deploy:prod")
            deploy "prod"
            ;;
        "health")
            health
            ;;
        "logs")
            show_logs "$2"
            ;;
        "backup")
            backup
            ;;
        "update")
            update
            ;;
        "security")
            security
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
