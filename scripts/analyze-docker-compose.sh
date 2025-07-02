#!/bin/bash

# WakeDock - Script d'analyse et optimisation Docker Compose
# Ce script analyse les fichiers docker-compose et propose des optimisations

set -euo pipefail

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

analyze_compose_files() {
    log_info "Analyse des fichiers Docker Compose..."
    
    # Trouver tous les fichiers docker-compose
    compose_files=($(find "$PROJECT_ROOT" -name "docker-compose*.yml" -type f))
    
    log_info "Fichiers Docker Compose trouvés: ${#compose_files[@]}"
    
    for file in "${compose_files[@]}"; do
        relative_path="${file#$PROJECT_ROOT/}"
        log_info "  - $relative_path"
    done
    
    # Analyser la structure
    echo ""
    log_info "Analyse de la structure:"
    
    # Fichiers principaux
    main_compose="$PROJECT_ROOT/docker-compose.yml"
    dev_compose="$PROJECT_ROOT/docker-compose.dev.yml"
    prod_compose="$PROJECT_ROOT/docker-compose.prod.yml"
    test_compose="$PROJECT_ROOT/docker-compose.test.yml"
    
    # Vérifier la cohérence
    if [[ -f "$main_compose" ]]; then
        log_success "✓ docker-compose.yml (principal)"
    else
        log_error "✗ docker-compose.yml manquant"
    fi
    
    if [[ -f "$dev_compose" ]]; then
        log_success "✓ docker-compose.dev.yml (développement)"
    else
        log_warning "⚠ docker-compose.dev.yml manquant"
    fi
    
    if [[ -f "$prod_compose" ]]; then
        log_success "✓ docker-compose.prod.yml (production)"
    else
        log_warning "⚠ docker-compose.prod.yml manquant"
    fi
    
    if [[ -f "$test_compose" ]]; then
        log_success "✓ docker-compose.test.yml (tests)"
    else
        log_warning "⚠ docker-compose.test.yml manquant"
    fi
}

check_compose_redundancy() {
    log_info "Vérification des redondances..."
    
    # Comparer les services entre fichiers
    compose_files=($(find "$PROJECT_ROOT" -maxdepth 1 -name "docker-compose*.yml" -type f))
    
    declare -A services_count
    
    for file in "${compose_files[@]}"; do
        if command -v yq >/dev/null 2>&1; then
            services=$(yq e '.services | keys | .[]' "$file" 2>/dev/null || echo "")
            for service in $services; do
                ((services_count["$service"]++)) || services_count["$service"]=1
            done
        else
            # Extraction simple sans yq
            services=$(grep -E "^  [a-zA-Z]" "$file" | grep -v "^  #" | cut -d: -f1 | tr -d ' ' || echo "")
            for service in $services; do
                ((services_count["$service"]++)) || services_count["$service"]=1
            done
        fi
    done
    
    log_info "Services définis dans plusieurs fichiers:"
    for service in "${!services_count[@]}"; do
        count=${services_count[$service]}
        if [[ $count -gt 1 ]]; then
            log_warning "  - $service: défini dans $count fichiers"
        fi
    done
}

validate_compose_syntax() {
    log_info "Validation de la syntaxe Docker Compose..."
    
    compose_files=($(find "$PROJECT_ROOT" -maxdepth 1 -name "docker-compose*.yml" -type f))
    
    for file in "${compose_files[@]}"; do
        filename=$(basename "$file")
        
        if docker-compose -f "$file" config >/dev/null 2>&1; then
            log_success "✓ $filename: syntaxe valide"
        else
            log_error "✗ $filename: erreurs de syntaxe détectées"
            docker-compose -f "$file" config 2>&1 | head -5
        fi
    done
}

analyze_docker_images() {
    log_info "Analyse des images Docker utilisées..."
    
    compose_files=($(find "$PROJECT_ROOT" -maxdepth 1 -name "docker-compose*.yml" -type f))
    
    declare -A images_used
    
    for file in "${compose_files[@]}"; do
        # Extraire les images utilisées
        if command -v yq >/dev/null 2>&1; then
            images=$(yq e '.services.[].image' "$file" 2>/dev/null | grep -v "null" || echo "")
        else
            images=$(grep -E "^\s*image:" "$file" | sed 's/.*image:\s*//' | tr -d '"' || echo "")
        fi
        
        for image in $images; do
            if [[ -n "$image" && "$image" != "null" ]]; then
                ((images_used["$image"]++)) || images_used["$image"]=1
            fi
        done
    done
    
    log_info "Images Docker utilisées:"
    for image in "${!images_used[@]}"; do
        count=${images_used[$image]}
        log_info "  - $image (utilisée $count fois)"
    done
}

check_security_practices() {
    log_info "Vérification des bonnes pratiques de sécurité..."
    
    compose_files=($(find "$PROJECT_ROOT" -maxdepth 1 -name "docker-compose*.yml" -type f))
    
    for file in "${compose_files[@]}"; do
        filename=$(basename "$file")
        log_info "Analyse de $filename:"
        
        # Vérifier les secrets en dur
        if grep -q "password:" "$file" 2>/dev/null; then
            log_warning "  ⚠ Mots de passe potentiels trouvés"
        fi
        
        # Vérifier l'utilisation des variables d'environnement
        if grep -q "\${" "$file" 2>/dev/null; then
            log_success "  ✓ Utilise les variables d'environnement"
        else
            log_warning "  ⚠ Peu/pas de variables d'environnement utilisées"
        fi
        
        # Vérifier les volumes Docker socket
        if grep -q "/var/run/docker.sock" "$file" 2>/dev/null; then
            log_warning "  ⚠ Accès au socket Docker détecté (risque de sécurité)"
        fi
        
        # Vérifier les ports exposés
        exposed_ports=$(grep -E "^\s*-\s*[0-9]" "$file" | wc -l || echo "0")
        if [[ $exposed_ports -gt 5 ]]; then
            log_warning "  ⚠ Beaucoup de ports exposés ($exposed_ports)"
        fi
    done
}

optimize_compose_structure() {
    log_info "Suggestions d'optimisation..."
    
    # Analyser la complexité
    compose_files=($(find "$PROJECT_ROOT" -maxdepth 1 -name "docker-compose*.yml" -type f))
    total_files=${#compose_files[@]}
    
    if [[ $total_files -gt 4 ]]; then
        log_warning "Structure complexe détectée ($total_files fichiers)"
        echo "  Suggestions:"
        echo "    - Consolider les environnements similaires"
        echo "    - Utiliser des overrides pour les différences mineures"
        echo "    - Créer des profils Docker Compose"
    else
        log_success "Structure Docker Compose optimale"
    fi
    
    # Vérifier les best practices
    log_info "Recommandations générales:"
    echo "  1. Utilisez des images officielles quand c'est possible"
    echo "  2. Spécifiez toujours les versions des images"
    echo "  3. Utilisez des variables d'environnement pour la configuration"
    echo "  4. Implémentez des health checks"
    echo "  5. Limitez les privilèges des conteneurs"
    echo "  6. Utilisez des réseaux personnalisés"
}

generate_compose_report() {
    log_info "Génération du rapport Docker Compose..."
    
    report_file="$PROJECT_ROOT/docker_compose_analysis_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# Analyse Docker Compose - WakeDock

**Date**: $(date)
**Script**: analyze-docker-compose.sh

## Structure Actuelle

### Fichiers Docker Compose
EOF

    compose_files=($(find "$PROJECT_ROOT" -name "docker-compose*.yml" -type f))
    for file in "${compose_files[@]}"; do
        relative_path="${file#$PROJECT_ROOT/}"
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        echo "- **$relative_path** (${size} bytes)" >> "$report_file"
    done

    cat >> "$report_file" << EOF

### Services Identifiés
EOF

    # Extraire les services uniques
    declare -A all_services
    for file in "${compose_files[@]}"; do
        services=$(grep -E "^  [a-zA-Z]" "$file" | grep -v "^  #" | cut -d: -f1 | tr -d ' ' || echo "")
        for service in $services; do
            all_services["$service"]=1
        done
    done

    for service in "${!all_services[@]}"; do
        echo "- $service" >> "$report_file"
    done

    cat >> "$report_file" << EOF

## Analyse de Sécurité

### Points d'Attention
- Vérification des secrets en dur: 
- Utilisation des variables d'environnement: 
- Accès au socket Docker: 
- Ports exposés: 

### Recommandations de Sécurité
1. **Secrets Management**: Utilisez Docker Secrets ou des outils externes
2. **Least Privilege**: Limitez les permissions des conteneurs
3. **Network Isolation**: Utilisez des réseaux personnalisés
4. **Image Security**: Scannez les images pour les vulnérabilités

## Optimisations Proposées

### Structure
- [ ] Consolider les fichiers similaires
- [ ] Utiliser des profils Docker Compose
- [ ] Standardiser les noms de services

### Performance
- [ ] Optimiser les images Docker
- [ ] Utiliser des caches de build
- [ ] Implémenter des health checks efficaces

### Maintenance
- [ ] Documenter les services
- [ ] Automatiser les tests de validation
- [ ] Mettre en place un monitoring

## Actions Recommandées

### Court Terme (1-2 jours)
- [ ] Corriger les problèmes de sécurité identifiés
- [ ] Valider la syntaxe de tous les fichiers
- [ ] Tester les configurations sur différents environnements

### Moyen Terme (1 semaine)
- [ ] Optimiser la structure des fichiers
- [ ] Implémenter les meilleures pratiques
- [ ] Documenter l'architecture

### Long Terme (1 mois)
- [ ] Migrer vers Docker Compose v2
- [ ] Implémenter des tests automatisés
- [ ] Optimiser les images pour la production

---

**Généré par**: scripts/analyze-docker-compose.sh
**Prochaine analyse**: $(date -d '+1 month' 2>/dev/null || date)
EOF

    log_success "Rapport généré: $report_file"
}

main() {
    log_info "Démarrage de l'analyse Docker Compose..."
    
    # Vérifier que Docker Compose est installé
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    analyze_compose_files
    echo ""
    check_compose_redundancy
    echo ""
    validate_compose_syntax
    echo ""
    analyze_docker_images
    echo ""
    check_security_practices
    echo ""
    optimize_compose_structure
    echo ""
    generate_compose_report
    
    log_success "🎉 Analyse Docker Compose terminée!"
    log_info "Consultez le rapport généré pour les détails complets."
}

# Vérifier que le script est exécuté depuis le bon répertoire
if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    log_error "Ce script doit être exécuté depuis la racine du projet WakeDock"
    exit 1
fi

main "$@"
