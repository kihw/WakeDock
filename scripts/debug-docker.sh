#!/bin/bash

# WakeDock Docker Debug & Diagnostic Script v0.6.5
# =================================================
# Script de débogage pour assurer un run correct via Docker
# Utilise deploy.sh existant avec tests et diagnostics approfondis

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/debug-docker.log"
DEPLOY_SCRIPT="$PROJECT_ROOT/deploy.sh"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "${BLUE}$*${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$*${NC}"
}

log_warning() {
    log "WARNING" "${YELLOW}$*${NC}"
}

log_error() {
    log "ERROR" "${RED}$*${NC}"
}

log_debug() {
    log "DEBUG" "${PURPLE}$*${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "🔍 Vérification des prérequis Docker..."
    
    local errors=0
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        ((errors++))
    else
        local docker_version=$(docker --version)
        log_success "Docker trouvé: $docker_version"
        
        # Check Docker daemon
        if ! docker info &> /dev/null; then
            log_error "Docker daemon n'est pas en cours d'exécution"
            ((errors++))
        else
            log_success "Docker daemon actif"
        fi
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        ((errors++))
    else
        local compose_version=$(docker-compose --version)
        log_success "Docker Compose trouvé: $compose_version"
    fi
    
    # Check deploy.sh
    if [[ ! -f "$DEPLOY_SCRIPT" ]]; then
        log_error "Script deploy.sh non trouvé à: $DEPLOY_SCRIPT"
        ((errors++))
    else
        if [[ ! -x "$DEPLOY_SCRIPT" ]]; then
            log_warning "deploy.sh n'est pas exécutable, correction..."
            chmod +x "$DEPLOY_SCRIPT"
        fi
        log_success "Script deploy.sh trouvé et exécutable"
    fi
    
    # Check available ports
    local ports=(80 443 3000 8000 5432 6379)
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_warning "Port $port déjà utilisé"
        else
            log_debug "Port $port disponible"
        fi
    done
    
    # Check disk space
    local available_space=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ "$available_space" -lt 5 ]]; then
        log_warning "Espace disque faible: ${available_space}GB disponible"
    else
        log_success "Espace disque suffisant: ${available_space}GB disponible"
    fi
    
    return $errors
}

# Function to test deploy.sh options
test_deploy_script() {
    log_info "🧪 Test des options du script deploy.sh..."
    
    cd "$PROJECT_ROOT"
    
    # Test help
    log_debug "Test de l'aide..."
    if ./deploy.sh --help &> /dev/null; then
        log_success "Option --help fonctionne"
    else
        log_error "Option --help échoue"
    fi
    
    # Test status
    log_debug "Test du statut..."
    if ./deploy.sh --status &> /dev/null; then
        log_success "Option --status fonctionne"
    else
        log_warning "Option --status échoue (normal si pas encore déployé)"
    fi
    
    # Test configuration check
    log_debug "Vérification de la configuration..."
    if [[ -f ".env" ]]; then
        log_success "Fichier .env trouvé"
        log_debug "Variables d'environnement détectées:"
        grep -E "^[A-Z_]+" .env | head -5 | while read line; do
            log_debug "  $line"
        done
    else
        log_warning "Fichier .env non trouvé"
    fi
}

# Function to run development build test
test_development_build() {
    log_info "🔧 Test du build en mode développement..."
    
    cd "$PROJECT_ROOT"
    
    # Clean previous build
    log_debug "Nettoyage des builds précédents..."
    ./deploy.sh --clean &>> "$LOG_FILE" || true
    
    # Run development build
    log_debug "Lancement du build développement..."
    if timeout 600 ./deploy.sh --dev --skip-tests &>> "$LOG_FILE"; then
        log_success "Build développement réussi"
        
        # Wait for services to start
        log_debug "Attente du démarrage des services..."
        sleep 30
        
        # Check services
        check_running_services
        
    else
        log_error "Build développement échoué"
        show_recent_logs
        return 1
    fi
}

# Function to test production build
test_production_build() {
    log_info "🚀 Test du build en mode production..."
    
    cd "$PROJECT_ROOT"
    
    # Clean previous build
    log_debug "Nettoyage des builds précédents..."
    ./deploy.sh --clean &>> "$LOG_FILE" || true
    
    # Run production build
    log_debug "Lancement du build production..."
    if timeout 900 ./deploy.sh --force &>> "$LOG_FILE"; then
        log_success "Build production réussi"
        
        # Wait for services to start
        log_debug "Attente du démarrage des services..."
        sleep 45
        
        # Check services
        check_running_services
        
    else
        log_error "Build production échoué"
        show_recent_logs
        return 1
    fi
}

# Function to check running services
check_running_services() {
    log_info "🔍 Vérification des services en cours d'exécution..."
    
    cd "$PROJECT_ROOT"
    
    # Check Docker containers
    log_debug "Conteneurs Docker actifs:"
    if docker-compose ps 2>/dev/null | tee -a "$LOG_FILE"; then
        local running_containers=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)
        log_info "Conteneurs actifs: $running_containers"
    else
        log_error "Impossible de lister les conteneurs"
        return 1
    fi
    
    # Health checks
    log_debug "Tests de santé des services..."
    
    # Frontend health check
    if curl -sf http://localhost:3000 &> /dev/null; then
        log_success "Frontend accessible (port 3000)"
    else
        log_error "Frontend non accessible (port 3000)"
    fi
    
    # Backend health check
    if curl -sf http://localhost:8000/health &> /dev/null; then
        log_success "Backend accessible (port 8000)"
    elif curl -sf http://localhost:8000 &> /dev/null; then
        log_warning "Backend accessible mais endpoint /health non trouvé"
    else
        log_error "Backend non accessible (port 8000)"
    fi
    
    # Database connection check
    if docker-compose exec -T postgres pg_isready &> /dev/null; then
        log_success "Base de données PostgreSQL accessible"
    else
        log_error "Base de données PostgreSQL non accessible"
    fi
    
    # Redis check
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis accessible"
    else
        log_error "Redis non accessible"
    fi
}

# Function to show recent logs
show_recent_logs() {
    log_info "📋 Logs récents des services..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose logs --tail=20 2>/dev/null | tee -a "$LOG_FILE"; then
        log_debug "Logs affichés ci-dessus"
    else
        log_error "Impossible de récupérer les logs"
    fi
}

# Function to check network connectivity
check_network_connectivity() {
    log_info "🌐 Vérification de la connectivité réseau..."
    
    cd "$PROJECT_ROOT"
    
    # Check Docker networks
    log_debug "Réseaux Docker:"
    docker network ls | tee -a "$LOG_FILE"
    
    # Check if containers can communicate
    if docker-compose exec -T backend ping -c 1 frontend &> /dev/null; then
        log_success "Communication backend -> frontend OK"
    else
        log_warning "Communication backend -> frontend échouée"
    fi
    
    if docker-compose exec -T frontend ping -c 1 backend &> /dev/null; then
        log_success "Communication frontend -> backend OK"
    else
        log_warning "Communication frontend -> backend échouée"
    fi
}

# Function to check volumes and persistence
check_volumes_persistence() {
    log_info "💾 Vérification des volumes et persistance..."
    
    cd "$PROJECT_ROOT"
    
    # List volumes
    log_debug "Volumes Docker:"
    docker volume ls | tee -a "$LOG_FILE"
    
    # Test file persistence
    local test_file="/tmp/wakedock_test_$(date +%s).txt"
    local test_content="WakeDock persistence test - $(date)"
    
    if docker-compose exec -T backend sh -c "echo '$test_content' > '$test_file'" &> /dev/null; then
        if docker-compose exec -T backend cat "$test_file" 2>/dev/null | grep -q "$test_content"; then
            log_success "Persistance des fichiers OK"
            docker-compose exec -T backend rm -f "$test_file" &> /dev/null || true
        else
            log_error "Test de persistance échoué"
        fi
    else
        log_warning "Impossible de tester la persistance"
    fi
}

# Function to run stress test
run_stress_test() {
    log_info "⚡ Test de charge basique..."
    
    # Simple load test with curl
    local success_count=0
    local total_requests=10
    
    for i in $(seq 1 $total_requests); do
        if curl -sf http://localhost:3000 &> /dev/null; then
            ((success_count++))
        fi
        sleep 0.5
    done
    
    local success_rate=$((success_count * 100 / total_requests))
    if [[ $success_rate -ge 80 ]]; then
        log_success "Test de charge: $success_rate% de réussite ($success_count/$total_requests)"
    else
        log_warning "Test de charge: $success_rate% de réussite ($success_count/$total_requests)"
    fi
}

# Function to generate diagnostic report
generate_diagnostic_report() {
    log_info "📊 Génération du rapport de diagnostic..."
    
    local report_file="$PROJECT_ROOT/logs/diagnostic-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# WakeDock Docker Diagnostic Report
**Date**: $(date)
**Version**: 0.6.5

## System Information
- **OS**: $(uname -a)
- **Docker**: $(docker --version)
- **Docker Compose**: $(docker-compose --version)
- **Available Space**: $(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}')

## Container Status
\`\`\`
$(docker-compose ps 2>/dev/null || echo "No containers running")
\`\`\`

## Recent Logs
\`\`\`
$(tail -50 "$LOG_FILE")
\`\`\`

## Network Information
\`\`\`
$(docker network ls)
\`\`\`

## Volume Information
\`\`\`
$(docker volume ls)
\`\`\`

---
*Rapport généré automatiquement par debug-docker.sh*
EOF

    log_success "Rapport de diagnostic généré: $report_file"
}

# Main function
main() {
    log_info "🚀 WakeDock Docker Debug & Diagnostic v0.6.5"
    log_info "================================================"
    echo ""
    
    local start_time=$(date +%s)
    local errors=0
    
    # Parse arguments
    local test_mode="full"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                test_mode="quick"
                shift
                ;;
            --dev-only)
                test_mode="dev"
                shift
                ;;
            --prod-only)
                test_mode="prod"
                shift
                ;;
            --help)
                echo "Usage: $0 [--quick|--dev-only|--prod-only|--help]"
                echo "  --quick    : Tests rapides uniquement"
                echo "  --dev-only : Test build développement seulement"
                echo "  --prod-only: Test build production seulement"
                echo "  --help     : Affiche cette aide"
                exit 0
                ;;
            *)
                log_error "Option inconnue: $1"
                exit 1
                ;;
        esac
    done
    
    # Step 1: Prerequisites
    if ! check_prerequisites; then
        log_error "❌ Prérequis non satisfaits"
        ((errors++))
        if [[ $errors -gt 0 ]]; then
            log_error "Arrêt du test à cause des prérequis manquants"
            exit 1
        fi
    fi
    
    # Step 2: Deploy script test
    test_deploy_script || ((errors++))
    
    if [[ "$test_mode" == "quick" ]]; then
        log_info "Mode rapide - tests de base uniquement"
    else
        # Step 3: Development build test
        if [[ "$test_mode" == "full" || "$test_mode" == "dev" ]]; then
            test_development_build || ((errors++))
            
            if [[ $errors -eq 0 ]]; then
                check_network_connectivity || true
                check_volumes_persistence || true
                run_stress_test || true
            fi
        fi
        
        # Step 4: Production build test
        if [[ "$test_mode" == "full" || "$test_mode" == "prod" ]]; then
            test_production_build || ((errors++))
            
            if [[ $errors -eq 0 ]]; then
                check_network_connectivity || true
                check_volumes_persistence || true
                run_stress_test || true
            fi
        fi
    fi
    
    # Step 5: Generate report
    generate_diagnostic_report
    
    # Summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    log_info "📋 Résumé du diagnostic"
    log_info "======================"
    log_info "Durée: ${duration}s"
    log_info "Erreurs: $errors"
    
    if [[ $errors -eq 0 ]]; then
        log_success "✅ Tous les tests sont passés avec succès!"
        log_success "WakeDock est prêt pour le déploiement Docker"
    else
        log_error "❌ $errors erreur(s) détectée(s)"
        log_error "Consultez les logs pour plus de détails: $LOG_FILE"
    fi
    
    echo ""
    log_info "📁 Fichiers générés:"
    log_info "  - Log complet: $LOG_FILE"
    log_info "  - Rapport diagnostic: $(ls -t $PROJECT_ROOT/logs/diagnostic-report-*.md | head -1)"
    
    exit $errors
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
