#!/bin/bash

# Script de versioning simplifié pour un seul repository
# Usage: ./scripts/update-single-version.sh [backend|frontend|main] [version]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour valider le format de version
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Format de version invalide. Utilisez le format X.Y.Z (ex: 1.2.3)"
        return 1
    fi
    return 0
}

# Fonction pour mettre à jour la version selon le type de repo
update_version() {
    local repo_type=$1
    local version=$2
    
    case "$repo_type" in
        "backend")
            if [[ -f "pyproject.toml" ]]; then
                log_info "Mise à jour de pyproject.toml"
                sed -i "s/version = \"[^\"]*\"/version = \"$version\"/" pyproject.toml
                log_success "Version mise à jour dans pyproject.toml"
            else
                log_error "Fichier pyproject.toml non trouvé"
                return 1
            fi
            ;;
        "frontend")
            if [[ -f "package.json" ]]; then
                log_info "Mise à jour de package.json"
                if command -v jq &> /dev/null; then
                    jq ".version = \"$version\"" package.json > package.json.tmp && mv package.json.tmp package.json
                else
                    sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" package.json
                fi
                log_success "Version mise à jour dans package.json"
                
                # Mise à jour des références de version dans le code
                if [[ -f "src/lib/utils/storage.ts" ]]; then
                    sed -i "s/private readonly version = '[^']*'/private readonly version = '$version'/" src/lib/utils/storage.ts
                fi
                
                if [[ -f "src/lib/components/sidebar/SidebarFooter.svelte" ]]; then
                    sed -i "s/WakeDock v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/WakeDock v$version/" src/lib/components/sidebar/SidebarFooter.svelte
                fi
            else
                log_error "Fichier package.json non trouvé"
                return 1
            fi
            ;;
        "main")
            # Mise à jour du repo principal
            if [[ -f "package.json" ]]; then
                log_info "Mise à jour de package.json"
                if command -v jq &> /dev/null; then
                    jq ".version = \"$version\"" package.json > package.json.tmp && mv package.json.tmp package.json
                else
                    sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" package.json
                fi
            fi
            
            if [[ -f "Dockerfile" ]]; then
                log_info "Mise à jour du Dockerfile"
                sed -i "s/org.opencontainers.image.version=\"[^\"]*\"/org.opencontainers.image.version=\"$version\"/" Dockerfile
            fi
            
            log_success "Version mise à jour dans les fichiers principaux"
            ;;
        *)
            log_error "Type de repository invalide. Utilisez: backend, frontend, ou main"
            return 1
            ;;
    esac
}

# Fonction principale
main() {
    local repo_type=${1:-}
    local version=${2:-}
    
    # Si pas d'arguments, mode interactif
    if [[ -z "$repo_type" ]]; then
        echo -e "${BLUE}Quel repository voulez-vous mettre à jour?${NC}"
        echo "1) backend"
        echo "2) frontend" 
        echo "3) main (repository principal)"
        echo -n "Choix (1-3): "
        read -r choice
        
        case "$choice" in
            1) repo_type="backend" ;;
            2) repo_type="frontend" ;;
            3) repo_type="main" ;;
            *) log_error "Choix invalide"; exit 1 ;;
        esac
    fi
    
    if [[ -z "$version" ]]; then
        echo -n "Entrez la nouvelle version (format X.Y.Z): "
        read -r version
    fi
    
    # Validation
    if ! validate_version "$version"; then
        exit 1
    fi
    
    # Vérification du repo
    if [[ -n $(git status --porcelain) ]]; then
        log_error "Le repository a des changements non commités"
        git status --short
        exit 1
    fi
    
    # Mise à jour
    log_info "Mise à jour de la version vers $version pour le repository $repo_type"
    
    if update_version "$repo_type" "$version"; then
        # Commit des changements
        git add .
        git commit -m "chore: bump version to $version"
        
        log_success "Version mise à jour avec succès!"
        echo -e "${YELLOW}N'oubliez pas de:${NC}"
        echo "1. Pousser les changements: git push"
        echo "2. Créer un tag: git tag -a v$version -m 'Release version $version'"
        echo "3. Pousser le tag: git push origin v$version"
    else
        log_error "Échec de la mise à jour de version"
        exit 1
    fi
}

main "$@"
