#!/bin/bash

# WakeDock Multi-Repo Local Deployment Script
# ============================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    print_status "Vérification des dépendances..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    print_success "Toutes les dépendances sont présentes"
}

# Create necessary directories
create_directories() {
    print_status "Création des répertoires nécessaires..."
    
    mkdir -p data/{caddy,caddy-config,dashboard}
    mkdir -p logs
    
    print_success "Répertoires créés"
}

# Setup network
setup_network() {
    print_status "Configuration du réseau Docker..."
    
    NETWORK_NAME="${WAKEDOCK_NETWORK:-caddy_net}"
    
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        docker network create "$NETWORK_NAME"
        print_success "Réseau $NETWORK_NAME créé"
    else
        print_warning "Le réseau $NETWORK_NAME existe déjà"
    fi
}

# Pull and update repositories
update_repositories() {
    print_status "Mise à jour des dépôts..."
    
    # Update backend
    if [ -d "wakedock-backend/.git" ]; then
        print_status "Mise à jour du backend..."
        cd wakedock-backend
        git pull origin main || git pull origin master || true
        cd ..
    else
        print_warning "Dépôt backend non trouvé, clonage..."
        git clone https://github.com/kihw/wakedock-backend.git
    fi
    
    # Update frontend
    if [ -d "wakedock-frontend/.git" ]; then
        print_status "Mise à jour du frontend..."
        cd wakedock-frontend
        git pull origin main || git pull origin master || true
        cd ..
    else
        print_warning "Dépôt frontend non trouvé, clonage..."
        git clone https://github.com/kihw/wakedock-frontend.git
    fi
    
    # Update main orchestration
    if [ -d "WakeDock/.git" ]; then
        print_status "Mise à jour de l'orchestration..."
        cd WakeDock
        git pull origin main || git pull origin master || true
        cd ..
    fi
    
    print_success "Dépôts mis à jour"
}

# Build and start services
deploy_services() {
    print_status "Déploiement des services..."
    
    # Load environment variables
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    fi
    
    # Choose compose file
    local compose_file="docker-compose-local-multi-repo.yml"
    
    if [ ! -f "$compose_file" ]; then
        print_error "Fichier Docker Compose non trouvé: $compose_file"
        exit 1
    fi
    
    # Build and start services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$compose_file" down --remove-orphans
        docker-compose -f "$compose_file" build --no-cache
        docker-compose -f "$compose_file" up -d
    else
        docker compose -f "$compose_file" down --remove-orphans
        docker compose -f "$compose_file" build --no-cache
        docker compose -f "$compose_file" up -d
    fi
    
    print_success "Services déployés"
}

# Health check
health_check() {
    print_status "Vérification de la santé des services..."
    
    sleep 30  # Wait for services to start
    
    # Check if containers are running
    local containers=("wakedock-core" "wakedock-dashboard" "wakedock-caddy" "wakedock-postgres" "wakedock-redis")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            print_success "✓ $container est en cours d'exécution"
        else
            print_error "✗ $container n'est pas en cours d'exécution"
        fi
    done
    
    # Test API endpoint
    print_status "Test de l'endpoint API..."
    
    local max_retries=10
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if curl -s -f http://localhost:5000/api/v1/health > /dev/null 2>&1; then
            print_success "✓ API backend accessible"
            break
        else
            retry=$((retry + 1))
            if [ $retry -eq $max_retries ]; then
                print_warning "✗ API backend non accessible après $max_retries tentatives"
            else
                print_status "Tentative $retry/$max_retries - API backend non encore prête, attente..."
                sleep 5
            fi
        fi
    done
    
    # Test frontend
    print_status "Test du frontend..."
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "✓ Frontend accessible"
    else
        print_warning "✗ Frontend non accessible"
    fi
    
    # Test proxy
    print_status "Test du proxy Caddy..."
    if curl -s -f http://localhost > /dev/null 2>&1; then
        print_success "✓ Proxy Caddy accessible"
    else
        print_warning "✗ Proxy Caddy non accessible"
    fi
}

# Show status
show_status() {
    print_status "État des services:"
    echo ""
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "docker-compose-local-multi-repo.yml" ps
    else
        docker compose -f "docker-compose-local-multi-repo.yml" ps
    fi
    
    echo ""
    print_status "URLs d'accès:"
    echo "🌐 Interface Web: http://localhost"
    echo "🚀 API Backend: http://localhost:5000"
    echo "🎨 Frontend: http://localhost:3000"
    echo "⚙️  Admin Caddy: http://localhost:2019"
    echo ""
    print_status "Logs en temps réel:"
    echo "docker-compose -f docker-compose-local-multi-repo.yml logs -f"
}

# Main function
main() {
    echo "🐳 WakeDock Multi-Repo Deployment"
    echo "=================================="
    echo ""
    
    case "${1:-deploy}" in
        "deploy"|"up")
            check_dependencies
            create_directories
            setup_network
            update_repositories
            deploy_services
            health_check
            show_status
            ;;
        "update")
            update_repositories
            deploy_services
            health_check
            ;;
        "stop"|"down")
            print_status "Arrêt des services..."
            if command -v docker-compose &> /dev/null; then
                docker-compose -f "docker-compose-local-multi-repo.yml" down
            else
                docker compose -f "docker-compose-local-multi-repo.yml" down
            fi
            print_success "Services arrêtés"
            ;;
        "status")
            show_status
            ;;
        "logs")
            if command -v docker-compose &> /dev/null; then
                docker-compose -f "docker-compose-local-multi-repo.yml" logs -f
            else
                docker compose -f "docker-compose-local-multi-repo.yml" logs -f
            fi
            ;;
        "clean")
            print_warning "Nettoyage complet (suppression des volumes)..."
            if command -v docker-compose &> /dev/null; then
                docker-compose -f "docker-compose-local-multi-repo.yml" down -v --remove-orphans
            else
                docker compose -f "docker-compose-local-multi-repo.yml" down -v --remove-orphans
            fi
            docker system prune -f
            print_success "Nettoyage terminé"
            ;;
        "help"|"--help"|"-h")
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  deploy, up    Déployer tous les services (défaut)"
            echo "  update        Mettre à jour les dépôts et redéployer"
            echo "  stop, down    Arrêter tous les services"
            echo "  status        Afficher le statut des services"
            echo "  logs          Afficher les logs en temps réel"
            echo "  clean         Nettoyage complet (supprime les volumes)"
            echo "  help          Afficher cette aide"
            ;;
        *)
            print_error "Commande inconnue: $1"
            echo "Utilisez '$0 help' pour voir les commandes disponibles"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
