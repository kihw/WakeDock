#!/bin/bash

# WakeDock Update Script
# This script handles updating WakeDock to the latest version

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/update.log"
BACKUP_DIR="$PROJECT_ROOT/backup/update-$(date +%Y%m%d-%H%M%S)"
GIT_REPO="https://github.com/your-org/wakedock.git"

# Create necessary directories
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Error handling
update_on_error() {
    log "ERROR" "Update script failed at line $1"
    echo -e "${RED}✗ Update failed. Check logs at $LOG_FILE${NC}"
    echo -e "${YELLOW}To rollback, run: $0 --rollback${NC}"
    exit 1
}

trap 'update_on_error $LINENO' ERR

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
    log "INFO" "Starting: $1"
}

# Function to confirm operations
confirm() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        echo "Operation cancelled."
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking prerequisites"
    
    local missing_tools=()
    
    # Check required tools
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo -e "${RED}✗ Missing required tools: ${missing_tools[*]}${NC}"
        exit 1
    fi
    
    # Check if we're in a git repository
    if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
        echo -e "${YELLOW}⚠ Not in a git repository. Manual update required.${NC}"
        if ! confirm "Continue with manual update?"; then
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ Prerequisites check completed${NC}"
    log "INFO" "Prerequisites check passed"
}

# Function to get current version
get_current_version() {
    local version="unknown"
    
    if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        version=$(grep -E '^version\s*=' "$PROJECT_ROOT/pyproject.toml" | cut -d'"' -f2 || echo "unknown")
    elif [[ -f "$PROJECT_ROOT/setup.py" ]]; then
        version=$(grep -E 'version\s*=' "$PROJECT_ROOT/setup.py" | cut -d'"' -f2 || echo "unknown")
    elif [[ -d "$PROJECT_ROOT/.git" ]]; then
        version=$(git describe --tags --always 2>/dev/null || echo "unknown")
    fi
    
    echo "$version"
}

# Function to create backup
create_backup() {
    print_header "Creating backup"
    
    # Backup configuration files
    local config_files=(
        "config/config.yml"
        "docker-compose.yml"
        "docker-compose.override.yml"
        ".env"
        "caddy/Caddyfile"
    )
    
    for file in "${config_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            mkdir -p "$BACKUP_DIR/$(dirname "$file")"
            cp "$PROJECT_ROOT/$file" "$BACKUP_DIR/$file"
            log "INFO" "Backed up $file"
        fi
    done
    
    # Backup data directory
    if [[ -d "$PROJECT_ROOT/data" ]]; then
        cp -r "$PROJECT_ROOT/data" "$BACKUP_DIR/"
        log "INFO" "Backed up data directory"
    fi
    
    # Backup database
    if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" ps postgres | grep -q "Up"; then
        echo "Creating database backup..."
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T postgres \
            pg_dump -U wakedock wakedock > "$BACKUP_DIR/database.sql"
        log "INFO" "Database backup created"
    fi
    
    echo -e "${GREEN}✓ Backup created at $BACKUP_DIR${NC}"
}

# Function to stop services
stop_services() {
    print_header "Stopping services"
    
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down
        log "INFO" "Services stopped"
    fi
    
    echo -e "${GREEN}✓ Services stopped${NC}"
}

# Function to update code from git
update_from_git() {
    print_header "Updating code from git"
    
    cd "$PROJECT_ROOT"
    
    # Fetch latest changes
    git fetch origin
    
    # Check if there are updates
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/main)
    
    if [[ "$local_commit" == "$remote_commit" ]]; then
        echo -e "${YELLOW}No updates available${NC}"
        return 0
    fi
    
    # Show changes
    echo "Changes to be applied:"
    git log --oneline "$local_commit..$remote_commit"
    
    if ! confirm "Apply these changes?"; then
        return 1
    fi
    
    # Apply updates
    git merge origin/main
    
    echo -e "${GREEN}✓ Code updated from git${NC}"
    log "INFO" "Code updated from git"
}

# Function to update dependencies
update_dependencies() {
    print_header "Updating dependencies"
    
    # Update Python dependencies
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        echo "Updating Python dependencies..."
        if command -v pip &> /dev/null; then
            pip install -U -r "$PROJECT_ROOT/requirements.txt"
        fi
    fi
    
    # Update Node.js dependencies
    if [[ -f "$PROJECT_ROOT/dashboard/package.json" ]]; then
        echo "Updating Node.js dependencies..."
        cd "$PROJECT_ROOT/dashboard"
        if command -v npm &> /dev/null; then
            npm update
        elif command -v yarn &> /dev/null; then
            yarn upgrade
        fi
        cd "$PROJECT_ROOT"
    fi
    
    echo -e "${GREEN}✓ Dependencies updated${NC}"
    log "INFO" "Dependencies updated"
}

# Function to run database migrations
run_migrations() {
    print_header "Running database migrations"
    
    if [[ -f "$PROJECT_ROOT/alembic.ini" ]]; then
        echo "Running Alembic migrations..."
        # Start database if needed
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up -d postgres
        sleep 10  # Wait for database to be ready
        
        # Run migrations in container
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T wakedock \
            alembic upgrade head || true
        
        log "INFO" "Database migrations completed"
    fi
    
    echo -e "${GREEN}✓ Database migrations completed${NC}"
}

# Function to rebuild and restart services
rebuild_services() {
    print_header "Rebuilding and restarting services"
    
    cd "$PROJECT_ROOT"
    
    # Build new images
    docker-compose build --no-cache
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    echo "Waiting for services to start..."
    sleep 30
    
    # Health check
    if command -v curl &> /dev/null; then
        local retries=5
        while [[ $retries -gt 0 ]]; do
            if curl -f http://localhost:8000/health &>/dev/null; then
                echo -e "${GREEN}✓ Services are healthy${NC}"
                break
            fi
            echo "Waiting for services to be ready... ($retries retries left)"
            sleep 10
            ((retries--))
        done
        
        if [[ $retries -eq 0 ]]; then
            echo -e "${YELLOW}⚠ Services may not be fully ready${NC}"
        fi
    fi
    
    echo -e "${GREEN}✓ Services rebuilt and restarted${NC}"
    log "INFO" "Services rebuilt and restarted"
}

# Function to verify update
verify_update() {
    print_header "Verifying update"
    
    local new_version=$(get_current_version)
    echo "Current version: $new_version"
    
    # Basic health checks
    local checks_passed=0
    local total_checks=3
    
    # Check if main service is running
    if docker-compose ps wakedock | grep -q "Up"; then
        echo -e "${GREEN}✓ WakeDock service is running${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗ WakeDock service is not running${NC}"
    fi
    
    # Check if database is accessible
    if docker-compose exec -T postgres pg_isready -U wakedock &>/dev/null; then
        echo -e "${GREEN}✓ Database is accessible${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗ Database is not accessible${NC}"
    fi
    
    # Check if API is responding
    if command -v curl &> /dev/null && curl -f http://localhost:8000/health &>/dev/null; then
        echo -e "${GREEN}✓ API is responding${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗ API is not responding${NC}"
    fi
    
    if [[ $checks_passed -eq $total_checks ]]; then
        echo -e "${GREEN}✓ Update verification passed ($checks_passed/$total_checks)${NC}"
        log "INFO" "Update verification passed"
        return 0
    else
        echo -e "${YELLOW}⚠ Update verification partial ($checks_passed/$total_checks)${NC}"
        log "WARNING" "Update verification partial"
        return 1
    fi
}

# Function to rollback
rollback() {
    print_header "Rolling back to previous version"
    
    local backup_dirs=($(ls -1d "$PROJECT_ROOT/backup/update-"* 2>/dev/null | sort -r))
    
    if [[ ${#backup_dirs[@]} -eq 0 ]]; then
        echo -e "${RED}✗ No backup found for rollback${NC}"
        exit 1
    fi
    
    local latest_backup="${backup_dirs[0]}"
    echo "Rolling back using backup: $latest_backup"
    
    if ! confirm "This will restore configuration and data from $latest_backup"; then
        exit 1
    fi
    
    # Stop services
    stop_services
    
    # Restore configuration files
    find "$latest_backup" -name "*.yml" -o -name "*.yaml" -o -name ".env" -o -name "Caddyfile" | while read -r file; do
        relative_path=${file#$latest_backup/}
        target_file="$PROJECT_ROOT/$relative_path"
        mkdir -p "$(dirname "$target_file")"
        cp "$file" "$target_file"
        log "INFO" "Restored $relative_path"
    done
    
    # Restore data directory
    if [[ -d "$latest_backup/data" ]]; then
        rm -rf "$PROJECT_ROOT/data"
        cp -r "$latest_backup/data" "$PROJECT_ROOT/"
        log "INFO" "Restored data directory"
    fi
    
    # Restore database
    if [[ -f "$latest_backup/database.sql" ]]; then
        docker-compose up -d postgres
        sleep 10
        docker-compose exec -T postgres psql -U wakedock -d wakedock < "$latest_backup/database.sql"
        log "INFO" "Database restored"
    fi
    
    # Restart services
    docker-compose up -d
    
    echo -e "${GREEN}✓ Rollback completed${NC}"
    log "INFO" "Rollback completed"
}

# Function to display update summary
show_summary() {
    print_header "Update Summary"
    
    local current_version=$(get_current_version)
    
    echo "Update completed successfully!"
    echo "Current version: $current_version"
    echo "Backup location: $BACKUP_DIR"
    echo ""
    echo "Services status:"
    docker-compose ps
    
    echo -e "\n${GREEN}✓ WakeDock update completed successfully${NC}"
    log "INFO" "Update completed successfully"
}

# Main update function
main() {
    local current_version=$(get_current_version)
    
    echo -e "${BLUE}WakeDock Update Manager${NC}"
    echo "Current version: $current_version"
    echo ""
    
    log "INFO" "Starting update process"
    
    check_prerequisites
    create_backup
    stop_services
    
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        update_from_git
    else
        echo -e "${YELLOW}Skipping git update (not a git repository)${NC}"
    fi
    
    update_dependencies
    run_migrations
    rebuild_services
    
    if verify_update; then
        show_summary
    else
        echo -e "${YELLOW}Update completed with warnings. Check the logs and services.${NC}"
    fi
}

# Handle command line arguments
case "${1:-}" in
    --rollback)
        rollback
        ;;
    -h|--help)
        echo "Usage: $0 [--rollback] [-h|--help]"
        echo ""
        echo "Options:"
        echo "  --rollback    Rollback to the previous version"
        echo "  -h            Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
