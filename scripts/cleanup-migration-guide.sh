#!/bin/bash

# WakeDock Cleanup Migration Guide
# Guide pour les utilisateurs après suppression des scripts redondants

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_header() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                  🔄 WAKEDOCK SCRIPTS CLEANUP                 ║
║                      Migration Guide                         ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

show_removed_scripts() {
    echo -e "${RED}🗑️  Scripts Supprimés (100% redondants)${NC}"
    echo "=========================================="
    echo
    echo -e "${YELLOW}1. health_check.py & health-check.sh${NC}"
    echo "   ├─ Raison : Entièrement remplacé par l'API intégrée"
    echo "   ├─ Nouveau : GET /api/v1/health"
    echo "   └─ CLI    : curl http://localhost/api/v1/health"
    echo
    echo -e "${YELLOW}2. status.sh${NC}"
    echo "   ├─ Raison : Remplacé par dashboard et API system"
    echo "   ├─ Nouveau : GET /api/v1/system/overview"
    echo "   └─ CLI    : curl http://localhost/api/v1/system/overview"
    echo
    echo -e "${YELLOW}3. validate-auth-fix.sh${NC}"
    echo "   └─ Raison : Script de test temporaire obsolète"
    echo
    echo -e "${YELLOW}4. test-api-enhancements.sh${NC}"
    echo "   └─ Raison : Tests intégrés dans l'application"
    echo
}

show_api_alternatives() {
    echo -e "${GREEN}📡 Nouvelles API Endpoints${NC}"
    echo "=========================="
    echo
    echo "# Health Checks"
    echo "curl http://localhost/api/v1/health                 # Santé rapide"
    echo "curl http://localhost/api/v1/system/health         # Santé détaillée"
    echo
    echo "# System Information"  
    echo "curl http://localhost/api/v1/system/overview       # Vue d'ensemble"
    echo "curl http://localhost/api/v1/system/metrics        # Métriques"
    echo
    echo "# Services Management"
    echo "curl http://localhost/api/v1/services              # Liste services"
    echo "curl http://localhost/api/v1/services/{id}         # Détails service"
    echo
}

show_dashboard_features() {
    echo -e "${BLUE}🌐 Interface Dashboard${NC}"
    echo "====================="
    echo
    echo "Accédez à : http://localhost/"
    echo
    echo "Fonctionnalités disponibles :"
    echo "├─ 📊 Monitoring temps réel"
    echo "├─ 🏥 Health checks visuels"  
    echo "├─ 🐳 Gestion des services Docker"
    echo "├─ 📈 Métriques système"
    echo "├─ 🔍 Logs en temps réel"
    echo "└─ ⚙️  Configuration services"
    echo
}

create_aliases() {
    echo -e "${YELLOW}🛠️  Création d'alias de compatibility${NC}"
    echo "====================================="
    echo
    
    local alias_file="$HOME/.wakedock_aliases"
    
    cat > "$alias_file" << 'EOF'
# WakeDock Compatibility Aliases
# Remplacent les anciens scripts supprimés

# Health checks
alias wakedock-health="curl -s http://localhost/api/v1/health | jq . 2>/dev/null || curl -s http://localhost/api/v1/health"
alias wakedock-health-detailed="curl -s http://localhost/api/v1/system/health | jq . 2>/dev/null || curl -s http://localhost/api/v1/system/health"

# System status (remplace status.sh)
alias wakedock-status="curl -s http://localhost/api/v1/system/overview | jq . 2>/dev/null || curl -s http://localhost/api/v1/system/overview"

# Services
alias wakedock-services="curl -s http://localhost/api/v1/services | jq . 2>/dev/null || curl -s http://localhost/api/v1/services"

# System metrics
alias wakedock-metrics="curl -s http://localhost/api/v1/system/metrics | jq . 2>/dev/null || curl -s http://localhost/api/v1/system/metrics"

# Dashboard shortcut
alias wakedock-dashboard="echo 'Opening WakeDock dashboard...' && (command -v xdg-open >/dev/null && xdg-open http://localhost/) || (command -v open >/dev/null && open http://localhost/) || echo 'Open manually: http://localhost/'"
EOF

    echo -e "${GREEN}✅ Alias créés dans : $alias_file${NC}"
    echo
    echo "Pour les activer dans votre shell :"
    echo "  echo 'source ~/.wakedock_aliases' >> ~/.bashrc"
    echo "  source ~/.bashrc"
    echo
}

show_remaining_scripts() {
    echo -e "${GREEN}✅ Scripts Conservés${NC}"
    echo "==================="
    echo
    echo "Ces scripts restent utiles :"
    echo
    echo "📁 setup/"
    echo "├─ setup.sh           # Installation initiale"
    echo "└─ validate-config.py # Validation configuration"
    echo
    echo "📁 database/"
    echo "├─ init-db.sh         # Initialisation BDD"
    echo "├─ init-db.sql        # Scripts SQL de base"
    echo "└─ migrate.sh         # Migrations"
    echo
    echo "📁 maintenance/"
    echo "├─ backup.sh          # Sauvegarde système (🟡 à intégrer API)"
    echo "├─ restore.sh         # Restauration (🟡 à intégrer API)"
    echo "├─ cleanup-project.sh # Nettoyage développement"
    echo "├─ manage-dependencies.sh # Gestion dépendances"
    echo "└─ manage-secrets.sh  # Gestion secrets"
    echo
    echo "📁 monitoring/"
    echo "├─ analyze-docker-compose.sh # Analyse Docker Compose"
    echo "└─ performance_benchmark.py  # Benchmarks performance"
    echo
}

main() {
    show_header
    
    case "${1:-all}" in
        "removed")
            show_removed_scripts
            ;;
        "api")
            show_api_alternatives
            ;;
        "dashboard")
            show_dashboard_features
            ;;
        "aliases")
            create_aliases
            ;;
        "remaining")
            show_remaining_scripts
            ;;
        "all"|*)
            show_removed_scripts
            echo
            show_api_alternatives
            echo
            show_dashboard_features
            echo
            show_remaining_scripts
            echo
            echo -e "${BLUE}💡 Pour créer des alias de compatibilité :${NC}"
            echo "   $0 aliases"
            ;;
    esac
    
    echo
    echo -e "${GREEN}🎉 Migration terminée ! Utilisez l'API et le dashboard pour monitoring.${NC}"
    echo -e "${BLUE}📖 Documentation complète : docs/api/README.md${NC}"
}

main "$@"
