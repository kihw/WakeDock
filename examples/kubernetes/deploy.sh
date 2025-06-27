#!/bin/bash

# WakeDock Kubernetes Deployment Script
# This script deploys WakeDock to a Kubernetes cluster

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="wakedock"
DOMAIN="${WAKEDOCK_DOMAIN:-wakedock.example.com}"
ENVIRONMENT="${WAKEDOCK_ENV:-production}"
KUBECTL_CONTEXT="${KUBECTL_CONTEXT:-}"

# Functions
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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize not found, using kubectl apply -k"
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_namespace() {
    log_info "Setting up namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace $NAMESPACE created"
    fi
}

generate_secrets() {
    log_info "Generating secrets..."
    
    # Generate random passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    JWT_SECRET=$(openssl rand -base64 64)
    ADMIN_PASSWORD=$(openssl rand -base64 16)
    API_KEY=$(openssl rand -hex 32)
    
    # Create secret manifest
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: wakedock-secrets
  namespace: $NAMESPACE
type: Opaque
data:
  postgres-user: $(echo -n "wakedock" | base64)
  postgres-password: $(echo -n "$POSTGRES_PASSWORD" | base64)
  database-url: $(echo -n "postgresql+psycopg2://wakedock:$POSTGRES_PASSWORD@postgresql:5432/wakedock" | base64)
  redis-password: $(echo -n "$REDIS_PASSWORD" | base64)
  redis-url: $(echo -n "redis://:$REDIS_PASSWORD@redis:6379" | base64)
  jwt-secret: $(echo -n "$JWT_SECRET" | base64)
  admin-password: $(echo -n "$ADMIN_PASSWORD" | base64)
  api-key: $(echo -n "$API_KEY" | base64)
EOF
    
    log_success "Secrets generated and applied"
    
    # Save credentials to file
    cat <<EOF > wakedock-credentials.txt
WakeDock Deployment Credentials
==============================
Generated at: $(date)
Environment: $ENVIRONMENT
Domain: $DOMAIN

Database:
- User: wakedock
- Password: $POSTGRES_PASSWORD

Redis:
- Password: $REDIS_PASSWORD

Admin:
- Password: $ADMIN_PASSWORD

API Key: $API_KEY
JWT Secret: $JWT_SECRET

IMPORTANT: Store these credentials securely and delete this file after use!
EOF
    
    log_warning "Credentials saved to wakedock-credentials.txt - please secure this file!"
}

deploy_components() {
    log_info "Deploying WakeDock components..."
    
    # Apply manifests in order
    local components=(
        "configmaps/"
        "rbac/"
        "services/"
        "deployments/"
        "ingress/"
        "monitoring/"
    )
    
    for component in "${components[@]}"; do
        log_info "Deploying $component..."
        kubectl apply -f "$component"|| {
            log_error "Failed to deploy $component"
            exit 1
        }
    done
    
    log_success "All components deployed"
}

wait_for_deployment() {
    log_info "Waiting for deployments to be ready..."
    
    local deployments=(
        "wakedock-backend"
        "wakedock-dashboard"
    )
    
    for deployment in "${deployments[@]}"; do
        log_info "Waiting for $deployment..."
        kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=300s || {
            log_error "Deployment $deployment failed to become ready"
            return 1
        }
    done
    
    # Wait for StatefulSets
    local statefulsets=(
        "postgresql"
        "redis"
    )
    
    for statefulset in "${statefulsets[@]}"; do
        log_info "Waiting for $statefulset..."
        kubectl rollout status statefulset/"$statefulset" -n "$NAMESPACE" --timeout=300s || {
            log_error "StatefulSet $statefulset failed to become ready"
            return 1
        }
    done
    
    log_success "All deployments are ready"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pods
    local failed_pods
    failed_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running,status.phase!=Succeeded -o name)
    
    if [[ -n "$failed_pods" ]]; then
        log_warning "Some pods are not running:"
        kubectl get pods -n "$NAMESPACE"
        return 1
    fi
    
    # Check services
    kubectl get services -n "$NAMESPACE"
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if kubectl port-forward -n "$NAMESPACE" svc/wakedock-backend 8080:8000 &
    then
        local port_forward_pid=$!
        sleep 5
        
        if curl -f http://localhost:8080/api/v1/health &> /dev/null; then
            log_success "Health endpoint is responding"
        else
            log_warning "Health endpoint is not responding"
        fi
        
        kill $port_forward_pid
    fi
    
    log_success "Deployment verification completed"
}

show_access_info() {
    log_info "WakeDock has been deployed successfully!"
    echo
    echo "Access Information:"
    echo "=================="
    echo "Domain: https://$DOMAIN"
    echo "Namespace: $NAMESPACE"
    echo
    echo "To access the dashboard:"
    echo "1. Make sure your domain DNS points to your ingress controller"
    echo "2. Visit https://$DOMAIN"
    echo
    echo "To access locally:"
    echo "kubectl port-forward -n $NAMESPACE svc/wakedock-dashboard 3000:3000"
    echo "kubectl port-forward -n $NAMESPACE svc/wakedock-backend 8000:8000"
    echo
    echo "Monitoring:"
    echo "kubectl get pods -n $NAMESPACE"
    echo "kubectl logs -f deployment/wakedock-backend -n $NAMESPACE"
    echo
    echo "Credentials are stored in: wakedock-credentials.txt"
}

cleanup() {
    log_info "Cleaning up temporary files..."
    # Clean up any temporary files if needed
}

# Main execution
main() {
    log_info "Starting WakeDock Kubernetes deployment..."
    
    # Set context if provided
    if [[ -n "$KUBECTL_CONTEXT" ]]; then
        kubectl config use-context "$KUBECTL_CONTEXT"
        log_info "Using kubectl context: $KUBECTL_CONTEXT"
    fi
    
    check_prerequisites
    setup_namespace
    generate_secrets
    deploy_components
    wait_for_deployment
    verify_deployment
    show_access_info
    cleanup
    
    log_success "WakeDock deployment completed successfully!"
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
