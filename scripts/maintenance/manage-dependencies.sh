#!/bin/bash

# WakeDock - Script de gestion des dépendances
# Ce script met à jour et audite les dépendances du projet

set -euo pipefail

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD_DIR="$PROJECT_ROOT/dashboard"

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

check_npm_audit() {
    log_info "Audit de sécurité NPM..."
    
    if cd "$DASHBOARD_DIR" 2>/dev/null; then
        # Créer un backup de package-lock.json
        if [[ -f "package-lock.json" ]]; then
            cp package-lock.json package-lock.json.backup
        fi
        
        # Afficher l'audit actuel
        log_info "État actuel des vulnérabilités:"
        npm audit --audit-level low || true
        
        echo ""
        read -p "Voulez-vous tenter de corriger automatiquement les vulnérabilités? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Tentative de correction automatique..."
            
            # Essayer la correction simple d'abord
            if npm audit fix; then
                log_success "Corrections automatiques appliquées"
            else
                log_warning "La correction automatique a échoué"
                
                echo ""
                read -p "Voulez-vous forcer les corrections (peut casser la compatibilité)? (y/N): " -n 1 -r
                echo
                
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    log_warning "Application des corrections forcées..."
                    npm audit fix --force || log_error "Les corrections forcées ont échoué"
                fi
            fi
            
            # Vérifier l'état après correction
            log_info "État après correction:"
            npm audit --audit-level low || true
        fi
        
        cd "$PROJECT_ROOT"
    else
        log_error "Impossible d'accéder au répertoire dashboard"
    fi
}

check_outdated_packages() {
    log_info "Vérification des packages obsolètes..."
    
    if cd "$DASHBOARD_DIR" 2>/dev/null; then
        log_info "Packages NPM obsolètes:"
        npm outdated || log_info "Tous les packages sont à jour"
        
        echo ""
        read -p "Voulez-vous mettre à jour les packages obsolètes? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Mise à jour des packages..."
            npm update
            log_success "Packages mis à jour"
        fi
        
        cd "$PROJECT_ROOT"
    fi
}

check_python_security() {
    log_info "Vérification des vulnérabilités Python..."
    
    # Installer pip-audit si nécessaire
    if ! command -v pip-audit >/dev/null 2>&1; then
        log_info "Installation de pip-audit..."
        pip install pip-audit
    fi
    
    # Vérifier les vulnérabilités
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_info "Audit des dépendances Python:"
        pip-audit -r "$PROJECT_ROOT/requirements.txt" || log_warning "Vulnérabilités détectées"
    fi
    
    if [[ -f "$PROJECT_ROOT/requirements-prod.txt" ]]; then
        log_info "Audit des dépendances de production:"
        pip-audit -r "$PROJECT_ROOT/requirements-prod.txt" || log_warning "Vulnérabilités détectées"
    fi
}

update_node_version() {
    log_info "Vérification de la version Node.js..."
    
    current_node=$(node --version 2>/dev/null || echo "Non installé")
    recommended_node="v20.18.0"
    
    log_info "Version actuelle: $current_node"
    log_info "Version recommandée: $recommended_node"
    
    if [[ "$current_node" != "$recommended_node" ]]; then
        log_warning "Version Node.js différente de celle recommandée"
        log_info "Utilisez nvm pour installer la version recommandée:"
        log_info "  nvm install $recommended_node"
        log_info "  nvm use $recommended_node"
    else
        log_success "Version Node.js correcte"
    fi
}

optimize_package_json() {
    log_info "Optimisation du package.json..."
    
    package_json="$DASHBOARD_DIR/package.json"
    
    if [[ -f "$package_json" ]]; then
        # Créer une sauvegarde
        cp "$package_json" "$package_json.backup"
        
        # Vérifier et optimiser les scripts
        log_info "Scripts disponibles dans package.json:"
        jq -r '.scripts | keys[]' "$package_json" 2>/dev/null || log_warning "jq non installé"
        
        # Suggestion d'ajouts de scripts utiles
        log_info "Scripts recommandés pour le développement:"
        echo "  - security:audit: Audit de sécurité complet"
        echo "  - deps:update: Mise à jour des dépendances"
        echo "  - deps:check: Vérification des dépendances obsolètes"
        
        log_success "Optimisation du package.json terminée"
    fi
}

generate_dependency_report() {
    log_info "Génération du rapport de dépendances..."
    
    report_file="$PROJECT_ROOT/dependency_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# Rapport de Dépendances WakeDock

**Date**: $(date)
**Script**: manage-dependencies.sh

## Environnement

- **Node.js**: $(node --version 2>/dev/null || echo "Non installé")
- **NPM**: $(npm --version 2>/dev/null || echo "Non installé")
- **Python**: $(python3 --version 2>/dev/null || echo "Non installé")
- **pip**: $(pip --version 2>/dev/null || echo "Non installé")

## Dépendances Frontend (NPM)

### Audit de Sécurité
EOF

    if cd "$DASHBOARD_DIR" 2>/dev/null; then
        echo "$(npm audit --audit-level low 2>&1 || echo 'Audit non disponible')" >> "$report_file"
        cd "$PROJECT_ROOT"
    fi

    cat >> "$report_file" << EOF

### Packages Obsolètes
EOF

    if cd "$DASHBOARD_DIR" 2>/dev/null; then
        echo '```' >> "$report_file"
        npm outdated 2>&1 >> "$report_file" || echo "Tous les packages sont à jour" >> "$report_file"
        echo '```' >> "$report_file"
        cd "$PROJECT_ROOT"
    fi

    cat >> "$report_file" << EOF

## Dépendances Backend (Python)

### Vulnérabilités
EOF

    if command -v pip-audit >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        echo '```' >> "$report_file"
        pip-audit -r "$PROJECT_ROOT/requirements.txt" 2>&1 >> "$report_file" || echo "Audit Python non disponible" >> "$report_file"
        echo '```' >> "$report_file"
    else
        echo "pip-audit non installé ou requirements.txt non trouvé" >> "$report_file"
    fi

    cat >> "$report_file" << EOF

## Recommandations

### Actions Immédiates
- [ ] Corriger les vulnérabilités critiques et hautes
- [ ] Mettre à jour les packages avec des correctifs de sécurité
- [ ] Tester l'application après les mises à jour

### Actions de Maintenance
- [ ] Programmer des audits réguliers (hebdomadaires)
- [ ] Mettre en place des alertes de sécurité automatiques
- [ ] Documenter les dépendances critiques

### Outils Recommandés
- **Snyk**: Monitoring continu des vulnérabilités
- **Dependabot**: Mises à jour automatiques des dépendances
- **npm-check-updates**: Gestion avancée des mises à jour NPM

---

**Généré par**: scripts/manage-dependencies.sh
**Prochaine révision**: $(date -d '+1 week' 2>/dev/null || date)
EOF

    log_success "Rapport généré: $report_file"
}

main() {
    log_info "Démarrage de la gestion des dépendances WakeDock..."
    
    update_node_version
    check_npm_audit
    check_outdated_packages
    check_python_security
    optimize_package_json
    generate_dependency_report
    
    log_success "🎉 Gestion des dépendances terminée!"
    log_info "Consultez le rapport généré pour plus de détails."
    
    # Recommandations finales
    echo ""
    log_info "🔧 Actions recommandées:"
    echo "  1. Testez l'application après les mises à jour"
    echo "  2. Commitez les changements de dépendances"
    echo "  3. Programmez des audits réguliers"
    echo "  4. Surveillez les alertes de sécurité"
}

# Vérifier que le script est exécuté depuis le bon répertoire
if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    log_error "Ce script doit être exécuté depuis la racine du projet WakeDock"
    exit 1
fi

main "$@"
