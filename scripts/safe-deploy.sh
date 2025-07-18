#!/bin/bash

# WakeDock Safe Deploy Script v0.6.5
# ====================================
# Script de déploiement sécurisé avec rollback automatique

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/safe-deploy.log"

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

log_info() {
    log "INFO" "${BLUE}$*${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$*${NC}"
}

log_warning() {
    log "WARNING" "${YELLOW}$*${NC}"
}

log_error() {
    log "ERROR" "${RED}$*${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "🔍 Vérification des prérequis..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/deploy.sh" ]]; then
        log_error "Script deploy.sh non trouvé dans $PROJECT_ROOT"
        return 1
    fi
    
    # Check if rollback script exists
    if [[ ! -f "$SCRIPT_DIR/rollback.sh" ]]; then
        log_error "Script rollback.sh non trouvé"
        return 1
    fi
    
    # Check if debug script exists
    if [[ ! -f "$SCRIPT_DIR/debug-docker.sh" ]]; then
        log_error "Script debug-docker.sh non trouvé"
        return 1
    fi
    
    log_success "✅ Tous les prérequis sont satisfaits"
    return 0
}

# Function to run pre-deployment tests
run_pre_deployment_tests() {
    log_info "🧪 Tests pré-déploiement..."
    
    cd "$PROJECT_ROOT"
    
    # Run debug script in quick mode
    if ./scripts/debug-docker.sh --mode=quick >/dev/null 2>&1; then
        log_success "✅ Tests Docker prérequis OK"
    else
        log_error "❌ Échec des tests Docker prérequis"
        return 1
    fi
    
    # Check if deploy.sh is executable
    if [[ -x "./deploy.sh" ]]; then
        log_success "✅ Script deploy.sh exécutable"
    else
        log_error "❌ Script deploy.sh non exécutable"
        return 1
    fi
    
    return 0
}

# Function to create backup
create_backup() {
    log_info "💾 Création d'une sauvegarde de sécurité..."
    
    cd "$PROJECT_ROOT"
    local backup_id
    backup_id=$(./scripts/rollback.sh create 2>/dev/null | grep "Sauvegarde créée" | awk '{print $NF}' | xargs basename 2>/dev/null || echo "")
    
    if [[ -n "$backup_id" ]]; then
        log_success "✅ Sauvegarde créée: $backup_id"
        echo "$backup_id"
        return 0
    else
        log_error "❌ Échec de la création de sauvegarde"
        return 1
    fi
}

# Function to deploy
deploy() {
    local mode="${1:-dev}"
    
    log_info "🚀 Déploiement en mode: $mode"
    
    cd "$PROJECT_ROOT"
    
    # Deploy based on mode
    case "$mode" in
        dev|development)
            if timeout 300 ./deploy.sh --dev; then
                log_success "✅ Déploiement dev réussi"
                return 0
            else
                log_error "❌ Échec du déploiement dev"
                return 1
            fi
            ;;
        prod|production)
            if timeout 600 ./deploy.sh --prod; then
                log_success "✅ Déploiement prod réussi"
                return 0
            else
                log_error "❌ Échec du déploiement prod"
                return 1
            fi
            ;;
        *)
            if timeout 300 ./deploy.sh; then
                log_success "✅ Déploiement standard réussi"
                return 0
            else
                log_error "❌ Échec du déploiement standard"
                return 1
            fi
            ;;
    esac
}

# Function to test deployment
test_deployment() {
    log_info "🔬 Tests post-déploiement..."
    
    cd "$PROJECT_ROOT"
    
    # Wait for services to start
    log_info "⏳ Attente du démarrage des services (30s)..."
    sleep 30
    
    # Quick test
    if ./scripts/test-deployment.sh --quick >/dev/null 2>&1; then
        log_success "✅ Tests post-déploiement OK"
        return 0
    else
        log_error "❌ Échec des tests post-déploiement"
        return 1
    fi
}

# Function to rollback if needed
rollback_if_needed() {
    log_error "🚨 Déploiement échoué - Rollback automatique"
    
    cd "$PROJECT_ROOT"
    
    if ./scripts/rollback.sh auto >/dev/null 2>&1; then
        log_success "✅ Rollback automatique réussi"
        return 0
    else
        log_error "❌ Échec du rollback automatique"
        return 1
    fi
}

# Function to cleanup old backups
cleanup_backups() {
    local keep_count="${1:-5}"
    
    log_info "🧹 Nettoyage des anciennes sauvegardes..."
    
    cd "$PROJECT_ROOT"
    
    if ./scripts/rollback.sh cleanup "$keep_count" >/dev/null 2>&1; then
        log_success "✅ Nettoyage terminé"
    else
        log_warning "⚠️ Problème lors du nettoyage"
    fi
}

# Main safe deploy function
safe_deploy() {
    local mode="${1:-dev}"
    local auto_rollback="${2:-true}"
    
    log_info "🛡️ Début du déploiement sécurisé WakeDock v0.6.5"
    log_info "Mode: $mode, Auto-rollback: $auto_rollback"
    
    # Check prerequisites
    if ! check_prerequisites; then
        log_error "❌ Prérequis non satisfaits"
        exit 1
    fi
    
    # Pre-deployment tests
    if ! run_pre_deployment_tests; then
        log_error "❌ Tests pré-déploiement échoués"
        exit 1
    fi
    
    # Create backup
    local backup_id
    if ! backup_id=$(create_backup); then
        log_error "❌ Impossible de créer une sauvegarde"
        exit 1
    fi
    
    # Deploy
    local deploy_success=false
    if deploy "$mode"; then
        # Test deployment
        if test_deployment; then
            deploy_success=true
            log_success "🎉 Déploiement sécurisé réussi!"
        else
            log_error "❌ Tests post-déploiement échoués"
        fi
    else
        log_error "❌ Déploiement échoué"
    fi
    
    # Rollback if deployment failed and auto-rollback is enabled
    if [[ "$deploy_success" == "false" && "$auto_rollback" == "true" ]]; then
        if rollback_if_needed; then
            log_info "✅ Système restauré à l'état précédent"
        else
            log_error "❌ Rollback échoué - intervention manuelle requise"
            exit 1
        fi
    fi
    
    # Cleanup old backups
    cleanup_backups 5
    
    if [[ "$deploy_success" == "true" ]]; then
        log_success "🚀 Déploiement sécurisé terminé avec succès"
        return 0
    else
        log_error "💥 Déploiement échoué"
        return 1
    fi
}

# Main function
main() {
    local mode="${1:-dev}"
    local auto_rollback="${2:-true}"
    
    case "$mode" in
        --help|-h)
            echo "Usage: $0 [dev|prod] [true|false]"
            echo ""
            echo "Arguments:"
            echo "  mode            Mode de déploiement (dev|prod, défaut: dev)"
            echo "  auto_rollback   Rollback automatique en cas d'échec (true|false, défaut: true)"
            echo ""
            echo "Exemples:"
            echo "  $0                    # Déploiement dev avec rollback automatique"
            echo "  $0 prod               # Déploiement prod avec rollback automatique"
            echo "  $0 dev false          # Déploiement dev sans rollback automatique"
            echo "  $0 prod true          # Déploiement prod avec rollback automatique"
            ;;
        *)
            safe_deploy "$mode" "$auto_rollback"
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
