#!/bin/bash

# WakeDock Rollback Script v0.6.5
# ===============================
# Script de rollback automatique en cas d'échec de déploiement

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
BACKUP_DIR="$PROJECT_ROOT/.backup"
LOG_FILE="$PROJECT_ROOT/logs/rollback.log"

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

# Function to create backup before deployment
create_backup() {
    log_info "📦 Création d'une sauvegarde avant déploiement..."
    
    local backup_timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_path="$BACKUP_DIR/$backup_timestamp"
    
    mkdir -p "$backup_path"
    
    # Save current docker-compose state
    cd "$PROJECT_ROOT"
    if docker-compose ps --services 2>/dev/null > "$backup_path/running_services.txt"; then
        log_success "État des services sauvegardé"
    fi
    
    # Save current images
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(wakedock|frontend|backend)" > "$backup_path/images.txt" 2>/dev/null; then
        log_success "Liste des images sauvegardée"
    fi
    
    # Save configuration files
    local config_files=(".env" "docker-compose-multi-repo.yml" "docker-compose-local-multi-repo.yml")
    for file in "${config_files[@]}"; do
        if [[ -f "$file" ]]; then
            cp "$file" "$backup_path/"
            log_success "Fichier $file sauvegardé"
        fi
    done
    
    # Save data volumes
    if [[ -d "data" ]]; then
        tar -czf "$backup_path/data_backup.tar.gz" data/ 2>/dev/null || true
        log_success "Données sauvegardées"
    fi
    
    echo "$backup_timestamp" > "$BACKUP_DIR/latest_backup.txt"
    log_success "Sauvegarde créée: $backup_path"
    echo "$backup_path"
}

# Function to restore from backup
restore_from_backup() {
    local backup_timestamp="$1"
    local backup_path="$BACKUP_DIR/$backup_timestamp"
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Sauvegarde non trouvée: $backup_path"
        return 1
    fi
    
    log_info "🔄 Restauration depuis la sauvegarde: $backup_timestamp"
    
    cd "$PROJECT_ROOT"
    
    # Stop current services
    log_info "Arrêt des services actuels..."
    docker-compose down || true
    
    # Restore configuration files
    local config_files=(".env" "docker-compose-multi-repo.yml" "docker-compose-local-multi-repo.yml")
    for file in "${config_files[@]}"; do
        if [[ -f "$backup_path/$file" ]]; then
            cp "$backup_path/$file" "$file"
            log_success "Fichier $file restauré"
        fi
    done
    
    # Restore data if available
    if [[ -f "$backup_path/data_backup.tar.gz" ]]; then
        log_info "Restauration des données..."
        tar -xzf "$backup_path/data_backup.tar.gz" 2>/dev/null || true
        log_success "Données restaurées"
    fi
    
    # Restart services
    log_info "Redémarrage des services..."
    if ./deploy.sh --dev; then
        log_success "Services redémarrés avec succès"
        return 0
    else
        log_error "Échec du redémarrage des services"
        return 1
    fi
}

# Function to list available backups
list_backups() {
    log_info "📋 Sauvegardes disponibles:"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_warning "Aucune sauvegarde trouvée"
        return 0
    fi
    
    local count=0
    for backup in "$BACKUP_DIR"/*/; do
        if [[ -d "$backup" ]]; then
            local backup_name=$(basename "$backup")
            local backup_date=$(echo "$backup_name" | sed 's/\([0-9]\{8\}\)-\([0-9]\{6\}\)/\1 \2/')
            log_info "  - $backup_name ($backup_date)"
            ((count++))
        fi
    done
    
    if [[ $count -eq 0 ]]; then
        log_warning "Aucune sauvegarde trouvée"
    else
        log_info "Total: $count sauvegarde(s)"
    fi
}

# Function to get latest backup
get_latest_backup() {
    if [[ -f "$BACKUP_DIR/latest_backup.txt" ]]; then
        cat "$BACKUP_DIR/latest_backup.txt"
    else
        ls -1 "$BACKUP_DIR" 2>/dev/null | grep -E "^[0-9]{8}-[0-9]{6}$" | sort | tail -1
    fi
}

# Function to automatic rollback
automatic_rollback() {
    log_error "🚨 Rollback automatique activé"
    
    local latest_backup=$(get_latest_backup)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "Aucune sauvegarde disponible pour le rollback"
        return 1
    fi
    
    log_info "Utilisation de la sauvegarde: $latest_backup"
    
    if restore_from_backup "$latest_backup"; then
        log_success "✅ Rollback automatique réussi"
        
        # Wait for services to start
        sleep 30
        
        # Test services
        cd "$PROJECT_ROOT"
        if ./scripts/test-deployment.sh --quick 2>/dev/null; then
            log_success "✅ Services fonctionnels après rollback"
            return 0
        else
            log_error "❌ Services non fonctionnels après rollback"
            return 1
        fi
    else
        log_error "❌ Échec du rollback automatique"
        return 1
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    local keep_count="${1:-5}"
    
    log_info "🧹 Nettoyage des anciennes sauvegardes (garde les $keep_count plus récentes)"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_info "Aucune sauvegarde à nettoyer"
        return 0
    fi
    
    local backup_list=($(ls -1 "$BACKUP_DIR" 2>/dev/null | grep -E "^[0-9]{8}-[0-9]{6}$" | sort -r))
    
    if [[ ${#backup_list[@]} -le $keep_count ]]; then
        log_info "Nombre de sauvegardes OK (${#backup_list[@]} <= $keep_count)"
        return 0
    fi
    
    local removed_count=0
    for ((i=$keep_count; i<${#backup_list[@]}; i++)); do
        local backup_to_remove="${backup_list[$i]}"
        local backup_path="$BACKUP_DIR/$backup_to_remove"
        
        if [[ -d "$backup_path" ]]; then
            rm -rf "$backup_path"
            log_success "Sauvegarde supprimée: $backup_to_remove"
            ((removed_count++))
        fi
    done
    
    log_info "Nettoyage terminé: $removed_count sauvegarde(s) supprimée(s)"
}

# Main function
main() {
    local action="${1:-auto}"
    
    case "$action" in
        create|backup)
            create_backup
            ;;
        restore)
            local backup_timestamp="${2:-$(get_latest_backup)}"
            if [[ -z "$backup_timestamp" ]]; then
                log_error "Aucune sauvegarde spécifiée ou disponible"
                exit 1
            fi
            restore_from_backup "$backup_timestamp"
            ;;
        list)
            list_backups
            ;;
        auto|automatic)
            automatic_rollback
            ;;
        cleanup)
            local keep_count="${2:-5}"
            cleanup_old_backups "$keep_count"
            ;;
        latest)
            local latest=$(get_latest_backup)
            if [[ -n "$latest" ]]; then
                echo "$latest"
            else
                log_error "Aucune sauvegarde disponible"
                exit 1
            fi
            ;;
        --help)
            echo "Usage: $0 [create|restore|list|auto|cleanup|latest|--help] [options]"
            echo ""
            echo "Actions:"
            echo "  create          Créer une nouvelle sauvegarde"
            echo "  restore [ID]    Restaurer depuis une sauvegarde (dernière si non spécifiée)"
            echo "  list            Lister les sauvegardes disponibles"
            echo "  auto            Rollback automatique vers la dernière sauvegarde"
            echo "  cleanup [N]     Nettoyer les anciennes sauvegardes (garde les N plus récentes, défaut: 5)"
            echo "  latest          Afficher l'ID de la dernière sauvegarde"
            echo "  --help          Afficher cette aide"
            echo ""
            echo "Exemples:"
            echo "  $0 create                    # Créer une sauvegarde"
            echo "  $0 restore 20250717-123000   # Restaurer une sauvegarde spécifique"
            echo "  $0 auto                      # Rollback automatique"
            echo "  $0 cleanup 3                 # Garder seulement les 3 dernières sauvegardes"
            ;;
        *)
            log_error "Action inconnue: $action"
            echo "Utilisez $0 --help pour voir les options disponibles"
            exit 1
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
