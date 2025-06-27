# WakeDock Ansible Deployment

This directory contains Ansible playbooks for automated deployment of WakeDock across different environments and platforms.

## Overview

These playbooks provide fully automated deployment of WakeDock with:
- Multi-environment support (development, staging, production)
- Docker and Docker Compose setup
- Kubernetes deployment automation
- SSL certificate management
- Monitoring setup
- Backup configuration

## Prerequisites

- Ansible 2.9+
- Python 3.7+
- SSH access to target hosts
- Docker and Docker Compose (for Docker deployments)
- kubectl configured (for Kubernetes deployments)

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ansible-galaxy install -r requirements.yml
   ```

2. **Configure inventory**:
   ```bash
   cp inventory/hosts.example inventory/hosts
   # Edit inventory/hosts with your server details
   ```

3. **Set up group variables**:
   ```bash
   cp group_vars/all.yml.example group_vars/all.yml
   # Edit group_vars/all.yml with your configuration
   ```

4. **Deploy**:
   ```bash
   # Docker deployment
   ansible-playbook -i inventory/hosts site.yml
   
   # Kubernetes deployment
   ansible-playbook -i inventory/hosts kubernetes.yml
   ```

## Playbook Structure

```
ansible/
├── site.yml                    # Main playbook
├── kubernetes.yml              # Kubernetes deployment
├── requirements.yml            # Ansible Galaxy requirements
├── requirements.txt            # Python requirements
├── ansible.cfg                 # Ansible configuration
├── inventory/
│   ├── hosts.example          # Inventory template
│   └── group_vars/            # Group variables
├── roles/
│   ├── common/                # Common setup
│   ├── docker/                # Docker installation
│   ├── wakedock/              # WakeDock application
│   ├── monitoring/            # Monitoring setup
│   └── security/              # Security hardening
├── playbooks/
│   ├── setup.yml              # Initial server setup
│   ├── deploy.yml             # Application deployment
│   ├── update.yml             # Updates and maintenance
│   └── backup.yml             # Backup operations
└── files/
    └── templates/             # Configuration templates
```

## Supported Deployments

### Docker Compose
- Single-node deployment
- Multi-container setup
- Volume management
- Network configuration

### Kubernetes
- Multi-node clusters
- Helm chart deployment
- Custom resource management
- Ingress configuration

### Bare Metal
- Direct service installation
- SystemD service management
- Nginx reverse proxy
- SSL termination

## Environments

### Development
```bash
ansible-playbook -i inventory/dev site.yml
```

### Staging
```bash
ansible-playbook -i inventory/staging site.yml
```

### Production
```bash
ansible-playbook -i inventory/prod site.yml
```

## Configuration

Key configuration files:
- `group_vars/all.yml`: Global settings
- `group_vars/{environment}.yml`: Environment-specific settings  
- `host_vars/{hostname}.yml`: Host-specific settings

## Monitoring

Automatically sets up:
- Prometheus metrics collection
- Grafana dashboards
- Log aggregation
- Alert notifications

## Security

Includes security hardening:
- Firewall configuration
- SSL certificate setup
- User management
- Key-based authentication

## Backup

Automated backup setup:
- Database backups
- Configuration backups
- Log rotation
- Remote storage sync

---

For detailed usage instructions, see the playbook-specific documentation in each directory.
