# Production Deployment Examples

This directory contains example configurations for deploying WakeDock in production environments.

## Examples Available

### 1. Docker Compose Production (`docker-compose/`)
- Full production setup with all services
- HTTPS with Let's Encrypt
- Redis for caching and rate limiting
- PostgreSQL database
- Monitoring with Prometheus and Grafana

### 2. Kubernetes Deployment (`kubernetes/`)
- Complete Kubernetes manifests
- Ingress configuration with cert-manager
- StatefulSets for databases
- ConfigMaps and Secrets management
- Resource limits and requests

### 3. Ansible Playbooks (`ansible/`)
- Automated deployment scripts
- Server provisioning
- SSL certificate management
- Database setup and migration
- Service configuration

## Quick Start

### Docker Compose Production

```bash
# Copy and customize the production configuration
cp examples/production/docker-compose/docker-compose.yml .
cp examples/production/docker-compose/.env.example .env

# Edit the environment variables
nano .env

# Start the production environment
docker-compose up -d
```

### Kubernetes

```bash
# Apply the Kubernetes manifests
kubectl apply -f examples/production/kubernetes/

# Check the deployment status
kubectl get pods -n wakedock
```

### Ansible

```bash
# Install dependencies
ansible-galaxy install -r examples/production/ansible/requirements.yml

# Run the playbook
ansible-playbook -i inventory examples/production/ansible/deploy.yml
```

## Security Considerations

- Always change default passwords
- Use strong SSL certificates
- Configure proper firewall rules
- Enable monitoring and alerting
- Regular security updates
- Backup strategy implementation

## Scaling

Each example includes guidance on:
- Horizontal scaling options
- Load balancing configuration
- Database clustering
- Monitoring and observability
- Performance tuning

## Support

For production deployment support, please:
1. Check the documentation in `docs/deployment.md`
2. Review the troubleshooting guide in `docs/troubleshooting.md`
3. Open an issue on GitHub with your specific deployment scenario
