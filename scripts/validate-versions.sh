#!/bin/bash

# Script de validation des versions pour WakeDock
# Vérifie que toutes les versions sont cohérentes

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration des paths
WAKEDOCK_ROOT="/Docker/code/WakeDock"
BACKEND_PATH="/Docker/code/wakedock-backend"
FRONTEND_PATH="/Docker/code/wakedock-frontend"

# Fonctions utilitaires
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

# Fonction pour extraire la version d'un package.json
get_package_json_version() {
    local file_path=$1
    if [[ -f "$file_path" ]] && command -v jq &> /dev/null; then
        jq -r '.version' "$file_path" 2>/dev/null || echo "unknown"
    elif [[ -f "$file_path" ]]; then
        grep '"version"' "$file_path" | sed 's/.*"version": *"\([^"]*\)".*/\1/' || echo "unknown"
    else
        echo "not_found"
    fi
}

# Fonction pour extraire la version d'un pyproject.toml
get_pyproject_version() {
    local file_path=$1
    if [[ -f "$file_path" ]]; then
        grep '^version = ' "$file_path" | sed 's/version = "\([^"]*\)"/\1/' || echo "unknown"
    else
        echo "not_found"
    fi
}

# Fonction pour extraire la version du Dockerfile
get_dockerfile_version() {
    local file_path=$1
    if [[ -f "$file_path" ]]; then
        grep 'org.opencontainers.image.version=' "$file_path" | sed 's/.*org.opencontainers.image.version="\([^"]*\)".*/\1/' || echo "unknown"
    else
        echo "not_found"
    fi
}

# Fonction principale
main() {
    echo -e "${BLUE}"
    echo "=================================="
    echo "   WakeDock Version Validator"
    echo "=================================="
    echo -e "${NC}"
    
    # Collecte des versions
    log_info "Collecte des versions des différents composants..."
    
    # WakeDock principal
    local wakedock_package_version=$(get_package_json_version "$WAKEDOCK_ROOT/package.json")
    local wakedock_dockerfile_version=$(get_dockerfile_version "$WAKEDOCK_ROOT/Dockerfile")
    
    # Backend
    local backend_version=$(get_pyproject_version "$BACKEND_PATH/pyproject.toml")
    local wakedock_backend_subproject_version=$(get_pyproject_version "$WAKEDOCK_ROOT/wakedock-backend/pyproject.toml")
    
    # Frontend
    local frontend_version=$(get_package_json_version "$FRONTEND_PATH/package.json")
    local wakedock_frontend_subproject_version=$(get_package_json_version "$WAKEDOCK_ROOT/wakedock-frontend/package.json")
    
    # Versions dans le code frontend
    local storage_version="unknown"
    if [[ -f "$FRONTEND_PATH/src/lib/utils/storage.ts" ]]; then
        storage_version=$(grep "private readonly version" "$FRONTEND_PATH/src/lib/utils/storage.ts" | sed "s/.*version = '\([^']*\)'.*/\1/" || echo "unknown")
    fi
    
    local sidebar_version="unknown"
    if [[ -f "$FRONTEND_PATH/src/lib/components/sidebar/SidebarFooter.svelte" ]]; then
        sidebar_version=$(grep "WakeDock v" "$FRONTEND_PATH/src/lib/components/sidebar/SidebarFooter.svelte" | sed 's/.*WakeDock v\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/' || echo "unknown")
    fi
    
    # Affichage des versions
    echo
    log_info "Versions détectées:"
    echo
    echo -e "${YELLOW}Repository Principal (WakeDock):${NC}"
    echo "  - package.json: $wakedock_package_version"
    echo "  - Dockerfile: $wakedock_dockerfile_version"
    echo
    echo -e "${YELLOW}Backend:${NC}"
    echo "  - Repository standalone: $backend_version"
    echo "  - Sous-projet WakeDock: $wakedock_backend_subproject_version"
    echo
    echo -e "${YELLOW}Frontend:${NC}"
    echo "  - Repository standalone: $frontend_version"
    echo "  - Sous-projet WakeDock: $wakedock_frontend_subproject_version"
    echo "  - storage.ts: $storage_version"
    echo "  - SidebarFooter.svelte: $sidebar_version"
    
    # Analyse de cohérence
    echo
    log_info "Analyse de cohérence..."
    
    local errors=0
    local warnings=0
    
    # Vérification de la cohérence du backend
    if [[ "$backend_version" != "not_found" && "$wakedock_backend_subproject_version" != "not_found" ]]; then
        if [[ "$backend_version" != "$wakedock_backend_subproject_version" ]]; then
            log_error "Incohérence Backend: standalone ($backend_version) ≠ sous-projet ($wakedock_backend_subproject_version)"
            ((errors++))
        else
            log_success "Backend: versions cohérentes ($backend_version)"
        fi
    else
        log_warning "Backend: impossible de comparer les versions (fichiers manquants)"
        ((warnings++))
    fi
    
    # Vérification de la cohérence du frontend
    if [[ "$frontend_version" != "not_found" && "$wakedock_frontend_subproject_version" != "not_found" ]]; then
        if [[ "$frontend_version" != "$wakedock_frontend_subproject_version" ]]; then
            log_error "Incohérence Frontend: standalone ($frontend_version) ≠ sous-projet ($wakedock_frontend_subproject_version)"
            ((errors++))
        else
            log_success "Frontend: versions package.json cohérentes ($frontend_version)"
        fi
    else
        log_warning "Frontend: impossible de comparer les versions package.json (fichiers manquants)"
        ((warnings++))
    fi
    
    # Vérification des versions dans le code frontend
    if [[ "$frontend_version" != "not_found" ]]; then
        if [[ "$storage_version" != "unknown" && "$storage_version" != "$frontend_version" ]]; then
            log_error "Incohérence Frontend: package.json ($frontend_version) ≠ storage.ts ($storage_version)"
            ((errors++))
        fi
        
        if [[ "$sidebar_version" != "unknown" && "$sidebar_version" != "$frontend_version" ]]; then
            log_error "Incohérence Frontend: package.json ($frontend_version) ≠ SidebarFooter.svelte ($sidebar_version)"
            ((errors++))
        fi
        
        if [[ "$storage_version" == "$frontend_version" && "$sidebar_version" == "$frontend_version" ]]; then
            log_success "Frontend: versions dans le code cohérentes ($frontend_version)"
        fi
    fi
    
    # Vérification du repository principal
    if [[ "$wakedock_package_version" != "not_found" && "$wakedock_dockerfile_version" != "not_found" ]]; then
        if [[ "$wakedock_package_version" != "$wakedock_dockerfile_version" ]]; then
            log_error "Incohérence WakeDock: package.json ($wakedock_package_version) ≠ Dockerfile ($wakedock_dockerfile_version)"
            ((errors++))
        else
            log_success "WakeDock principal: versions cohérentes ($wakedock_package_version)"
        fi
    else
        log_warning "WakeDock principal: impossible de comparer les versions (fichiers manquants)"
        ((warnings++))
    fi
    
    # Résumé final
    echo
    echo -e "${BLUE}=================================="
    echo "         Résumé de validation"
    echo -e "==================================${NC}"
    
    if [[ $errors -eq 0 ]]; then
        log_success "Toutes les versions sont cohérentes!"
        if [[ $warnings -gt 0 ]]; then
            log_warning "$warnings avertissement(s) détecté(s)"
        fi
        exit 0
    else
        log_error "$errors erreur(s) de cohérence détectée(s)"
        if [[ $warnings -gt 0 ]]; then
            log_warning "$warnings avertissement(s) détecté(s)"
        fi
        echo
        echo -e "${YELLOW}Recommandations:${NC}"
        echo "1. Utilisez le script release-version.sh pour synchroniser toutes les versions"
        echo "2. Ou utilisez update-single-version.sh pour chaque repository individuellement"
        exit 1
    fi
}

main "$@"
