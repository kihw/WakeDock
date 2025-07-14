#!/bin/bash

# Script de release automatisé WakeDock avec push automatique
# Usage: ./scripts/auto-release.sh [version]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
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
        if command -v jq &> /dev/null; then
            jq ".version = \"$new_version\"" "$file_path" > "${file_path}.tmp" && mv "${file_path}.tmp" "$file_path"
        else
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

# Fonction pour effectuer la release d'un repository
release_repository() {
    local repo_path=$1
    local repo_name=$2
    local new_version=$3
    local branch_name=$4
    local auto_push=${5:-true}
    
    log_step "=== Release du repository $repo_name ==="
    
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
    git commit -m "chore: bump version to $new_version

- Update version in configuration files
- Prepare release $new_version
- Auto-generated by release script"
    
    if [[ "$auto_push" == "true" ]]; then
        # Push de la branche
        log_info "Push de la branche $branch_name"
        git push origin "$branch_name"
        
        # Merge automatique vers main
        log_info "Merge vers main"
        git checkout main
        git merge "$branch_name" --no-ff -m "Release version $new_version

Merged from $branch_name
- Version bumped to $new_version
- All configuration files updated"
        
        # Push main
        log_info "Push de main"
        git push origin main
        
        # Création du tag
        local tag_name="v$new_version"
        log_info "Création du tag $tag_name"
        git tag -a "$tag_name" -m "Release version $new_version

Features and improvements in this release:
- Version $new_version
- Updated configuration files
- Production ready build"
        
        # Push du tag
        log_info "Push du tag $tag_name"
        git push origin "$tag_name"
        
        # Nettoyage de la branche de release
        log_info "Suppression de la branche de release $branch_name"
        git branch -d "$branch_name"
        git push origin --delete "$branch_name"
        
        log_success "Repository $repo_name mis à jour et déployé (version $new_version)"
    else
        log_success "Repository $repo_name préparé pour la release (version $new_version)"
        log_warning "Push automatique désactivé - vous devez pousser manuellement"
    fi
    
    return 0
}

# Fonction pour créer un changelog automatique
create_changelog_entry() {
    local version=$1
    local date=$(date "+%Y-%m-%d")
    
    log_info "Création d'une entrée de changelog pour v$version"
    
    # Créer un fichier temporaire avec la nouvelle entrée
    local temp_file=$(mktemp)
    local changelog_entry="## [$version] - $date

### Added
- Version bump to $version
- Automated release process
- Updated configuration files

### Changed
- All version references updated across repositories
- Build configurations synchronized

### Fixed
- Version consistency across all components

"

    # Ajouter au CHANGELOG.md s'il existe
    if [[ -f "CHANGELOG.md" ]]; then
        # Lire la première ligne (titre)
        head -1 CHANGELOG.md > "$temp_file"
        echo "" >> "$temp_file"
        echo "$changelog_entry" >> "$temp_file"
        # Ajouter le reste du fichier (à partir de la ligne 2)
        tail -n +2 CHANGELOG.md >> "$temp_file" 2>/dev/null || true
        mv "$temp_file" CHANGELOG.md
        log_success "Entrée ajoutée au CHANGELOG.md"
    else
        log_warning "CHANGELOG.md non trouvé, création d'un nouveau fichier"
        echo "# Changelog" > CHANGELOG.md
        echo "" >> CHANGELOG.md
        echo "$changelog_entry" >> CHANGELOG.md
    fi
    
    # Nettoyer le fichier temporaire
    rm -f "$temp_file"
}

# Fonction principale
main() {
    local new_version=${1:-}
    local auto_push=${2:-true}
    
    echo -e "${PURPLE}"
    echo "=================================================="
    echo "     🚀 WAKEDOCK AUTO-RELEASE SYSTEM             "
    echo "=================================================="
    echo -e "${NC}"
    
    # Demander la nouvelle version si pas fournie
    if [[ -z "$new_version" ]]; then
        echo -n "Entrez le numéro de version (format X.Y.Z): "
        read -r new_version
    fi
    
    # Validation du format
    if ! validate_version "$new_version"; then
        exit 1
    fi
    
    # Demander confirmation pour l'auto-push
    if [[ "$auto_push" != "false" ]]; then
        echo
        log_warning "Mode AUTO-PUSH activé"
        echo -e "${YELLOW}Le script va automatiquement:${NC}"
        echo "• Créer les branches de release"
        echo "• Faire les commits"
        echo "• Merger vers main"
        echo "• Pousser vers remote"
        echo "• Créer et pousser les tags"
        echo "• Nettoyer les branches temporaires"
        echo
        
        if ! confirm "Voulez-vous continuer avec l'auto-push?"; then
            auto_push="false"
            log_info "Mode manuel activé - vous devrez pousser manuellement"
        fi
    fi
    
    # Demander confirmation finale
    echo
    echo -e "${YELLOW}Récapitulatif de la release:${NC}"
    echo "- Version: $new_version"
    echo "- Auto-push: $auto_push"
    echo "- Repositories:"
    echo "  * WakeDock (principal)"
    echo "  * wakedock-backend"
    echo "  * wakedock-frontend"
    echo "- Branche: release/v$new_version"
    echo "- Tag: v$new_version"
    echo
    
    if ! confirm "Voulez-vous procéder à la release automatisée?"; then
        log_info "Opération annulée"
        exit 0
    fi
    
    # Variables
    local branch_name="release/v$new_version"
    local failed_repos=()
    
    # Début de la release
    echo
    log_step "Début de la release automatisée v$new_version..."
    
    # Repository WakeDock principal
    if ! release_repository "$WAKEDOCK_ROOT" "WakeDock" "$new_version" "$branch_name" "$auto_push"; then
        failed_repos+=("WakeDock")
    fi
    
    # Repository Backend
    if [[ -d "$BACKEND_PATH" ]]; then
        if ! release_repository "$BACKEND_PATH" "wakedock-backend" "$new_version" "$branch_name" "$auto_push"; then
            failed_repos+=("wakedock-backend")
        fi
    else
        log_warning "Repository wakedock-backend non trouvé à $BACKEND_PATH"
    fi
    
    # Repository Frontend
    if [[ -d "$FRONTEND_PATH" ]]; then
        if ! release_repository "$FRONTEND_PATH" "wakedock-frontend" "$new_version" "$branch_name" "$auto_push"; then
            failed_repos+=("wakedock-frontend")
        fi
    else
        log_warning "Repository wakedock-frontend non trouvé à $FRONTEND_PATH"
    fi
    
    # Création du changelog dans le repo principal
    cd "$WAKEDOCK_ROOT"
    create_changelog_entry "$new_version"
    
    # Résumé final
    echo
    echo -e "${PURPLE}=================================================="
    echo "              RELEASE TERMINÉE"
    echo -e "==================================================${NC}"
    
    if [[ ${#failed_repos[@]} -eq 0 ]]; then
        log_success "🎉 Release v$new_version terminée avec succès!"
        echo
        echo -e "${GREEN}✅ Actions réalisées:${NC}"
        if [[ "$auto_push" == "true" ]]; then
            echo "✓ Branches de release créées et mergées"
            echo "✓ Fichiers de version mis à jour"
            echo "✓ Commits effectués avec messages détaillés"
            echo "✓ Push vers remote origin"
            echo "✓ Tags v$new_version créés et poussés"
            echo "✓ Branches temporaires nettoyées"
            echo "✓ Changelog mis à jour"
            echo
            echo -e "${BLUE}🔗 URLs utiles:${NC}"
            echo "• Tags: https://github.com/kihw/wakedock-*/releases/tag/v$new_version"
            echo "• Commits: git log --oneline --grep='$new_version'"
        else
            echo "✓ Branches de release créées localement"
            echo "✓ Fichiers de version mis à jour"
            echo "✓ Commits effectués"
            echo "✓ Changelog mis à jour"
            echo
            echo -e "${YELLOW}⚠️  Actions manuelles requises:${NC}"
            echo "1. Push des branches: git push origin $branch_name"
            echo "2. Merge vers main: git checkout main && git merge $branch_name"
            echo "3. Création des tags: git tag -a v$new_version -m 'Release v$new_version'"
            echo "4. Push des tags: git push origin v$new_version"
        fi
    else
        log_error "❌ Échec de la release pour certains repositories:"
        for repo in "${failed_repos[@]}"; do
            echo -e "  ${RED}✗${NC} $repo"
        done
        echo
        echo -e "${YELLOW}Vérifiez les erreurs ci-dessus et relancez si nécessaire${NC}"
        exit 1
    fi
}

# Vérification des prérequis
if ! command -v git &> /dev/null; then
    log_error "git n'est pas installé"
    exit 1
fi

# Exécution du script principal
main "$@"
