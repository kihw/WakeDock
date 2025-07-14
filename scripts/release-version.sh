#!/bin/bash

# Script de versioning pour WakeDock
# Gère la mise à jour des versions pour les 3 repositories
# Usage: ./scripts/release-version.sh

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

# Fonction pour valider le format de version
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Format de version invalide. Utilisez le format X.Y.Z (ex: 1.2.3)"
        return 1
    fi
    return 0
}

# Fonction pour demander confirmation
confirm() {
    local message=$1
    echo -e "${YELLOW}$message${NC}"
    read -p "Continuer? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Fonction pour vérifier si on est sur la branche main
check_main_branch() {
    local repo_path=$1
    local repo_name=$2
    
    cd "$repo_path"
    local current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]]; then
        log_error "Repository $repo_name n'est pas sur la branche main (branche actuelle: $current_branch)"
        return 1
    fi
    return 0
}

# Fonction pour vérifier si le repo est propre
check_clean_repo() {
    local repo_path=$1
    local repo_name=$2
    
    cd "$repo_path"
    if [[ -n $(git status --porcelain) ]]; then
        log_error "Repository $repo_name a des changements non commités"
        git status --short
        return 1
    fi
    return 0
}

# Fonction pour mettre à jour la version dans package.json
update_package_json_version() {
    local file_path=$1
    local new_version=$2
    
    if [[ -f "$file_path" ]]; then
        log_info "Mise à jour de $file_path"
        # Utilisation de jq pour mettre à jour proprement le JSON
        if command -v jq &> /dev/null; then
            jq ".version = \"$new_version\"" "$file_path" > "${file_path}.tmp" && mv "${file_path}.tmp" "$file_path"
        else
            # Fallback avec sed si jq n'est pas disponible
            sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$new_version\"/" "$file_path"
        fi
        log_success "Version mise à jour dans $file_path"
    else
        log_warning "Fichier $file_path non trouvé"
    fi
}

# Fonction pour mettre à jour la version dans pyproject.toml
update_pyproject_version() {
    local file_path=$1
    local new_version=$2
    
    if [[ -f "$file_path" ]]; then
        log_info "Mise à jour de $file_path"
        sed -i "s/version = \"[^\"]*\"/version = \"$new_version\"/" "$file_path"
        log_success "Version mise à jour dans $file_path"
    else
        log_warning "Fichier $file_path non trouvé"
    fi
}

# Fonction pour mettre à jour la version dans le Dockerfile
update_dockerfile_version() {
    local file_path=$1
    local new_version=$2
    
    if [[ -f "$file_path" ]]; then
        log_info "Mise à jour de $file_path"
        sed -i "s/org.opencontainers.image.version=\"[^\"]*\"/org.opencontainers.image.version=\"$new_version\"/" "$file_path"
        log_success "Version mise à jour dans $file_path"
    else
        log_warning "Fichier $file_path non trouvé"
    fi
}

# Fonction pour mettre à jour les références de version dans le frontend
update_frontend_version_refs() {
    local new_version=$1
    local frontend_path=$2
    
    # Mise à jour dans storage.ts
    local storage_file="$frontend_path/src/lib/utils/storage.ts"
    if [[ -f "$storage_file" ]]; then
        log_info "Mise à jour des références de version dans storage.ts"
        sed -i "s/private readonly version = '[^']*'/private readonly version = '$new_version'/" "$storage_file"
    fi
    
    # Mise à jour dans SidebarFooter.svelte
    local sidebar_file="$frontend_path/src/lib/components/sidebar/SidebarFooter.svelte"
    if [[ -f "$sidebar_file" ]]; then
        log_info "Mise à jour des références de version dans SidebarFooter.svelte"
        sed -i "s/WakeDock v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/WakeDock v$new_version/" "$sidebar_file"
    fi
    
    # Mise à jour dans LoginFooter.svelte
    local login_footer_file="$frontend_path/src/lib/components/auth/login/LoginFooter.svelte"
    if [[ -f "$login_footer_file" ]]; then
        log_info "Mise à jour des références de version dans LoginFooter.svelte"
        sed -i "s/let buildVersion = 'v[^']*'/let buildVersion = 'v$new_version'/" "$login_footer_file"
        sed -i "s/PUBLIC_BUILD_VERSION || 'v[^']*'/PUBLIC_BUILD_VERSION || 'v$new_version'/" "$login_footer_file"
    fi
}

# Fonction principale pour mettre à jour un repository
update_repository_version() {
    local repo_path=$1
    local repo_name=$2
    local new_version=$3
    local branch_name=$4
    
    log_info "=== Mise à jour du repository $repo_name ==="
    
    cd "$repo_path"
    
    # Vérifications préliminaires
    check_main_branch "$repo_path" "$repo_name" || return 1
    check_clean_repo "$repo_path" "$repo_name" || return 1
    
    # Pull des dernières modifications
    log_info "Pull des dernières modifications de main"
    git pull origin main
    
    # Création de la branche de release
    log_info "Création de la branche $branch_name"
    git checkout -b "$branch_name"
    
    # Mise à jour des fichiers de version selon le type de repository
    case "$repo_name" in
        "wakedock-backend")
            update_pyproject_version "$repo_path/pyproject.toml" "$new_version"
            ;;
        "wakedock-frontend")
            update_package_json_version "$repo_path/package.json" "$new_version"
            update_frontend_version_refs "$new_version" "$repo_path"
            ;;
        "WakeDock")
            # Pour le repo principal, on met à jour les sous-projets et les références
            update_package_json_version "$repo_path/package.json" "$new_version"
            update_dockerfile_version "$repo_path/Dockerfile" "$new_version"
            
            # Mise à jour des sous-projets s'ils existent
            if [[ -d "$repo_path/wakedock-backend" ]]; then
                update_pyproject_version "$repo_path/wakedock-backend/pyproject.toml" "$new_version"
            fi
            if [[ -d "$repo_path/wakedock-frontend" ]]; then
                update_package_json_version "$repo_path/wakedock-frontend/package.json" "$new_version"
                update_frontend_version_refs "$new_version" "$repo_path/wakedock-frontend"
            fi
            ;;
    esac
    
    # Commit des changements
    log_info "Commit des changements de version"
    git add .
    git commit -m "chore: bump version to $new_version"
    
    # Push de la branche
    log_info "Push de la branche $branch_name"
    git push origin "$branch_name"
    
    # Création du tag
    local tag_name="v$new_version"
    log_info "Création du tag $tag_name"
    git tag -a "$tag_name" -m "Release version $new_version"
    git push origin "$tag_name"
    
    log_success "Repository $repo_name mis à jour avec succès (version $new_version)"
    
    return 0
}

# Fonction principale
main() {
    echo -e "${BLUE}"
    echo "=================================="
    echo "   WakeDock Version Manager"
    echo "=================================="
    echo -e "${NC}"
    
    # Demander la nouvelle version
    echo -n "Entrez le numéro de version (format X.Y.Z): "
    read -r new_version
    
    # Validation du format
    if ! validate_version "$new_version"; then
        exit 1
    fi
    
    # Demander confirmation
    echo
    echo -e "${YELLOW}Récapitulatif de la release:${NC}"
    echo "- Version: $new_version"
    echo "- Repositories à mettre à jour:"
    echo "  * WakeDock (principal)"
    echo "  * wakedock-backend"
    echo "  * wakedock-frontend"
    echo "- Branche de release: release/v$new_version"
    echo "- Tag: v$new_version"
    echo
    
    if ! confirm "Voulez-vous procéder à la mise à jour de version?"; then
        log_info "Opération annulée"
        exit 0
    fi
    
    # Variables
    local branch_name="release/v$new_version"
    local failed_repos=()
    
    # Mise à jour des repositories
    echo
    log_info "Début de la mise à jour des repositories..."
    
    # Repository WakeDock principal
    if ! update_repository_version "$WAKEDOCK_ROOT" "WakeDock" "$new_version" "$branch_name"; then
        failed_repos+=("WakeDock")
    fi
    
    # Repository Backend
    if [[ -d "$BACKEND_PATH" ]]; then
        if ! update_repository_version "$BACKEND_PATH" "wakedock-backend" "$new_version" "$branch_name"; then
            failed_repos+=("wakedock-backend")
        fi
    else
        log_warning "Repository wakedock-backend non trouvé à $BACKEND_PATH"
    fi
    
    # Repository Frontend
    if [[ -d "$FRONTEND_PATH" ]]; then
        if ! update_repository_version "$FRONTEND_PATH" "wakedock-frontend" "$new_version" "$branch_name"; then
            failed_repos+=("wakedock-frontend")
        fi
    else
        log_warning "Repository wakedock-frontend non trouvé à $FRONTEND_PATH"
    fi
    
    # Résumé final
    echo
    echo -e "${BLUE}=================================="
    echo "       Résumé de la release"
    echo -e "==================================${NC}"
    
    if [[ ${#failed_repos[@]} -eq 0 ]]; then
        log_success "Tous les repositories ont été mis à jour avec succès!"
        echo
        echo -e "${GREEN}Actions réalisées:${NC}"
        echo "✓ Création de la branche release/v$new_version"
        echo "✓ Mise à jour des fichiers de version"
        echo "✓ Commit des changements"
        echo "✓ Push des branches"
        echo "✓ Création et push des tags v$new_version"
        echo
        echo -e "${YELLOW}Prochaines étapes:${NC}"
        echo "1. Créer les Pull Requests pour merger les branches release"
        echo "2. Tester les builds"
        echo "3. Déployer les nouvelles versions"
    else
        log_error "Échec de la mise à jour pour certains repositories:"
        for repo in "${failed_repos[@]}"; do
            echo -e "  ${RED}✗${NC} $repo"
        done
    fi
}

# Vérification des prérequis
if ! command -v git &> /dev/null; then
    log_error "git n'est pas installé"
    exit 1
fi

# Exécution du script principal
main "$@"
