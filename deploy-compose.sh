#!/bin/bash

# WakeDock Docker Compose Deployment Script
# Modern deployment with Caddy reverse proxy and SSL automation

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🚀 $1${NC}"; }

# Parse command line arguments
CLEAN_BUILD=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help|-h)
            echo "WakeDock Deployment Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean                 Clean build (remove all containers and volumes)"
            echo "  --skip-tests           Skip endpoint testing"
            echo "  --help, -h             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Standard deployment"
            echo "  $0 --clean            # Clean deployment"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

log_step "Starting WakeDock Docker Compose deployment..."

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found. Please install docker-compose."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Load and validate environment
load_environment() {
    log_info "Loading environment configuration..."
    
    # Use single .env file
    ENV_FILE="${SCRIPT_DIR}/.env"
    
    if [ -f "${ENV_FILE}" ]; then
        log_info "Loading environment variables from ${ENV_FILE}..."
        # Load environment variables, filtering out comments, empty lines, and invalid variable names
        set -a
        source <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "${ENV_FILE}")
        set +a
    else
        log_warning "No .env file found, creating from template..."
        if [ -f "${SCRIPT_DIR}/.env.example" ]; then
            cp "${SCRIPT_DIR}/.env.example" "${ENV_FILE}"
            log_warning "Please edit ${ENV_FILE} with your configuration"
        fi
    fi
    
    log_success "Environment loaded"
}

# Create required directories and networks
setup_infrastructure() {
    log_info "Setting up infrastructure..."
    
    # Create required directories
    mkdir -p "${CADDY_DATA_DIR:-./data/caddy}" 2>/dev/null || true
    mkdir -p "${CADDY_CONFIG_DIR:-./config/caddy}" 2>/dev/null || true
    mkdir -p "${WAKEDOCK_CONFIG_DIR:-./config}" 2>/dev/null || true
    mkdir -p "${DASHBOARD_DATA_DIR:-./data/dashboard}" 2>/dev/null || true
    
    # Create Docker network if it doesn't exist
    NETWORK_NAME="${WAKEDOCK_NETWORK:-caddy_net}"
    if ! docker network ls | grep -q "${NETWORK_NAME}"; then
        log_info "Creating Docker network: ${NETWORK_NAME}"
        docker network create "${NETWORK_NAME}" || true
    fi
    
    log_success "Infrastructure setup complete"
}

# Clean existing containers and volumes
clean_deployment() {
    if [ "${CLEAN_BUILD}" = true ]; then
        log_info "Performing clean deployment..."
        
        # Stop and remove all containers
        docker-compose down --remove-orphans --volumes 2>/dev/null || true
        
        # Clean Docker system
        log_info "Cleaning Docker system..."
        docker system prune -f --volumes
        
        # Remove specific images if they exist
        docker images | grep -E "wakedock|caddy" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
        
        log_success "Clean deployment completed"
    else
        log_info "Stopping existing containers..."
        docker-compose down --remove-orphans 2>/dev/null || true
    fi
}

# Deploy services
deploy_services() {
    log_step "Building and deploying services..."
    
    log_info "Configuring services..."
    
    # Build and start services
    if [ "${CLEAN_BUILD}" = true ]; then
        docker-compose up -d --build --force-recreate
    else
        docker-compose up -d --build
    fi
    
    log_success "Services deployed"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to become healthy..."
    
    local max_wait=120
    local wait_time=0
    local services_ready=false
    
    while [ $wait_time -lt $max_wait ] && [ "$services_ready" = false ]; do
        sleep 5
        wait_time=$((wait_time + 5))
        
        # Check if all services are healthy
        if docker-compose ps | grep -E "(Up|healthy)" | wc -l | grep -q "5"; then
            services_ready=true
            log_success "All services are healthy"
        else
            log_info "Waiting for services... (${wait_time}s/${max_wait}s)"
        fi
    done
    
    if [ "$services_ready" = false ]; then
        log_warning "Some services may not be fully ready. Check logs with: docker-compose logs"
    fi
}

# Test endpoints
test_endpoints() {
    if [ "${SKIP_TESTS}" = true ]; then
        log_info "Skipping endpoint tests (--skip-tests flag)"
        return
    fi
    
    log_info "Testing endpoints..."
    
    # Get public IP
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
    BASE_URL="http://${PUBLIC_IP}:${CADDY_HTTP_PORT:-80}"
    
    # Test endpoints with retries
    test_endpoint() {
        local endpoint="$1"
        local name="$2"
        local retries=3
        
        for i in $(seq 1 $retries); do
            if curl -f -s "${BASE_URL}${endpoint}" > /dev/null 2>&1; then
                log_success "${name}: OK"
                return 0
            fi
            sleep 2
        done
        log_error "${name}: FAILED"
        return 1
    }
    
    test_endpoint "/api/config" "Config endpoint"
    test_endpoint "/api/v1/health" "Health endpoint"
}

# Display deployment summary
show_summary() {
    log_success "Deployment completed successfully!"
    echo ""
    echo "🌐 Services available at:"
    
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
    echo "  - Dashboard: http://${PUBLIC_IP}:${CADDY_HTTP_PORT:-80}"
    echo "  - API: http://${PUBLIC_IP}:${CADDY_HTTP_PORT:-80}/api/v1"
    echo "  - Config: http://${PUBLIC_IP}:${CADDY_HTTP_PORT:-80}/api/config"
    echo "  - Caddy Admin: http://${PUBLIC_IP}:${CADDY_ADMIN_PORT:-2019}"
    
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    
    echo ""
    echo "📝 Useful commands:"
    echo "  - View logs: docker-compose logs -f [service]"
    echo "  - Check status: docker-compose ps"
    echo "  - Stop services: docker-compose down"
    echo "  - Restart service: docker-compose restart <service>"
    echo "  - Access container: docker-compose exec <service> bash"
}

# Main execution
main() {
    check_prerequisites
    load_environment
    setup_infrastructure
    clean_deployment
    deploy_services
    wait_for_services
    test_endpoints
    show_summary
}

# Error handling
trap 'log_error "Deployment failed at line ${LINENO}. Check logs with: docker-compose logs"' ERR

# Run main function
main "$@"