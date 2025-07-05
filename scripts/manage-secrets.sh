#!/bin/bash

# WakeDock Secrets Management Script
# This script helps manage secrets for WakeDock deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SECRETS_DIR="$PROJECT_ROOT/secrets"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate a random secret
generate_secret() {
    local length=${1:-32}
    openssl rand -hex "$length"
}

# Generate a random base64 secret
generate_base64_secret() {
    local length=${1:-32}
    openssl rand -base64 "$length"
}

# Create secrets directory
create_secrets_dir() {
    if [ ! -d "$SECRETS_DIR" ]; then
        mkdir -p "$SECRETS_DIR"
        chmod 700 "$SECRETS_DIR"
        log_info "Created secrets directory: $SECRETS_DIR"
    fi
}

# Generate all required secrets
generate_all_secrets() {
    create_secrets_dir
    
    log_info "Generating WakeDock secrets..."
    
    # API Key (64 chars)
    if [ ! -f "$SECRETS_DIR/api_key.txt" ]; then
        generate_secret 32 > "$SECRETS_DIR/api_key.txt"
        chmod 600 "$SECRETS_DIR/api_key.txt"
        log_info "Generated API key"
    else
        log_warn "API key already exists, skipping"
    fi
    
    # JWT Secret (64 chars)
    if [ ! -f "$SECRETS_DIR/jwt_secret.txt" ]; then
        generate_secret 32 > "$SECRETS_DIR/jwt_secret.txt"
        chmod 600 "$SECRETS_DIR/jwt_secret.txt"
        log_info "Generated JWT secret"
    else
        log_warn "JWT secret already exists, skipping"
    fi
    
    # Encryption Key (32 chars)
    if [ ! -f "$SECRETS_DIR/encryption_key.txt" ]; then
        generate_secret 16 > "$SECRETS_DIR/encryption_key.txt"
        chmod 600 "$SECRETS_DIR/encryption_key.txt"
        log_info "Generated encryption key"
    else
        log_warn "Encryption key already exists, skipping"
    fi
    
    # CSRF Secret (32 chars)
    if [ ! -f "$SECRETS_DIR/csrf_secret.txt" ]; then
        generate_secret 16 > "$SECRETS_DIR/csrf_secret.txt"
        chmod 600 "$SECRETS_DIR/csrf_secret.txt"
        log_info "Generated CSRF secret"
    else
        log_warn "CSRF secret already exists, skipping"
    fi
    
    # Database URL (if not exists)
    if [ ! -f "$SECRETS_DIR/database_url.txt" ]; then
        echo "postgresql://wakedock:$(generate_secret 16)@postgres:5432/wakedock" > "$SECRETS_DIR/database_url.txt"
        chmod 600 "$SECRETS_DIR/database_url.txt"
        log_info "Generated database URL"
    else
        log_warn "Database URL already exists, skipping"
    fi
    
    log_info "All secrets generated successfully!"
}

# Rotate a specific secret
rotate_secret() {
    local secret_name="$1"
    local secret_file="$SECRETS_DIR/${secret_name}.txt"
    
    if [ ! -f "$secret_file" ]; then
        log_error "Secret file not found: $secret_file"
        return 1
    fi
    
    # Backup old secret
    cp "$secret_file" "$secret_file.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Generate new secret based on type
    case "$secret_name" in
        "api_key"|"jwt_secret")
            generate_secret 32 > "$secret_file"
            ;;
        "encryption_key"|"csrf_secret")
            generate_secret 16 > "$secret_file"
            ;;
        "database_url")
            echo "postgresql://wakedock:$(generate_secret 16)@postgres:5432/wakedock" > "$secret_file"
            ;;
        *)
            log_error "Unknown secret type: $secret_name"
            return 1
            ;;
    esac
    
    chmod 600 "$secret_file"
    log_info "Rotated secret: $secret_name"
}

# List all secrets
list_secrets() {
    if [ ! -d "$SECRETS_DIR" ]; then
        log_warn "No secrets directory found"
        return 0
    fi
    
    log_info "Available secrets:"
    for secret_file in "$SECRETS_DIR"/*.txt; do
        if [ -f "$secret_file" ]; then
            local secret_name=$(basename "$secret_file" .txt)
            local secret_size=$(stat -c%s "$secret_file")
            local secret_modified=$(stat -c%Y "$secret_file")
            local secret_date=$(date -d "@$secret_modified" '+%Y-%m-%d %H:%M:%S')
            echo "  - $secret_name (${secret_size} bytes, modified: $secret_date)"
        fi
    done
}

# Validate secrets
validate_secrets() {
    local errors=0
    
    log_info "Validating secrets..."
    
    # Check if secrets directory exists
    if [ ! -d "$SECRETS_DIR" ]; then
        log_error "Secrets directory not found: $SECRETS_DIR"
        return 1
    fi
    
    # Required secrets
    local required_secrets=("api_key" "jwt_secret" "encryption_key" "csrf_secret")
    
    for secret_name in "${required_secrets[@]}"; do
        local secret_file="$SECRETS_DIR/${secret_name}.txt"
        
        if [ ! -f "$secret_file" ]; then
            log_error "Required secret missing: $secret_name"
            errors=$((errors + 1))
        else
            # Check file permissions
            local perms=$(stat -c%a "$secret_file")
            if [ "$perms" != "600" ]; then
                log_warn "Insecure permissions on $secret_name: $perms (should be 600)"
            fi
            
            # Check file size
            local size=$(stat -c%s "$secret_file")
            if [ "$size" -lt 16 ]; then
                log_error "Secret too short: $secret_name ($size bytes)"
                errors=$((errors + 1))
            fi
        fi
    done
    
    if [ $errors -eq 0 ]; then
        log_info "All secrets are valid!"
        return 0
    else
        log_error "Found $errors secret validation errors"
        return 1
    fi
}

# Clean up old secret backups
cleanup_backups() {
    local days=${1:-7}
    
    log_info "Cleaning up secret backups older than $days days..."
    
    if [ -d "$SECRETS_DIR" ]; then
        find "$SECRETS_DIR" -name "*.backup.*" -type f -mtime +$days -delete
        log_info "Cleanup completed"
    else
        log_warn "No secrets directory found"
    fi
}

# Export secrets as environment variables (for development)
export_env() {
    if [ ! -d "$SECRETS_DIR" ]; then
        log_error "Secrets directory not found: $SECRETS_DIR"
        return 1
    fi
    
    log_info "Exporting secrets as environment variables..."
    
    for secret_file in "$SECRETS_DIR"/*.txt; do
        if [ -f "$secret_file" ]; then
            local secret_name=$(basename "$secret_file" .txt)
            local secret_value=$(cat "$secret_file")
            local env_name="WAKEDOCK_$(echo "$secret_name" | tr '[:lower:]' '[:upper:]')"
            
            echo "export $env_name=\"$secret_value\""
        fi
    done
    
    log_info "To use these exports, run: source <(./scripts/manage-secrets.sh export-env)"
}

# Main function
main() {
    case "${1:-}" in
        "generate")
            generate_all_secrets
            ;;
        "rotate")
            if [ $# -lt 2 ]; then
                log_error "Usage: $0 rotate <secret_name>"
                exit 1
            fi
            rotate_secret "$2"
            ;;
        "list")
            list_secrets
            ;;
        "validate")
            validate_secrets
            ;;
        "cleanup")
            cleanup_backups "${2:-7}"
            ;;
        "export-env")
            export_env
            ;;
        *)
            echo "WakeDock Secrets Management"
            echo ""
            echo "Usage: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  generate    - Generate all required secrets"
            echo "  rotate      - Rotate a specific secret"
            echo "  list        - List all secrets"
            echo "  validate    - Validate secrets"
            echo "  cleanup     - Clean up old secret backups"
            echo "  export-env  - Export secrets as environment variables"
            echo ""
            echo "Examples:"
            echo "  $0 generate"
            echo "  $0 rotate api_key"
            echo "  $0 list"
            echo "  $0 validate"
            echo "  $0 cleanup 7"
            echo "  source <($0 export-env)"
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    if ! command -v openssl &> /dev/null; then
        log_error "openssl is required but not installed"
        exit 1
    fi
}

# Run main function
check_dependencies
main "$@"
