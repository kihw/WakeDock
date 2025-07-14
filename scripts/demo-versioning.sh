#!/bin/bash

# Script de démonstration pour les outils de versioning WakeDock
# Usage: ./scripts/demo-versioning.sh

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_demo() {
    echo -e "${PURPLE}[DEMO]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Fonction pour afficher les commandes
show_command() {
    echo -e "${YELLOW}$ $1${NC}"
}

# Fonction pour simuler une pause
pause_demo() {
    echo
    echo -e "${BLUE}Appuyez sur Entrée pour continuer...${NC}"
    read -r
}

# Fonction principale
main() {
    clear
    echo -e "${PURPLE}"
    echo "=================================================="
    echo "     🚀 DÉMONSTRATION - SYSTEM DE VERSIONING     "
    echo "=================================================="
    echo -e "${NC}"
    
    log_demo "Bienvenue dans la démonstration du système de versioning WakeDock!"
    echo
    echo -e "${YELLOW}Ce système permet de:${NC}"
    echo "✅ Gérer les versions des 3 repositories (WakeDock, backend, frontend)"
    echo "✅ Synchroniser automatiquement les fichiers de configuration"
    echo "✅ Créer des branches et tags de release"
    echo "✅ Valider la cohérence des versions"
    
    pause_demo
    
    # Étape 1: Validation des versions actuelles
    clear
    echo -e "${PURPLE}=== ÉTAPE 1: VALIDATION DES VERSIONS ACTUELLES ===${NC}"
    log_demo "Commençons par vérifier l'état actuel des versions"
    echo
    show_command "./scripts/validate-versions.sh"
    echo
    
    ./scripts/validate-versions.sh || true
    
    pause_demo
    
    # Étape 2: Explication des scripts disponibles
    clear
    echo -e "${PURPLE}=== ÉTAPE 2: SCRIPTS DISPONIBLES ===${NC}"
    log_demo "Voici les 3 scripts principaux du système:"
    echo
    echo -e "${GREEN}1. release-version.sh${NC} - Release complète de tous les repos"
    echo -e "${GREEN}2. update-single-version.sh${NC} - Mise à jour d'un seul repo"
    echo -e "${GREEN}3. validate-versions.sh${NC} - Validation des cohérences"
    echo
    
    log_info "Fichiers créés dans ./scripts/:"
    ls -la scripts/{release-version.sh,update-single-version.sh,validate-versions.sh} 2>/dev/null || echo "Scripts en cours de création..."
    
    pause_demo
    
    # Étape 3: Démonstration des tâches VS Code
    clear
    echo -e "${PURPLE}=== ÉTAPE 3: TÂCHES VS CODE ===${NC}"
    log_demo "Des tâches VS Code ont été configurées pour faciliter l'utilisation"
    echo
    echo -e "${YELLOW}Tâches disponibles (Ctrl+Shift+P > Tasks: Run Task):${NC}"
    echo "🎯 Release Version - All Repositories"
    echo "🎯 Update Version - Main Repository"
    echo "🎯 Update Version - Backend"
    echo "🎯 Update Version - Frontend"
    echo "🎯 Validate Versions"
    echo
    
    log_info "Fichier de configuration créé:"
    echo "📁 .vscode/tasks.json"
    
    pause_demo
    
    # Étape 4: Workflow recommandé
    clear
    echo -e "${PURPLE}=== ÉTAPE 4: WORKFLOW RECOMMANDÉ ===${NC}"
    log_demo "Voici le workflow recommandé pour une release:"
    echo
    echo -e "${YELLOW}Phase 1: Préparation${NC}"
    show_command "git status  # Vérifier que tous les repos sont propres"
    show_command "git checkout main && git pull  # Être sur main à jour"
    echo
    echo -e "${YELLOW}Phase 2: Validation${NC}"
    show_command "./scripts/validate-versions.sh  # Vérifier les cohérences"
    echo
    echo -e "${YELLOW}Phase 3: Release${NC}"
    show_command "./scripts/release-version.sh  # Lancer la release interactive"
    echo
    echo -e "${YELLOW}Phase 4: Finalisation${NC}"
    echo "• Créer les Pull Requests"
    echo "• Tester les builds"
    echo "• Merger et déployer"
    
    pause_demo
    
    # Étape 5: Exemple d'utilisation
    clear
    echo -e "${PURPLE}=== ÉTAPE 5: EXEMPLE D'UTILISATION ===${NC}"
    log_demo "Simulation d'une mise à jour de version individuelle"
    echo
    log_warning "SIMULATION UNIQUEMENT - Aucun changement réel ne sera effectué"
    echo
    show_command "./scripts/update-single-version.sh frontend 1.2.0"
    echo
    echo -e "${BLUE}Le script demanderait:${NC}"
    echo "1. Confirmation de la version"
    echo "2. Vérification que le repo est propre"
    echo "3. Mise à jour des fichiers:"
    echo "   - package.json"
    echo "   - src/lib/utils/storage.ts"
    echo "   - src/lib/components/sidebar/SidebarFooter.svelte"
    echo "4. Commit automatique avec message standardisé"
    
    pause_demo
    
    # Étape 6: Architecture des fichiers
    clear
    echo -e "${PURPLE}=== ÉTAPE 6: ARCHITECTURE DES FICHIERS ===${NC}"
    log_demo "Fichiers automatiquement gérés par le système:"
    echo
    echo -e "${YELLOW}Repository Principal (WakeDock):${NC}"
    echo "📄 package.json"
    echo "🐳 Dockerfile"
    echo "📦 wakedock-backend/pyproject.toml (sous-projet)"
    echo "📦 wakedock-frontend/package.json (sous-projet)"
    echo
    echo -e "${YELLOW}Backend (wakedock-backend):${NC}"
    echo "📄 pyproject.toml"
    echo
    echo -e "${YELLOW}Frontend (wakedock-frontend):${NC}"
    echo "📄 package.json"
    echo "💾 src/lib/utils/storage.ts"
    echo "🎨 src/lib/components/sidebar/SidebarFooter.svelte"
    echo "🔐 src/lib/components/auth/login/LoginFooter.svelte"
    
    pause_demo
    
    # Étape 7: Résumé final
    clear
    echo -e "${PURPLE}=== RÉSUMÉ FINAL ===${NC}"
    log_success "Système de versioning WakeDock configuré avec succès!"
    echo
    echo -e "${GREEN}✅ Scripts créés et configurés${NC}"
    echo -e "${GREEN}✅ Tâches VS Code disponibles${NC}"
    echo -e "${GREEN}✅ Documentation complète${NC}"
    echo -e "${GREEN}✅ Validation automatique${NC}"
    echo
    echo -e "${YELLOW}📚 Documentation:${NC}"
    echo "• README complet dans ./scripts/README.md"
    echo "• Exemples d'utilisation inclus"
    echo "• Guide de dépannage disponible"
    echo
    echo -e "${BLUE}🚀 Pour commencer:${NC}"
    echo "1. Exécutez: ./scripts/validate-versions.sh"
    echo "2. Ou utilisez les tâches VS Code (Ctrl+Shift+P)"
    echo "3. Consultez ./scripts/README.md pour plus de détails"
    echo
    log_success "Démonstration terminée! Le système est prêt à l'utilisation."
}

# Vérification que nous sommes dans le bon répertoire
if [[ ! -d "scripts" ]]; then
    echo -e "${RED}Erreur: Ce script doit être exécuté depuis la racine du projet WakeDock${NC}"
    exit 1
fi

main "$@"
