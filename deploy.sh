#!/bin/bash

# WakeDock Unified Deployment Script
# ==================================
# Supports both production (GitHub) and development (local) modes
# with intelligent change detection and optimized builds

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
BUILD_CACHE_DIR=".build_cache"
PRODUCTION_CACHE_DIR="$BUILD_CACHE_DIR/production"
DEVELOPMENT_CACHE_DIR="$BUILD_CACHE_DIR/development"

# Default mode and options
MODE="production"
FORCE_REBUILD=false
CLEAN_BUILD=false
SKIP_TESTS=false
SKIP_CACHE_CHECK=false

# GitHub repositories
BACKEND_REPO="https://github.com/kihw/wakedock-backend.git"
FRONTEND_REPO="https://github.com/kihw/wakedock-frontend.git"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_build_info() {
    echo -e "${CYAN}[BUILD]${NC} $1"
}

print_mode_info() {
    echo -e "${PURPLE}[MODE]${NC} $1"
}

# Show help
show_help() {
    cat << EOF
🐳 WakeDock Unified Deployment Script
=====================================

Usage: $0 [MODE] [OPTIONS]

MODES:
  (default)              Production mode - build from GitHub
  --dev                  Development mode - build locally
  
OPTIONS:
  --force                Force complete rebuild
  --clean                Clean build (remove containers and volumes)
  --skip-tests           Skip endpoint testing
  --skip-cache           Skip cache checking
  --status               Show services status
  --logs                 Show logs in real-time
  --help, -h             Show this help

EXAMPLES:
  $0                     # Production deployment from GitHub
  $0 --dev               # Development deployment from local files
  $0 --force             # Force rebuild in production
  $0 --dev --clean       # Clean development build
  $0 --status            # Show current services status
  $0 --logs              # Show logs

MODES DETAILS:
  Production Mode:
    - Builds from GitHub repositories
    - Uses docker-compose-multi-repo.yml
    - Detects GitHub commits for rebuild
    - SSL enabled with Caddy for mtool.ovh
    
  Development Mode:
    - Builds from local directories
    - Uses docker-compose-local-multi-repo.yml  
    - Detects local file changes
    - HTTP configuration for local testing

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev|--development)
                MODE="development"
                shift
                ;;
            --force|--force-rebuild)
                FORCE_REBUILD=true
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-cache)
                SKIP_CACHE_CHECK=true
                shift
                ;;
            --status)
                show_status
                exit 0
                ;;
            --logs)
                show_logs
                exit 0
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Create build cache directories
create_build_cache() {
    mkdir -p "$PRODUCTION_CACHE_DIR" "$DEVELOPMENT_CACHE_DIR"
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not running"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    if [ "$MODE" = "production" ]; then
        if ! command -v git &> /dev/null; then
            print_error "Git is required for production mode"
            exit 1
        fi
        
        if ! command -v curl &> /dev/null; then
            print_error "curl is required for GitHub API access"
            exit 1
        fi
    fi
    
    print_success "Dependencies check passed"
}

# Load environment variables
load_environment() {
    print_status "Loading environment configuration..."
    
    ENV_FILE=".env"
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        print_success "Environment loaded from $ENV_FILE"
    else
        print_warning "No .env file found, using defaults"
    fi
}

# Create necessary directories and networks
setup_infrastructure() {
    print_status "Setting up infrastructure..."
    
    # Create required directories
    mkdir -p "${CADDY_DATA_DIR:-./data/caddy}" 2>/dev/null || true
    mkdir -p "${CADDY_CONFIG_DIR:-./data/caddy-config}" 2>/dev/null || true
    mkdir -p "${WAKEDOCK_CONFIG_DIR:-./config}" 2>/dev/null || true
    mkdir -p "${DASHBOARD_DATA_DIR:-./data/dashboard}" 2>/dev/null || true
    mkdir -p "${POSTGRES_DATA_DIR:-./data/postgres}" 2>/dev/null || true
    mkdir -p "${REDIS_DATA_DIR:-./data/redis}" 2>/dev/null || true
    mkdir -p "${WAKEDOCK_LOGS_DIR:-./logs}" 2>/dev/null || true
    
    # Create Docker network if it doesn't exist
    NETWORK_NAME="${WAKEDOCK_NETWORK:-caddy_net}"
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        print_status "Creating Docker network: $NETWORK_NAME"
        docker network create "$NETWORK_NAME" || true
    fi
    
    print_success "Infrastructure setup complete"
}

# Calculate hash for directory content (development mode)
calculate_directory_hash() {
    local dir="$1"
    local exclude_patterns="$2"
    
    if [ ! -d "$dir" ]; then
        echo "directory_not_found"
        return
    fi
    
    local find_cmd="find \"$dir\" -type f"
    
    # Add exclusions
    IFS=',' read -ra EXCLUDES <<< "$exclude_patterns"
    for pattern in "${EXCLUDES[@]}"; do
        find_cmd+=" ! -path \"*${pattern}*\""
    done
    
    # Calculate hash of file contents and modification times
    eval "$find_cmd" | sort | xargs ls -la 2>/dev/null | md5sum | cut -d' ' -f1
}

# Get latest commit hash from GitHub
get_github_commit_hash() {
    local repo_url="$1"
    local branch="${2:-main}"
    
    # Extract repo path from URL
    local repo_path=$(echo "$repo_url" | sed 's/https:\/\/github.com\///' | sed 's/\.git$//')
    
    # Get latest commit hash using GitHub API
    local api_url="https://api.github.com/repos/$repo_path/commits/$branch"
    local commit_hash=$(curl -s "$api_url" | grep '"sha":' | head -1 | cut -d'"' -f4)
    
    if [ -z "$commit_hash" ]; then
        print_warning "Could not fetch commit hash for $repo_path"
        echo "unknown"
    else
        echo "$commit_hash"
    fi
}

# Check if rebuild is needed
check_rebuild_needed() {
    local service="$1"
    local current_hash="$2"
    local hash_file="$3"
    
    if [ "$FORCE_REBUILD" = "true" ] || [ "$SKIP_CACHE_CHECK" = "true" ]; then
        print_build_info "🔨 Forced rebuild for $service"
        return 0
    fi
    
    if [ ! -f "$hash_file" ]; then
        print_build_info "📦 First build for $service"
        return 0
    fi
    
    local stored_hash=$(cat "$hash_file")
    
    if [ "$current_hash" != "$stored_hash" ]; then
        print_build_info "🔄 Changes detected for $service"
        print_status "  Previous: ${stored_hash:0:12}..."
        print_status "  Current:  ${current_hash:0:12}..."
        return 0
    fi
    
    print_success "✅ No changes for $service - skipping build"
    return 1
}

# Store hash after successful build
store_hash() {
    local hash="$1"
    local hash_file="$2"
    echo "$hash" > "$hash_file"
}

# Production mode: GitHub-based deployment
deploy_production() {
    print_mode_info "🚀 Production deployment from GitHub"
    
    local compose_file="docker-compose-multi-repo.yml"
    local cache_dir="$PRODUCTION_CACHE_DIR"
    
    if [ ! -f "$compose_file" ]; then
        print_error "Production compose file not found: $compose_file"
        exit 1
    fi
    
    # Get GitHub commit hashes
    print_status "📊 Checking GitHub repositories..."
    local backend_hash=$(get_github_commit_hash "$BACKEND_REPO" "main")
    local frontend_hash=$(get_github_commit_hash "$FRONTEND_REPO" "main")
    
    # Check what needs to be rebuilt
    local rebuild_backend=false
    local rebuild_frontend=false
    
    if check_rebuild_needed "backend" "$backend_hash" "$cache_dir/backend_commit_hash"; then
        rebuild_backend=true
    fi
    
    if check_rebuild_needed "frontend" "$frontend_hash" "$cache_dir/frontend_commit_hash"; then
        rebuild_frontend=true
    fi
    
    # Stop services if rebuild needed
    if [ "$rebuild_backend" = "true" ] || [ "$rebuild_frontend" = "true" ] || [ "$CLEAN_BUILD" = "true" ]; then
        print_status "🛑 Stopping services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$compose_file" down --remove-orphans
        else
            docker compose -f "$compose_file" down --remove-orphans
        fi
    fi
    
    # Clean build if requested
    if [ "$CLEAN_BUILD" = "true" ]; then
        print_status "🧹 Cleaning Docker system..."
        docker system prune -f --volumes
    fi
    
    # Build services
    local build_args=""
    if [ "$rebuild_backend" = "true" ] && [ "$rebuild_frontend" = "true" ]; then
        print_build_info "🔨 Building backend and frontend from GitHub..."
        build_args="wakedock-backend wakedock-frontend"
    elif [ "$rebuild_backend" = "true" ]; then
        print_build_info "🔨 Building backend from GitHub..."
        build_args="wakedock-backend"
    elif [ "$rebuild_frontend" = "true" ]; then
        print_build_info "🔨 Building frontend from GitHub..."
        build_args="wakedock-frontend"
    fi
    
    # Execute build and deployment
    if [ -n "$build_args" ] || [ "$CLEAN_BUILD" = "true" ]; then
        if command -v docker-compose &> /dev/null; then
            if [ "$CLEAN_BUILD" = "true" ]; then
                docker-compose -f "$compose_file" build --no-cache $build_args
            else
                docker-compose -f "$compose_file" build $build_args
            fi
            docker-compose -f "$compose_file" up -d
        else
            if [ "$CLEAN_BUILD" = "true" ]; then
                docker compose -f "$compose_file" build --no-cache $build_args
            else
                docker compose -f "$compose_file" build $build_args
            fi
            docker compose -f "$compose_file" up -d
        fi
        
        # Store successful build hashes
        if [ "$rebuild_backend" = "true" ]; then
            store_hash "$backend_hash" "$cache_dir/backend_commit_hash"
        fi
        if [ "$rebuild_frontend" = "true" ]; then
            store_hash "$frontend_hash" "$cache_dir/frontend_commit_hash"
        fi
    else
        print_success "✅ No builds needed - starting existing services"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$compose_file" up -d
        else
            docker compose -f "$compose_file" up -d
        fi
    fi
    
    print_success "🚀 Production deployment completed"
}

# Development mode: Local files-based deployment
deploy_development() {
    print_mode_info "🛠️ Development deployment from local files"
    
    local compose_file="docker-compose-local-multi-repo.yml"
    local cache_dir="$DEVELOPMENT_CACHE_DIR"
    
    if [ ! -f "$compose_file" ]; then
        print_error "Development compose file not found: $compose_file"
        exit 1
    fi
    
    # Calculate local file hashes
    print_status "📊 Analyzing local changes..."
    local backend_hash=$(calculate_directory_hash "wakedock-backend" "node_modules,.git,__pycache__,.pytest_cache,*.pyc,.venv,dist,build")
    local frontend_hash=$(calculate_directory_hash "wakedock-frontend" "node_modules,.git,.next,dist,build,.svelte-kit,*.log")
    
    # Check what needs to be rebuilt
    local rebuild_backend=false
    local rebuild_frontend=false
    
    if check_rebuild_needed "backend" "$backend_hash" "$cache_dir/backend_files_hash"; then
        rebuild_backend=true
    fi
    
    if check_rebuild_needed "frontend" "$frontend_hash" "$cache_dir/frontend_files_hash"; then
        rebuild_frontend=true
    fi
    
    # Stop services if rebuild needed
    if [ "$rebuild_backend" = "true" ] || [ "$rebuild_frontend" = "true" ] || [ "$CLEAN_BUILD" = "true" ]; then
        print_status "🛑 Stopping services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$compose_file" down --remove-orphans
        else
            docker compose -f "$compose_file" down --remove-orphans
        fi
    fi
    
    # Clean build if requested
    if [ "$CLEAN_BUILD" = "true" ]; then
        print_status "🧹 Cleaning Docker system..."
        docker system prune -f --volumes
    fi
    
    # Build services
    local build_args=""
    if [ "$rebuild_backend" = "true" ] && [ "$rebuild_frontend" = "true" ]; then
        print_build_info "🔨 Building backend and frontend locally..."
        build_args="wakedock-backend wakedock-frontend"
    elif [ "$rebuild_backend" = "true" ]; then
        print_build_info "🔨 Building backend locally..."
        build_args="wakedock-backend"
    elif [ "$rebuild_frontend" = "true" ]; then
        print_build_info "🔨 Building frontend locally..."
        build_args="wakedock-frontend"
    fi
    
    # Execute build and deployment
    if [ -n "$build_args" ] || [ "$CLEAN_BUILD" = "true" ]; then
        if command -v docker-compose &> /dev/null; then
            if [ "$CLEAN_BUILD" = "true" ]; then
                docker-compose -f "$compose_file" build --no-cache $build_args
            else
                docker-compose -f "$compose_file" build $build_args
            fi
            docker-compose -f "$compose_file" up -d
        else
            if [ "$CLEAN_BUILD" = "true" ]; then
                docker compose -f "$compose_file" build --no-cache $build_args
            else
                docker compose -f "$compose_file" build $build_args
            fi
            docker compose -f "$compose_file" up -d
        fi
        
        # Store successful build hashes
        if [ "$rebuild_backend" = "true" ]; then
            store_hash "$backend_hash" "$cache_dir/backend_files_hash"
        fi
        if [ "$rebuild_frontend" = "true" ]; then
            store_hash "$frontend_hash" "$cache_dir/frontend_files_hash"
        fi
    else
        print_success "✅ No builds needed - starting existing services"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$compose_file" up -d
        else
            docker compose -f "$compose_file" up -d
        fi
    fi
    
    print_success "🛠️ Development deployment completed"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "⏳ Waiting for services to become healthy..."
    
    local compose_file
    if [ "$MODE" = "production" ]; then
        compose_file="docker-compose-multi-repo.yml"
    else
        compose_file="docker-compose-local-multi-repo.yml"
    fi
    
    local max_wait=120
    local wait_time=0
    local services_ready=false
    
    while [ $wait_time -lt $max_wait ] && [ "$services_ready" = false ]; do
        sleep 5
        wait_time=$((wait_time + 5))
        
        # Check if all services are healthy
        local healthy_count
        if command -v docker-compose &> /dev/null; then
            healthy_count=$(docker-compose -f "$compose_file" ps | grep -E "(Up|healthy)" | wc -l)
        else
            healthy_count=$(docker compose -f "$compose_file" ps | grep -E "(Up|healthy)" | wc -l)
        fi
        
        if [ "$healthy_count" -ge 5 ]; then
            services_ready=true
            print_success "✅ All services are healthy"
        else
            print_status "⏳ Waiting for services... (${wait_time}s/${max_wait}s)"
        fi
    done
    
    if [ "$services_ready" = false ]; then
        print_warning "⚠️ Some services may not be fully ready"
    fi
}

# Test endpoints
test_endpoints() {
    if [ "$SKIP_TESTS" = "true" ]; then
        print_status "⏭️ Skipping endpoint tests"
        return
    fi
    
    print_status "🧪 Testing endpoints..."
    
    local base_url
    if [ "$MODE" = "production" ]; then
        base_url="https://mtool.ovh"
    else
        base_url="http://localhost"
    fi
    
    # Test function with retries
    test_endpoint() {
        local endpoint="$1"
        local name="$2"
        local retries=3
        
        for i in $(seq 1 $retries); do
            if curl -f -s "$base_url$endpoint" > /dev/null 2>&1; then
                print_success "✅ $name: OK"
                return 0
            fi
            sleep 2
        done
        print_warning "⚠️ $name: Not responding"
        return 1
    }
    
    test_endpoint "/api/v1/health" "Health endpoint"
    test_endpoint "/" "Frontend"
}

# Show status
show_status() {
    print_status "📊 Services Status"
    echo ""
    
    local compose_file
    if [ -f "docker-compose-multi-repo.yml" ] && [ "$MODE" = "production" ]; then
        compose_file="docker-compose-multi-repo.yml"
    elif [ -f "docker-compose-local-multi-repo.yml" ]; then
        compose_file="docker-compose-local-multi-repo.yml"
    else
        print_error "No compose file found"
        return 1
    fi
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$compose_file" ps
    else
        docker compose -f "$compose_file" ps
    fi
    
    echo ""
    print_status "🌐 Access URLs:"
    if [ "$MODE" = "production" ]; then
        echo "  🚀 Production: https://mtool.ovh"
        echo "  🔧 API: https://mtool.ovh/api/v1"
        echo "  ⚙️ Admin: https://mtool.ovh:2019"
    else
        echo "  🛠️ Development: http://localhost"
        echo "  🔧 API: http://localhost/api/v1"
        echo "  ⚙️ Admin: http://localhost:2019"
    fi
    
    echo ""
    print_status "📁 Build Cache:"
    if [ -f "$PRODUCTION_CACHE_DIR/backend_commit_hash" ]; then
        local hash=$(cat "$PRODUCTION_CACHE_DIR/backend_commit_hash")
        echo "  🐍 Backend (prod): ${hash:0:12}..."
    fi
    if [ -f "$PRODUCTION_CACHE_DIR/frontend_commit_hash" ]; then
        local hash=$(cat "$PRODUCTION_CACHE_DIR/frontend_commit_hash")
        echo "  ⚛️ Frontend (prod): ${hash:0:12}..."
    fi
    if [ -f "$DEVELOPMENT_CACHE_DIR/backend_files_hash" ]; then
        local hash=$(cat "$DEVELOPMENT_CACHE_DIR/backend_files_hash")
        echo "  🐍 Backend (dev): ${hash:0:12}..."
    fi
    if [ -f "$DEVELOPMENT_CACHE_DIR/frontend_files_hash" ]; then
        local hash=$(cat "$DEVELOPMENT_CACHE_DIR/frontend_files_hash")
        echo "  ⚛️ Frontend (dev): ${hash:0:12}..."
    fi
}

# Show logs
show_logs() {
    local compose_file
    if [ -f "docker-compose-multi-repo.yml" ] && [ "$MODE" = "production" ]; then
        compose_file="docker-compose-multi-repo.yml"
    elif [ -f "docker-compose-local-multi-repo.yml" ]; then
        compose_file="docker-compose-local-multi-repo.yml"
    else
        print_error "No compose file found"
        return 1
    fi
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$compose_file" logs -f
    else
        docker compose -f "$compose_file" logs -f
    fi
}

# Show deployment summary
show_summary() {
    print_success "🎉 Deployment completed successfully!"
    echo ""
    
    print_status "🎯 Mode: $MODE"
    print_status "🌐 Access URLs:"
    
    if [ "$MODE" = "production" ]; then
        echo "  🚀 Production: https://mtool.ovh"
        echo "  🔧 API: https://mtool.ovh/api/v1"
        echo "  ⚙️ Admin: https://mtool.ovh:2019"
    else
        echo "  🛠️ Development: http://localhost"
        echo "  🔧 API: http://localhost/api/v1"
        echo "  ⚙️ Admin: http://localhost:2019"
    fi
    
    echo ""
    print_status "📝 Useful commands:"
    echo "  📊 Check status: $0 --status"
    echo "  📋 View logs: $0 --logs"
    echo "  🔄 Redeploy: $0 $([ "$MODE" = "development" ] && echo "--dev")"
    echo "  🧹 Clean deploy: $0 --clean $([ "$MODE" = "development" ] && echo "--dev")"
    echo "  🔨 Force rebuild: $0 --force $([ "$MODE" = "development" ] && echo "--dev")"
}

# Main execution
main() {
    echo "🐳 WakeDock Unified Deployment"
    echo "=============================="
    echo ""
    
    # Parse arguments first
    parse_arguments "$@"
    
    # Show mode
    if [ "$MODE" = "production" ]; then
        print_mode_info "🚀 Production mode - building from GitHub"
    else
        print_mode_info "🛠️ Development mode - building from local files"
    fi
    
    # Execute deployment
    check_dependencies
    create_build_cache
    load_environment
    setup_infrastructure
    
    if [ "$MODE" = "production" ]; then
        deploy_production
    else
        deploy_development
    fi
    
    wait_for_services
    test_endpoints
    show_summary
}

# Error handling
trap 'print_error "Deployment failed at line ${LINENO}. Check logs with: $0 --logs"' ERR

# Run main function
main "$@"