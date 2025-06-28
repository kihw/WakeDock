#!/bin/bash

# WakeDock System Cleanup Script
# This script cleans up temporary files, logs, and unused Docker resources

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
LOG_FILE="$PROJECT_ROOT/logs/cleanup.log"
BACKUP_RETENTION_DAYS=30
LOG_RETENTION_DAYS=7

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Error handling
cleanup_on_error() {
    log "ERROR" "Cleanup script failed at line $1"
    exit 1
}

trap 'cleanup_on_error $LINENO' ERR

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
    log "INFO" "Starting: $1"
}

# Function to confirm dangerous operations
confirm() {
    local message="$1"
    local default="${2:-n}"
    
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

# Function to clean old log files
clean_logs() {
    print_header "Cleaning old log files"
    
    local log_dirs=(
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/caddy/logs"
        "$PROJECT_ROOT/dashboard/logs"
    )
    
    for log_dir in "${log_dirs[@]}"; do
        if [[ -d "$log_dir" ]]; then
            echo "Cleaning logs in: $log_dir"
            find "$log_dir" -name "*.log" -type f -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true
            find "$log_dir" -name "*.log.*" -type f -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true
            log "INFO" "Cleaned old logs in $log_dir"
        fi
    done
    
    echo -e "${GREEN}✓ Log cleanup completed${NC}"
}

# Function to clean temporary files
clean_temp_files() {
    print_header "Cleaning temporary files"
    
    local temp_patterns=(
        "$PROJECT_ROOT/tmp/*"
        "$PROJECT_ROOT/.tmp/*"
        "$PROJECT_ROOT/**/.__pycache__"
        "$PROJECT_ROOT/**/*.pyc"
        "$PROJECT_ROOT/**/*.pyo"
        "$PROJECT_ROOT/**/.pytest_cache"
        "$PROJECT_ROOT/**/.coverage"
        "$PROJECT_ROOT/**/coverage.xml"
        "$PROJECT_ROOT/**/htmlcov"
        "$PROJECT_ROOT/dashboard/node_modules/.cache"
        "$PROJECT_ROOT/dashboard/.svelte-kit"
        "$PROJECT_ROOT/dashboard/build"
    )
    
    for pattern in "${temp_patterns[@]}"; do
        # Use find to safely remove files matching pattern
        if [[ "$pattern" == *"*"* ]]; then
            # Pattern contains wildcards, use find
            dir_part=$(dirname "$pattern")
            file_part=$(basename "$pattern")
            if [[ -d "$dir_part" ]]; then
                find "$dir_part" -name "$file_part" -type f -delete 2>/dev/null || true
                find "$dir_part" -name "$file_part" -type d -exec rm -rf {} + 2>/dev/null || true
            fi
        else
            # Exact path
            if [[ -e "$pattern" ]]; then
                rm -rf "$pattern"
            fi
        fi
    done
    
    echo -e "${GREEN}✓ Temporary files cleanup completed${NC}"
    log "INFO" "Temporary files cleaned"
}

# Function to clean old backups
clean_old_backups() {
    print_header "Cleaning old backups"
    
    local backup_dirs=(
        "$PROJECT_ROOT/backup"
        "$PROJECT_ROOT/backups"
        "$PROJECT_ROOT/data/backups"
    )
    
    for backup_dir in "${backup_dirs[@]}"; do
        if [[ -d "$backup_dir" ]]; then
            echo "Cleaning backups in: $backup_dir"
            find "$backup_dir" -name "*.tar.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null || true
            find "$backup_dir" -name "*.sql" -type f -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null || true
            find "$backup_dir" -name "backup-*" -type d -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
            log "INFO" "Cleaned old backups in $backup_dir"
        fi
    done
    
    echo -e "${GREEN}✓ Backup cleanup completed${NC}"
}

# Function to clean Docker resources
clean_docker_resources() {
    print_header "Cleaning Docker resources"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠ Docker not found, skipping Docker cleanup${NC}"
        return
    fi
    
    if confirm "This will remove unused Docker images, containers, and volumes. Are you sure?"; then
        echo "Removing stopped containers..."
        docker container prune -f || true
        
        echo "Removing unused images..."
        docker image prune -f || true
        
        echo "Removing unused volumes..."
        docker volume prune -f || true
        
        echo "Removing unused networks..."
        docker network prune -f || true
        
        # More aggressive cleanup (optional)
        if confirm "Remove all unused images (including tagged ones)?"; then
            docker image prune -a -f || true
        fi
        
        echo -e "${GREEN}✓ Docker cleanup completed${NC}"
        log "INFO" "Docker resources cleaned"
    else
        echo "Skipping Docker cleanup"
    fi
}

# Function to optimize database
optimize_database() {
    print_header "Optimizing database"
    
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        echo "Running database optimization..."
        
        # Check if PostgreSQL container is running
        if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" ps postgres | grep -q "Up"; then
            # Run VACUUM and ANALYZE
            docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T postgres \
                psql -U wakedock -d wakedock -c "VACUUM ANALYZE;" || true
            
            echo -e "${GREEN}✓ Database optimization completed${NC}"
            log "INFO" "Database optimized"
        else
            echo -e "${YELLOW}⚠ PostgreSQL container not running, skipping database optimization${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ docker-compose.yml not found, skipping database optimization${NC}"
    fi
}

# Function to clean application cache
clean_app_cache() {
    print_header "Cleaning application cache"
    
    local cache_dirs=(
        "$PROJECT_ROOT/data/cache"
        "$PROJECT_ROOT/.cache"
        "$HOME/.cache/wakedock"
    )
    
    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            echo "Cleaning cache in: $cache_dir"
            find "$cache_dir" -type f -mtime +7 -delete 2>/dev/null || true
            log "INFO" "Cleaned cache in $cache_dir"
        fi
    done
    
    # Clean Redis cache if available
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" ps redis | grep -q "Up"; then
            if confirm "Clear Redis cache?"; then
                docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T redis redis-cli FLUSHDB || true
                echo -e "${GREEN}✓ Redis cache cleared${NC}"
                log "INFO" "Redis cache cleared"
            fi
        fi
    fi
    
    echo -e "${GREEN}✓ Application cache cleanup completed${NC}"
}

# Function to display disk usage before and after
show_disk_usage() {
    local label="$1"
    echo -e "\n${BLUE}=== Disk Usage ($label) ===${NC}"
    df -h "$PROJECT_ROOT" | grep -v Filesystem
    du -sh "$PROJECT_ROOT" 2>/dev/null | cut -f1 | xargs echo "Project size:"
}

# Function to display cleanup summary
show_summary() {
    print_header "Cleanup Summary"
    
    echo "Cleanup operations completed:"
    echo "- Log files older than $LOG_RETENTION_DAYS days"
    echo "- Temporary files and caches"
    echo "- Backup files older than $BACKUP_RETENTION_DAYS days"
    echo "- Docker resources (if selected)"
    echo "- Database optimization (if applicable)"
    echo "- Application cache"
    
    echo -e "\n${GREEN}✓ All cleanup operations completed successfully${NC}"
    log "INFO" "Cleanup script completed successfully"
}

# Main function
main() {
    echo -e "${BLUE}WakeDock System Cleanup${NC}"
    echo "This script will clean up temporary files, logs, and unused resources."
    echo
    
    # Show initial disk usage
    show_disk_usage "Before cleanup"
    
    # Start logging
    log "INFO" "Starting cleanup script"
    
    # Run cleanup operations
    clean_logs
    clean_temp_files
    clean_old_backups
    clean_app_cache
    
    # Optional operations that require confirmation
    if [[ "${1:-}" != "--auto" ]]; then
        clean_docker_resources
        optimize_database
    else
        echo -e "${YELLOW}Running in auto mode, skipping interactive operations${NC}"
    fi
    
    # Show final disk usage
    show_disk_usage "After cleanup"
    
    # Show summary
    show_summary
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [--auto] [-h|--help]"
        echo ""
        echo "Options:"
        echo "  --auto    Run in automatic mode (skip interactive prompts)"
        echo "  -h        Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
