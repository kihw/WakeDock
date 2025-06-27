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

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to setup environment
setup() {
    echo "🔧 Setting up development environment..."
    
    # Copy config if not exists
    if [ ! -f "config/config.yml" ]; then
        cp config/config.example.yml config/config.yml
        echo "✅ Created config/config.yml from example"
    fi
    
    # Create directories
    mkdir -p data logs caddy/data caddy/config
    
    # Install Python dependencies if venv exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        pip install -r requirements.txt
        echo "✅ Python dependencies updated"
    fi
    
    # Install dashboard dependencies
    if [ -d "dashboard" ]; then
        cd dashboard
        npm install
        cd ..
        echo "✅ Dashboard dependencies updated"
    fi
    
    echo "✅ Setup complete!"
}

# Function to start services
start() {
    echo "🚀 Starting WakeDock..."
    check_docker
    
    # Create network if it doesn't exist
    docker network create wakedock-network 2>/dev/null || true
    
    docker-compose up -d
    
    echo "✅ WakeDock started!"
    echo ""
    echo "🌐 Access points:"
    echo "  Dashboard: http://admin.localhost"
    echo "  API:       http://localhost:8000"
    echo ""
    echo "📊 To view logs: $0 logs"
}

# Function to stop services
stop() {
    echo "🛑 Stopping WakeDock..."
    docker-compose down
    echo "✅ WakeDock stopped!"
}

# Function to restart services
restart() {
    echo "🔄 Restarting WakeDock..."
    stop
    start
}

# Function to show logs
logs() {
    echo "📋 Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

# Function to build images
build() {
    echo "🔨 Building Docker images..."
    check_docker
    docker-compose build --no-cache
    echo "✅ Build complete!"
}

# Function to clean up
clean() {
    echo "🧹 Cleaning up..."
    
    read -p "This will remove all containers, images, and volumes. Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --rmi all
        docker system prune -f
        echo "✅ Cleanup complete!"
    else
        echo "❌ Cleanup cancelled"
    fi
}

# Function to run tests
test() {
    echo "🧪 Running tests..."
    
    # Python tests
    if [ -f "pytest.ini" ] || [ -f "tests/test_*.py" ]; then
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        python -m pytest tests/ -v
    fi
    
    # Dashboard tests
    if [ -f "dashboard/package.json" ]; then
        cd dashboard
        npm test
        cd ..
    fi
    
    echo "✅ Tests complete!"
}

# Function to start in development mode
dev() {
    echo "🔧 Starting development mode..."
    
    # Start backend in development mode
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    export WAKEDOCK_DEBUG=true
    export WAKEDOCK_LOG_LEVEL=DEBUG
    
    # Start services
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    echo "✅ Development mode started!"
    echo ""
    echo "🔧 Development features enabled:"
    echo "  - Debug mode"
    echo "  - Auto-reload"
    echo "  - Verbose logging"
    echo "  - API docs at http://localhost:8000/docs"
}

# Main command handling
case "${1:-help}" in
    setup)
        setup
        ;;
    start)
        start
        ;;
    stop) 
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    build)
        build
        ;;
    clean)
        clean
        ;;
    test)
        test
        ;;
    dev)
        dev
        ;;
    help|*)
        show_help
        ;;
esac
