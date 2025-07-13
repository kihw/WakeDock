#!/bin/bash

# WakeDock Scripts Migration Helper
# Aide à la transition vers la nouvelle structure de scripts

set -euo pipefail

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Migration Helper - Nouvelle Structure Scripts WakeDock${NC}"
echo "=================================================================="
echo

# Mapping des anciens vers nouveaux chemins
declare -A SCRIPT_MAPPING=(
    ["scripts/setup.sh"]="scripts/setup/setup.sh"
    ["scripts/validate-config.py"]="scripts/setup/validate-config.py"
    ["scripts/init-db.sh"]="scripts/database/init-db.sh"
    ["scripts/init-db.sql"]="scripts/database/init-db.sql"
    ["scripts/migrate.sh"]="scripts/database/migrate.sh"
    ["scripts/backup.sh"]="scripts/maintenance/backup.sh"
    ["scripts/restore.sh"]="scripts/maintenance/restore.sh"
    ["scripts/cleanup-project.sh"]="scripts/maintenance/cleanup-project.sh"
    ["scripts/manage-dependencies.sh"]="scripts/maintenance/manage-dependencies.sh"
    ["scripts/manage-secrets.sh"]="scripts/maintenance/manage-secrets.sh"
    ["scripts/health-check.sh"]="scripts/monitoring/health-check.sh"
    ["scripts/status.sh"]="scripts/monitoring/status.sh"
    ["scripts/performance_benchmark.py"]="scripts/monitoring/performance_benchmark.py"
    ["scripts/analyze-docker-compose.sh"]="scripts/monitoring/analyze-docker-compose.sh"
)

# Scripts supprimés
declare -a DEPRECATED_SCRIPTS=(
    "scripts/debug-auth.sh"
    "scripts/test-api-enhancements.sh"
    "scripts/validate-auth-fix.sh"
    "scripts/run_performance_migrations.py"
)

echo -e "${GREEN}✨ Nouveaux Chemins des Scripts${NC}"
echo "--------------------------------"
for old_path in "${!SCRIPT_MAPPING[@]}"; do
    new_path="${SCRIPT_MAPPING[$old_path]}"
    echo -e "${BLUE}$old_path${NC} → ${GREEN}$new_path${NC}"
done

echo
echo -e "${YELLOW}🗑️  Scripts Obsolètes (déplacés vers deprecated/)${NC}"
echo "-----------------------------------------------"
for script in "${DEPRECATED_SCRIPTS[@]}"; do
    echo -e "${RED}$script${NC} → deprecated/"
done

echo
echo -e "${BLUE}📖 Exemples de Migration${NC}"
echo "-------------------------"
echo "Ancien :"
echo -e "  ${RED}./scripts/health-check.sh${NC}"
echo "Nouveau :"
echo -e "  ${GREEN}./scripts/monitoring/health-check.sh${NC}"
echo
echo "Ancien :"
echo -e "  ${RED}./scripts/backup.sh${NC}"
echo "Nouveau :"
echo -e "  ${GREEN}./scripts/maintenance/backup.sh${NC}"

echo
echo -e "${GREEN}✅ Migration terminée avec succès !${NC}"
echo "Consultez scripts/README.md pour plus de détails."
