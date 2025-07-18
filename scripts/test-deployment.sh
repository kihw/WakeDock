#!/bin/bash

# WakeDock Deployment Test Script v0.6.5
# ======================================
# Script de test rapide pour valider le déploiement Docker

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 WakeDock Deployment Test v0.6.5${NC}"
echo "======================================"

# Test 1: Check deploy.sh exists and is executable
echo -e "${BLUE}1. Vérification du script deploy.sh...${NC}"
if [[ -x "$PROJECT_ROOT/deploy.sh" ]]; then
    echo -e "${GREEN}✅ deploy.sh trouvé et exécutable${NC}"
else
    echo -e "${RED}❌ deploy.sh non trouvé ou non exécutable${NC}"
    exit 1
fi

# Test 2: Check Docker
echo -e "${BLUE}2. Vérification de Docker...${NC}"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo -e "${GREEN}✅ Docker opérationnel${NC}"
else
    echo -e "${RED}❌ Docker non disponible${NC}"
    exit 1
fi

# Test 3: Check Docker Compose
echo -e "${BLUE}3. Vérification de Docker Compose...${NC}"
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅ Docker Compose disponible${NC}"
else
    echo -e "${RED}❌ Docker Compose non disponible${NC}"
    exit 1
fi

# Test 4: Quick deploy script test
echo -e "${BLUE}4. Test rapide du script deploy.sh...${NC}"
cd "$PROJECT_ROOT"

if ./deploy.sh --help &> /dev/null; then
    echo -e "${GREEN}✅ deploy.sh --help fonctionne${NC}"
else
    echo -e "${RED}❌ deploy.sh --help échoue${NC}"
    exit 1
fi

# Test 5: Check configuration files
echo -e "${BLUE}5. Vérification des fichiers de configuration...${NC}"
config_files=(
    "docker-compose-multi-repo.yml"
    "docker-compose-local-multi-repo.yml"
    ".env.example"
    ".env"
)

missing_files=0
for file in "${config_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $file trouvé${NC}"
    else
        echo -e "${YELLOW}⚠️  $file manquant${NC}"
        ((missing_files++))
    fi
done

if [[ $missing_files -eq 0 ]]; then
    echo -e "${GREEN}✅ Tous les fichiers de configuration trouvés${NC}"
else
    echo -e "${YELLOW}⚠️  $missing_files fichier(s) de configuration manquant(s)${NC}"
fi

# Test 6: Run debug script if available
echo -e "${BLUE}6. Lancement du diagnostic complet...${NC}"
if [[ -x "scripts/debug-docker.sh" ]]; then
    echo -e "${BLUE}Lancement du script de debug...${NC}"
    ./scripts/debug-docker.sh --quick
    exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✅ Diagnostic complet réussi${NC}"
    else
        echo -e "${RED}❌ Diagnostic complet échoué (code: $exit_code)${NC}"
        exit $exit_code
    fi
else
    echo -e "${YELLOW}⚠️  Script debug-docker.sh non trouvé, test manuel...${NC}"
    
    # Manual basic test
    echo -e "${BLUE}Test manuel de base...${NC}"
    if ./deploy.sh --status &> /dev/null; then
        echo -e "${GREEN}✅ deploy.sh --status fonctionne${NC}"
    else
        echo -e "${YELLOW}⚠️  deploy.sh --status échoue (normal si pas encore déployé)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Tests de déploiement terminés avec succès!${NC}"
echo -e "${BLUE}Pour un diagnostic complet, utilisez:${NC}"
echo -e "${BLUE}  ./scripts/debug-docker.sh${NC}"
echo ""
