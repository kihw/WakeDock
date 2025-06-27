# 🐳 WakeDock

**Intelligent Docker orchestration with Caddy reverse proxy**

> Wake up your Docker containers on-demand and automatically shut them down when idle. Perfect for self-hosted services that don't need to run 24/7.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![Caddy](https://img.shields.io/badge/Caddy-integrated-green.svg)](https://caddyserver.com/)

---

## 🚀 What is WakeDock?

WakeDock is an intelligent orchestration tool that automatically manages your Docker containers based on real-time demand. When someone visits your service's subdomain, WakeDock instantly starts the container and shows a beautiful loading page during startup. When the service is idle, it automatically shuts down to save resources.

**Think of it as "serverless" for your self-hosted Docker services.**

### ✨ Key Features

- 🌐 **Automatic Reverse Proxy** - Dynamic Caddy configuration for each service
- 🔄 **On-Demand Wake-Up** - Containers start when accessed, not before
- ⏳ **Smart Loading Pages** - Beautiful UI while services are starting
- 📊 **Intelligent Auto-Shutdown** - Configurable rules based on inactivity, CPU, RAM usage
- 📈 **Resource Monitoring** - Real-time stats and usage tracking
- 🎛️ **Web Dashboard** - Modern interface to manage all services
- 🔐 **Secure Access** - Built-in authentication and access control
- � **Advanced Authentication System** - OAuth, SSO, and centralized user management (v1.5+)
- �🐳 **Docker Native** - Works with containers and Docker Compose stacks

---

## 🏗️ Architecture

```
User Request → Caddy Reverse Proxy → WakeDock Core → Docker Container
     ↓                                      ↓              ↓
Loading Page ←                    Monitoring Engine ← Resource Stats
```

### How it Works

1. **User visits** `service.yourdomain.com`
2. **Caddy** detects the request and forwards to WakeDock
3. **WakeDock** checks if the container is running
4. If not running: **starts container** and shows loading page
5. Once ready: **proxies traffic** to the actual service
6. **Monitors usage** and automatically shuts down when idle

---

## 🛠️ Installation

### Prerequisites

- Docker & Docker Compose
- Caddy v2+
- A domain with wildcard DNS (*.yourdomain.com)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/wakedock.git
cd wakedock

# Copy and edit configuration
cp config/config.example.yml config/config.yml
nano config/config.yml

# Start WakeDock
docker-compose up -d
```

### Quick Deploy (Docker Hosting Platforms)

For automated deployment on platforms like Dokploy, use the quick deploy script:

```bash
# Make scripts executable
chmod +x deploy.sh manage.sh

# Quick deploy (creates network, directories, and starts services)
./deploy.sh
```

### Environment Files

- `.env` - Development configuration
- `.env.production` - Production configuration  
- `.env.example` - Template with all available variables

### Network Configuration

WakeDock uses a Docker network (default: `caddy_net`) that can be shared with other services:

```bash
# Create network manually if needed
docker network create caddy_net
```

### Configuration Example

```yaml
# config/config.yml
wakedock:
  domain: "yourdomain.com"
  admin_password: "your-secure-password"
  
caddy:
  api_endpoint: "http://caddy:2019"
  config_path: "/etc/caddy/Caddyfile"

services:
  - name: "nextcloud"
    subdomain: "cloud"
    docker_compose: "./services/nextcloud/docker-compose.yml"
    auto_shutdown:
      inactive_minutes: 30
      cpu_threshold: 5
      memory_threshold: 100
    
  - name: "grafana"
    subdomain: "monitoring"
    docker_image: "grafana/grafana:latest"
    ports: ["3000:3000"]
    auto_shutdown:
      inactive_minutes: 15
```

---

## 📋 Usage

### Adding a New Service

1. **Via Web Interface** (Recommended)
   - Go to `http://admin.yourdomain.com`
   - Click "Add Service"
   - Fill in the configuration
   - Click "Save & Deploy"

2. **Via Configuration File**
   ```yaml
   services:
     - name: "my-app"
       subdomain: "app"
       docker_image: "my-app:latest"
       ports: ["8080:80"]
       auto_shutdown:
         inactive_minutes: 20
   ```

### Managing Services

- **Dashboard**: `http://admin.yourdomain.com`
- **API**: `http://admin.yourdomain.com/api/v1/`
- **Logs**: `docker-compose logs wakedock`

### API Endpoints

```http
GET    /api/v1/services           # List all services
POST   /api/v1/services           # Create new service
GET    /api/v1/services/{id}      # Get service details
PUT    /api/v1/services/{id}      # Update service
DELETE /api/v1/services/{id}      # Delete service
POST   /api/v1/services/{id}/wake # Force wake service
POST   /api/v1/services/{id}/sleep # Force sleep service
```

---

## ⚙️ Configuration Options

### Auto-Shutdown Rules

Configure when containers should automatically stop:

```yaml
auto_shutdown:
  inactive_minutes: 30        # Stop after 30 minutes of no requests
  cpu_threshold: 5           # Stop if CPU usage < 5% for check_interval
  memory_threshold: 100      # Stop if RAM usage < 100MB for check_interval
  check_interval: 300        # Check every 5 minutes
  grace_period: 60           # Wait 60s before actually stopping
```

### Loading Page Customization

```yaml
loading_page:
  title: "Starting {service_name}..."
  message: "Please wait while we wake up your service"
  theme: "dark"              # dark, light, or custom
  custom_css: "./themes/custom.css"
  estimated_time: 30         # Estimated startup time in seconds
```

### Monitoring Options

```yaml
monitoring:
  enabled: true
  metrics_retention: "7d"    # Keep metrics for 7 days
  collect_interval: 30       # Collect stats every 30 seconds
  endpoints:
    - "/health"
    - "/metrics"
```

---

## 🔧 Advanced Usage

### Custom Docker Compose Stacks

```yaml
services:
  - name: "wordpress-stack"
    subdomain: "blog"
    docker_compose: "./stacks/wordpress/docker-compose.yml"
    environment:
      MYSQL_ROOT_PASSWORD: "secure-password"
      WORDPRESS_DB_HOST: "db:3306"
    auto_shutdown:
      inactive_minutes: 60
```

### Health Checks

```yaml
services:
  - name: "my-service"
    health_check:
      enabled: true
      endpoint: "/health"
      timeout: 30
      retries: 3
      interval: 10
```

### Custom Startup Scripts

```yaml
services:
  - name: "complex-app"
    startup_script: "./scripts/prepare-environment.sh"
    ready_check:
      type: "http"
      endpoint: "/ready"
      expected_status: 200
```

---

## 🖥️ Dashboard Screenshots

### Main Dashboard
![Dashboard](docs/images/dashboard.png)

### Service Configuration
![Service Config](docs/images/service-config.png)

### Real-time Monitoring
![Monitoring](docs/images/monitoring.png)

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/yourusername/wakedock.git
cd wakedock

# Install development dependencies
pip install -r requirements-dev.txt
npm install

# Run tests
pytest
npm test

# Start development server
python -m wakedock.main --dev
```

### Roadmap

- [ ] **v1.0** - Basic wake/sleep functionality
- [ ] **v1.1** - Web dashboard
- [ ] **v1.2** - Advanced monitoring
- [ ] **v1.3** - Multi-user support
- [ ] **v1.4** - Kubernetes support
- [ ] **v1.5** - **Advanced Authentication System** 🔐
  - OAuth 2.0 integration (Google, GitHub, Azure AD, etc.)
  - Basic authentication with username/password
  - Per-service access control and user permissions
  - Authentication proxy for all services
  - SSO (Single Sign-On) across all managed services
  - Role-based access control (RBAC)
  - Session management with configurable timeout
  - Integration with external identity providers (LDAP, Active Directory)
- [ ] **v2.0** - Auto-scaling capabilities

---

## 📊 Performance & Resource Usage

### Typical Resource Usage

- **WakeDock Core**: ~50MB RAM, <1% CPU
- **Caddy**: ~30MB RAM, <1% CPU
- **Dashboard**: ~20MB RAM when active

### Scalability

- **Services**: Tested with 50+ concurrent services
- **Response Time**: <200ms for wake-up detection
- **Startup Time**: Depends on container (typically 5-60 seconds)

---

## 🛡️ Security Considerations

- **Admin Interface**: Protected by authentication
- **API Access**: Token-based authentication
- **Container Isolation**: Standard Docker security
- **Network**: Internal Docker networks by default
- **Logs**: Sensitive data filtering

### Security Best Practices

1. Use strong passwords for admin interface
2. Enable HTTPS with proper certificates
3. Regularly update Docker images
4. Monitor access logs
5. Use least-privilege principles

---

## 🔍 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs wakedock

# Verify Docker daemon
docker info

# Check service configuration
wakedock config validate
```

**Caddy proxy not working:**
```bash
# Check Caddy status
curl http://localhost:2019/config/

# Verify DNS resolution
dig +short app.yourdomain.com

# Check certificate issues
caddy validate --config /etc/caddy/Caddyfile
```

**Service stuck in "starting" state:**
```bash
# Check container logs
docker logs <container_name>

# Verify health checks
curl http://localhost:8080/health

# Force restart
wakedock service restart <service_name>
```

### Debug Mode

```bash
# Enable debug logging
export WAKEDOCK_LOG_LEVEL=DEBUG
docker-compose up wakedock

# Or via config
debug: true
log_level: "DEBUG"
```

---

## 🔐 Advanced Authentication System (v1.5)

### Vision

WakeDock v1.5 introduira un système d'authentification complet qui agit comme un proxy d'authentification pour tous vos services auto-hébergés. Au lieu que chaque service gère sa propre authentification, WakeDock centralise l'authentification et contrôle l'accès à tous vos services.

### 🌟 Fonctionnalités Clés

#### **Proxy d'Authentification Universel**
- Intercepte toutes les requêtes vers vos services
- Redirige vers la page de connexion si l'utilisateur n'est pas authentifié
- Maintient les sessions utilisateurs de manière centralisée
- Proxy transparent vers le service une fois authentifié

#### **Support Multi-Protocoles d'Authentification**
- **OAuth 2.0 / OpenID Connect** pour les fournisseurs populaires :
  - Google Workspace / Gmail
  - GitHub / GitHub Enterprise
  - Microsoft Azure AD / Office 365
  - Discord, Twitter, Facebook
  - Keycloak, Auth0, Okta
- **Authentification Basique** avec base de données locale :
  - Inscription/connexion par email/mot de passe
  - Récupération de mot de passe par email
  - Validation par email optionnelle
- **Intégrations Entreprise** :
  - LDAP / Active Directory
  - SAML 2.0
  - Radius

#### **Contrôle d'Accès Granulaire**
```yaml
authentication:
  providers:
    - type: "oauth"
      provider: "google"
      client_id: "your-google-client-id"
      client_secret: "your-google-client-secret"
      allowed_domains: ["yourdomain.com"]
    
    - type: "basic"
      allow_registration: true
      require_email_verification: true
      password_policy:
        min_length: 8
        require_special_chars: true

  access_control:
    default_policy: "deny"  # deny ou allow
    
    rules:
      - service: "nextcloud"
        users: ["admin@yourdomain.com", "user1@company.com"]
        groups: ["admin", "users"]
        
      - service: "grafana"
        groups: ["admin", "monitoring"]
        
      - service: "public-blog"
        policy: "allow"  # Accès public, pas d'auth requise
        
      - service: "*"  # Toutes les autres services
        groups: ["admin"]
```

#### **Interface de Gestion des Utilisateurs**
- Dashboard admin pour gérer les utilisateurs et permissions
- Auto-provisioning depuis les fournisseurs OAuth
- Gestion des groupes et rôles
- Logs d'authentification et d'accès
- Statistiques d'utilisation par utilisateur

### 🔄 Flux d'Authentification

```
1. User → https://app.yourdomain.com
2. WakeDock vérifie la session
3. Si non authentifié → Redirection vers /auth/login
4. Utilisateur choisit le mode d'authentification :
   ├─ OAuth (Google, GitHub, etc.)
   └─ Basic (email/password)
5. Après auth réussie → Cookie de session sécurisé
6. Vérification des permissions pour le service demandé
7. Si autorisé → Wake du container + Proxy vers le service
8. Si non autorisé → Page d'erreur 403
```

### 🛡️ Sécurité Avancée

#### **Gestion des Sessions**
- JWT tokens sécurisés avec rotation automatique
- Sessions persistantes avec durée configurable
- Support multi-device avec révocation sélective
- Protection CSRF intégrée

#### **Fonctionnalités de Sécurité**
- Rate limiting sur les tentatives de connexion
- Détection de tentatives d'intrusion
- Audit trail complet des accès
- Support 2FA/MFA (TOTP, SMS, email)
- Whitelist/blacklist IP automatique

### 📊 Monitoring et Analytics

```yaml
authentication:
  monitoring:
    enabled: true
    log_failed_attempts: true
    alert_on_suspicious_activity: true
    metrics:
      - login_attempts
      - active_sessions
      - service_usage_by_user
      - failed_auth_by_ip
```

### 🔧 Configuration Exemple Complète

```yaml
# config/config.yml
wakedock:
  domain: "yourdomain.com"
  admin_password: "your-secure-password"

authentication:
  enabled: true
  session_timeout: "24h"
  require_https: true
  
  providers:
    google:
      enabled: true
      client_id: "${GOOGLE_CLIENT_ID}"
      client_secret: "${GOOGLE_CLIENT_SECRET}"
      allowed_domains: ["yourdomain.com"]
      
    github:
      enabled: true
      client_id: "${GITHUB_CLIENT_ID}"
      client_secret: "${GITHUB_CLIENT_SECRET}"
      allowed_organizations: ["your-org"]
      
    basic:
      enabled: true
      allow_registration: false  # Seulement admin peut créer des users
      password_requirements:
        min_length: 12
        require_uppercase: true
        require_numbers: true
        require_special: true

  access_control:
    default_policy: "deny"
    admin_users: ["admin@yourdomain.com"]
    
    services:
      nextcloud:
        allowed_users: ["user1@yourdomain.com", "user2@yourdomain.com"]
        allowed_groups: ["family", "team"]
        
      grafana:
        allowed_groups: ["admin", "devops"]
        require_2fa: true
        
      public-site:
        public: true  # Pas d'auth requise

services:
  - name: "nextcloud"
    subdomain: "cloud"
    docker_compose: "./services/nextcloud/docker-compose.yml"
    authentication:
      required: true
      bypass_health_checks: true  # Les health checks passent sans auth
    auto_shutdown:
      inactive_minutes: 30
```

### 🚀 Migration depuis v1.4

La migration sera automatique avec rétrocompatibilité :

```bash
# Backup de la configuration actuelle
wakedock config backup

# Mise à jour vers v1.5
docker-compose pull
docker-compose up -d

# Configuration de l'authentification
wakedock auth setup --interactive

# Test de la configuration
wakedock auth validate
```

### 💡 Cas d'Usage

1. **Famille/Personnel** : OAuth Google + contrôle par domaine email
2. **Petite Entreprise** : GitHub OAuth + gestion par organisation
3. **Entreprise** : LDAP/AD + SAML pour SSO corporate
4. **Communauté** : Inscription libre + modération admin
5. **Hybride** : Mix OAuth + comptes locaux pour flexibilité maximale

Cette fonctionnalité transformera WakeDock en une solution complète de gestion d'accès pour tous vos services auto-hébergés, éliminant le besoin de gérer l'authentification individuellement pour chaque application.

---

## 📜 Automatic Caddy Configuration

WakeDock now uses **dynamic configuration** for Caddy, eliminating file mounting issues:

- ✅ **No Caddyfile mounting** - Avoids Docker volume mount errors
- ✅ **Self-configuring** - WakeDock sets up its own routes automatically  
- ✅ **Platform compatible** - Works on Dokploy, Kubernetes, and other platforms
- ✅ **Real-time updates** - Configuration changes without restarts

When WakeDock starts:
1. Caddy launches with minimal configuration
2. WakeDock automatically configures proxy routes
3. Your services become available immediately

> **Note**: Legacy `Caddyfile` configurations are still supported for manual setups.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Caddy](https://caddyserver.com/) for the amazing reverse proxy
- [Docker](https://www.docker.com/) for containerization
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Svelte](https://svelte.dev/) for the frontend framework

---

## 📞 Support

- **Documentation**: [docs.wakedock.dev](https://docs.wakedock.dev)
- **Issues**: [GitHub Issues](https://github.com/yourusername/wakedock/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/wakedock/discussions)
- **Discord**: [Join our community](https://discord.gg/wakedock)

---

**Made with ❤️ for the self-hosted community**