# WakeDock Kubernetes Deployment

This directory contains Kubernetes manifests for deploying WakeDock in a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- Helm 3.x (optional, for easier deployment)
- cert-manager (for SSL certificates)
- Ingress controller (nginx, traefik, etc.)

## Quick Deployment

### Automated Deployment (Recommended)

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Deploy with default settings
./deploy.sh

# Deploy with custom domain
WAKEDOCK_DOMAIN=your-domain.com ./deploy.sh

# Deploy to specific cluster context
KUBECTL_CONTEXT=your-context ./deploy.sh
```

### Manual Deployment

```bash
# Apply all manifests in order
kubectl apply -f namespace.yaml
kubectl apply -f configmaps/
kubectl apply -f secrets/
kubectl apply -f rbac/
kubectl apply -f services/
kubectl apply -f deployments/
kubectl apply -f ingress/
kubectl apply -f monitoring/

# Or use kustomize
kubectl apply -k .

# Wait for deployments
kubectl rollout status deployment/wakedock-backend -n wakedock
kubectl rollout status deployment/wakedock-dashboard -n wakedock
kubectl rollout status statefulset/postgresql -n wakedock
kubectl rollout status statefulset/redis -n wakedock
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Ingress        │    │  WakeDock       │    │  Dashboard      │
│  (SSL/TLS)      │────│  Backend        │────│  Frontend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                       │
                       ┌───────┴───────┐      ┌───────┴───────┐
                       │  PostgreSQL   │      │  Redis        │
                       │  (StatefulSet) │      │  (StatefulSet)│
                       └───────────────┘      └───────────────┘
```

## Components

### Core Services
- **WakeDock Backend**: Main application (Deployment)
- **Dashboard Frontend**: Web interface (Deployment)
- **PostgreSQL**: Database (StatefulSet)
- **Redis**: Cache and rate limiting (StatefulSet)

## Components

### Core Services
- **WakeDock Backend**: Main application (Deployment)
- **Dashboard Frontend**: Web interface (Deployment)
- **PostgreSQL**: Database (StatefulSet)
- **Redis**: Cache and rate limiting (StatefulSet)

### Supporting Services
- **Ingress Controller**: NGINX for external access
- **cert-manager**: SSL certificate management
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboard

### Security Features
- **RBAC**: Role-based access control
- **Network Policies**: Pod-to-pod communication control
- **Security Contexts**: Container security settings
- **TLS/SSL**: Encrypted communication

### Monitoring & Observability
- **Prometheus Metrics**: Application and infrastructure metrics
- **Grafana Dashboards**: Visual monitoring
- **Alerting Rules**: Automated alert notifications
- **Health Checks**: Liveness and readiness probes

## File Structure

```
kubernetes/
├── deploy.sh                 # Automated deployment script
├── kustomization.yaml        # Kustomize configuration
├── namespace.yaml           # Namespace definition
├── configmaps/
│   └── wakedock-config.yaml # Application configuration
├── secrets/
│   └── secrets.yaml         # Sensitive data (template)
├── rbac/
│   └── rbac.yaml           # Role-based access control
├── services/
│   └── services.yaml       # Service definitions
├── deployments/
│   ├── wakedock-backend.yaml
│   ├── wakedock-dashboard.yaml
│   ├── postgresql.yaml
│   └── redis.yaml
├── ingress/
│   └── ingress.yaml        # External access configuration
└── monitoring/
    └── monitoring.yaml     # Prometheus rules and dashboards
```
- **Ingress**: HTTPS termination and routing
- **ConfigMaps**: Configuration management
- **Secrets**: Sensitive data storage
- **ServiceMonitor**: Prometheus monitoring
- **PodDisruptionBudget**: High availability

### Optional Components
- **Grafana**: Metrics visualization
- **Prometheus**: Metrics collection
- **Backup CronJob**: Automated backups

## Configuration

1. **Edit ConfigMaps**: Update `configmaps/wakedock-config.yaml`
2. **Set Secrets**: Update `secrets/wakedock-secrets.yaml` 
3. **Configure Ingress**: Update `ingress/wakedock-ingress.yaml`
4. **Scale Resources**: Adjust resource limits in deployments

## Monitoring

The deployment includes:
- Health checks for all services
- Prometheus ServiceMonitors
- Grafana dashboards
- Resource monitoring

## High Availability

For production HA setup:
- Scale replicas: `kubectl scale deployment wakedock --replicas=3`
- Use PostgreSQL cluster (not included)
- Configure Redis Sentinel (not included)
- Multiple ingress controllers

## Troubleshooting

```bash
# Check pod status
kubectl get pods -n wakedock

# View logs
kubectl logs -f deployment/wakedock -n wakedock

# Check events
kubectl get events -n wakedock --sort-by='.lastTimestamp'

# Port forward for testing
kubectl port-forward svc/wakedock 8000:8000 -n wakedock
```

## Customization

- **Storage**: Update StorageClass in StatefulSets
- **Resources**: Adjust CPU/memory limits
- **Networking**: Configure NetworkPolicies
- **Security**: Set PodSecurityPolicies
- **Backup**: Configure backup storage

## Advanced Configuration

### Environment Variables

Configure your deployment by setting these environment variables:

```bash
# Required
export WAKEDOCK_DOMAIN="your-domain.com"
export WAKEDOCK_ENV="production"

# Optional
export KUBECTL_CONTEXT="your-k8s-context"
export WAKEDOCK_REPLICAS_BACKEND="2"
export WAKEDOCK_REPLICAS_DASHBOARD="2"
export POSTGRES_STORAGE_SIZE="20Gi"
export REDIS_STORAGE_SIZE="5Gi"
```

### SSL/TLS Configuration

For production, configure SSL certificates:

1. **Using cert-manager (Recommended)**:
   ```bash
   # Install cert-manager
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   
   # Create ClusterIssuer
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-prod
   spec:
     acme:
       server: https://acme-v02.api.letsencrypt.org/directory
       email: your-email@example.com
       privateKeySecretRef:
         name: letsencrypt-prod
       solvers:
       - http01:
           ingress:
             class: nginx
   EOF
   ```

### Scaling

Scale deployments based on load:

```bash
# Scale backend
kubectl scale deployment wakedock-backend --replicas=3 -n wakedock

# Auto-scaling
kubectl autoscale deployment wakedock-backend \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n wakedock
```

### Cleanup

To completely remove WakeDock:

```bash
# Delete all resources
kubectl delete namespace wakedock

# Or use the manifests
kubectl delete -k .
```

---

For more information, see the main [WakeDock documentation](../../docs/).
