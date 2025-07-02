# 🐳 WakeDock - Modern Docker Management Platform

![WakeDock Banner](https://img.shields.io/badge/WakeDock-Docker%20Management-blue?style=for-the-badge&logo=docker)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://docker.com)

**WakeDock** is a comprehensive Docker container management platform featuring a modern web interface, powerful API, and enterprise-grade capabilities. Built with Python FastAPI backend and SvelteKit frontend, it provides intuitive container orchestration with real-time monitoring and advanced security features.

## 🌟 Key Features

### 🎨 Modern Web Interface
- **Beautiful Dashboard**: Glassmorphism design with responsive layouts
- **Real-time Updates**: WebSocket-powered live container status
- **Dark/Light Themes**: Adaptive UI with system preference detection
- **Mobile-first**: Touch-friendly interface for all devices
- **Accessibility**: WCAG 2.1 compliant with screen reader support

### 🐳 Container Management
- **Full Lifecycle Control**: Create, start, stop, restart, and remove containers
- **Real-time Monitoring**: CPU, memory, network, and disk usage metrics
- **Log Streaming**: Live container logs with search and filtering
- **Bulk Operations**: Manage multiple containers simultaneously
- **Health Checks**: Automated container health monitoring

### 🚀 Advanced Features
- **Image Management**: Pull, build, and organize Docker images
- **Network Control**: Create and manage Docker networks
- **Volume Management**: Persistent storage administration
- **Compose Support**: Docker Compose project management
- **Security Scanning**: Container vulnerability assessments

### 🔒 Security & Authentication
- **JWT Authentication**: Secure token-based user sessions
- **Role-based Access**: Admin, user, and viewer permission levels
- **CSRF Protection**: Cross-site request forgery prevention
- **Rate Limiting**: API abuse prevention
- **Audit Logging**: Complete action tracking and compliance

### 📊 Monitoring & Analytics
- **System Metrics**: Host resource monitoring
- **Performance Dashboards**: Grafana integration for advanced analytics
- **Alerting**: Custom thresholds and notifications
- **Export Capabilities**: Metrics data export for external analysis

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ with Docker Compose v2
- **2GB+ RAM** (4GB+ recommended for production)
- **Linux/macOS/Windows** with WSL2 support

### One-Command Deployment

```bash
# Clone and start WakeDock
git clone https://github.com/your-org/wakedock.git
cd wakedock
cp .env.example .env
docker-compose up -d

# Access the dashboard
open http://localhost:3000
```

### Production Deployment

```bash
# Production setup with HTTPS
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📁 Project Structure

```
wakedock/
├── src/wakedock/           # Python FastAPI backend
│   ├── api/               # REST API endpoints
│   ├── core/             # Business logic
│   ├── database/         # Data models & migrations
│   └── auth/             # Authentication system
├── dashboard/            # SvelteKit frontend
│   ├── src/
│   │   ├── lib/         # Shared components & utilities
│   │   ├── routes/      # Page components
│   │   └── stores/      # State management
│   └── static/          # Static assets
├── caddy/               # Reverse proxy configuration
├── docs/                # Comprehensive documentation
│   ├── architecture/    # System architecture
│   ├── api/            # API reference
│   ├── development/    # Development guide
│   └── deployment/     # Deployment instructions
├── examples/           # Example configurations
└── monitoring/         # Prometheus & Grafana configs
```

## 🎨 UI Showcase

### Modern Dashboard Design
- **Glassmorphism Effects**: Translucent cards with blur backgrounds
- **Micro-animations**: Smooth transitions and interactive feedback
- **Component Library**: Consistent design system across all interfaces
- **Data Visualization**: Interactive charts and real-time metrics

### Enhanced Components
- **📊 StatsCards**: Real-time metrics with trend indicators
- **🔧 ServiceCard**: Modern container management interface
- **🧭 Navigation**: Smart sidebar with contextual actions
- **📱 Responsive**: Mobile-optimized touch interactions

## 🛠️ Development

### Backend Development

```bash
# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Run development server
python manage.py dev
```

### Frontend Development

```bash
# Set up Node.js environment
cd dashboard
npm install

# Start development server
npm run dev
```

### Testing

```bash
# Backend tests
pytest tests/

# Frontend tests
cd dashboard && npm run test

# End-to-end tests
npm run test:e2e
```

## 📚 Documentation

| Documentation | Description |
|---------------|-------------|
| [🏗️ Architecture](docs/architecture/README.md) | System design and component overview |
| [🔧 Development](docs/development/SETUP.md) | Development environment setup |
| [🚀 Deployment](docs/deployment/README.md) | Production deployment guide |
| [📡 API Reference](docs/api/README.md) | Complete API documentation |
| [📋 Contributing](CONTRIBUTING.md) | Contribution guidelines |
| [📝 Changelog](CHANGELOG.md) | Release notes and changes |

## 🎯 Use Cases

### Development Teams
- **Local Development**: Manage development containers and services
- **CI/CD Integration**: Container deployment automation
- **Team Collaboration**: Shared development environments

### DevOps & Operations
- **Production Monitoring**: Real-time container health and metrics
- **Infrastructure Management**: Multi-host Docker orchestration
- **Incident Response**: Quick container troubleshooting and recovery

### Enterprise Deployment
- **Multi-tenant Isolation**: Role-based access and resource limits
- **Compliance Reporting**: Audit logs and security monitoring
- **High Availability**: Load balancing and failover capabilities

## 🏆 Why Choose WakeDock?

### vs. Portainer
- ✅ **Modern UI/UX**: Responsive design with better mobile support
- ✅ **Real-time Updates**: WebSocket-powered live data
- ✅ **Better Security**: Enhanced authentication and RBAC
- ✅ **API-first**: Comprehensive REST API with OpenAPI docs

### vs. Docker Desktop
- ✅ **Web-based**: No desktop app required, works anywhere
- ✅ **Multi-host**: Manage containers across multiple servers
- ✅ **Team Collaboration**: Multi-user access with permissions
- ✅ **Advanced Monitoring**: Built-in metrics and alerting

### vs. Custom Solutions
- ✅ **Production Ready**: Battle-tested with enterprise features
- ✅ **Easy Deployment**: One-command setup with Docker Compose
- ✅ **Comprehensive**: Complete container lifecycle management
- ✅ **Extensible**: Plugin architecture for custom integrations

## 🔧 Configuration

### Environment Variables

```bash
# Core configuration
WAKEDOCK_CORE_PORT=8000
DASHBOARD_PORT=3000
WAKEDOCK_LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-super-secret-key
CORS_ORIGINS=https://yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host/db
# or SQLite: sqlite:///data/wakedock.db

# Docker
DOCKER_SOCKET_PATH=/var/run/docker.sock

# Monitoring (optional)
ENABLE_MONITORING=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

### Config File

```yaml
# config/config.yml
wakedock:
  host: 0.0.0.0
  port: 8000
  data_path: /app/data

database:
  url: ${DATABASE_URL}
  pool_size: 10

logging:
  level: INFO
  file: /app/logs/wakedock.log

security:
  jwt_secret: ${JWT_SECRET_KEY}
  cors_origins: ${CORS_ORIGINS}
```

## 📊 Monitoring Integration

### Prometheus Metrics
- Container resource usage
- API request metrics
- System health indicators
- Custom business metrics

### Grafana Dashboards
- Pre-built container monitoring dashboards
- System overview and drill-down views
- Alert configuration and notification rules

## 🔐 Security Features

### Authentication & Authorization
- **JWT Token Authentication**: Secure session management
- **Role-based Access Control**: Granular permission system
- **Multi-factor Authentication**: Optional 2FA support
- **Session Management**: Automatic token refresh and expiry

### Security Hardening
- **HTTPS Enforcement**: Automatic SSL certificate management
- **CSRF Protection**: Cross-site request forgery prevention
- **Input Validation**: Comprehensive request sanitization
- **Rate Limiting**: API abuse prevention

## 🌍 Community & Support

### Getting Help
- 📖 **Documentation**: Comprehensive guides and API reference
- 💬 **Discord**: Community chat and real-time support
- 🐛 **GitHub Issues**: Bug reports and feature requests
- 📧 **Email**: enterprise@wakedock.com for business inquiries

### Contributing
We welcome contributions from the community! See our [Contributing Guide](CONTRIBUTING.md) for:
- Development setup instructions
- Code style and standards
- Pull request process
- Issue reporting guidelines

## 📜 License

WakeDock is released under the [MIT License](LICENSE). See the LICENSE file for complete terms and conditions.

## 🙏 Acknowledgments

WakeDock is built with and inspired by many excellent open source projects:

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[SvelteKit](https://kit.svelte.dev/)** - Full-stack web framework
- **[Docker](https://docker.com)** - Containerization platform
- **[Caddy](https://caddyserver.com/)** - Automatic HTTPS web server
- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework

---

<div align="center">

**[🌟 Star us on GitHub](https://github.com/your-org/wakedock)** | **[📋 Report Issues](https://github.com/your-org/wakedock/issues)** | **[💬 Join Discord](https://discord.gg/wakedock)**

Made with ❤️ by the WakeDock team

</div>

### 🚀 **Enhanced Dashboard**
- **Hero Section**: Impressive landing area with animated background
- **Quick Actions**: Fast access to common tasks
- **Advanced Filtering**: Search and status filtering
- **Loading States**: Skeleton loaders and shimmer effects
- **Empty States**: Helpful guidance when no data

## 🛠️ Technical Improvements

### 📦 **Component Architecture**
```typescript
// Modern Svelte components with TypeScript
// Enhanced props and event handling
// Better state management
// Improved accessibility
```

### 🎨 **CSS Features**
- **CSS Custom Properties**: `--color-primary`, `--radius`, `--spacing-*`
- **Modern Layout**: CSS Grid and Flexbox
- **Backdrop Filters**: Glass effect support
- **CSS Animations**: Keyframe animations for smooth UX
- **Responsive Units**: `clamp()`, `min()`, `max()` for fluid design

### 🔧 **Development Experience**
- **TypeScript**: Full type safety
- **Component Props**: Well-defined interfaces
- **Event Handling**: Proper event dispatching
- **Error Boundaries**: Graceful error handling

## 📸 UI Showcase

### 🏠 Dashboard
- Hero section with system overview
- Statistics cards with trends
- Service management grid
- Quick action shortcuts

### 📋 Service Management
- Service cards with resource metrics
- Interactive status controls
- Detailed service information
- Port mapping visualization

### 🔍 Enhanced Navigation
- Collapsible sidebar with system status
- Header with search and notifications
- User menu with profile options
- Theme switching capabilities

## 🚀 Getting Started

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📱 Responsive Breakpoints

```css
/* Mobile First */
@media (max-width: 480px)  { /* Mobile */ }
@media (max-width: 768px)  { /* Tablet */ }
@media (max-width: 1024px) { /* Small Desktop */ }
@media (min-width: 1025px) { /* Large Desktop */ }
```

## 🎨 Design Tokens

### Colors
```css
--color-primary: #3b82f6;       /* Primary blue */
--color-success: #10b981;       /* Success green */
--color-warning: #f59e0b;       /* Warning orange */
--color-error: #ef4444;         /* Error red */
```

### Spacing
```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
```

### Border Radius
```css
--radius: 0.75rem;       /* Standard radius */
--radius-lg: 1rem;       /* Large radius */
--radius-xl: 1.5rem;     /* Extra large radius */
--radius-full: 9999px;   /* Circular */
```

## 🔧 Component Props

### ServiceCard
```typescript
interface ServiceCardProps {
  service: {
    id: string;
    name: string;
    subdomain: string;
    status: 'running' | 'stopped' | 'starting' | 'error';
    docker_image?: string;
    ports: string[];
    resource_usage?: {
      cpu_percent: number;
      memory_usage: number;
      memory_percent: number;
    };
  };
}
```

### StatsCards
```typescript
interface StatsCardsProps {
  stats: {
    services: ServiceStats;
    system: SystemStats;
    docker: DockerInfo;
    caddy: CaddyInfo;
  };
}
```

## 🎯 Key Features

### ⚡ Performance
- **Optimized Animations**: 60fps smooth animations
- **Lazy Loading**: Components load when needed
- **Efficient Rendering**: Minimal re-renders
- **Small Bundle Size**: Optimized build

### ♿ Accessibility
- **ARIA Labels**: Screen reader support
- **Keyboard Navigation**: Full keyboard support
- **Focus Management**: Proper focus indicators
- **Color Contrast**: WCAG compliant colors

### 🔒 Security
- **XSS Protection**: Sanitized inputs
- **CSRF Protection**: Token-based security
- **Secure Headers**: Content security policies

## 🔄 State Management

```typescript
// Reactive stores with Svelte
import { writable, derived } from 'svelte/store';

// Theme management
const theme = writable('light');

// Service state
const services = writable([]);
const filteredServices = derived(
  [services, searchTerm], 
  ([$services, $searchTerm]) => 
    $services.filter(s => s.name.includes($searchTerm))
);
```

## 🎨 Animation System

```css
/* Smooth transitions */
.card {
  transition: all var(--transition-normal);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
}

/* Loading animations */
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

## 🌟 Browser Support

- **Chrome**: ✅ Full support
- **Firefox**: ✅ Full support  
- **Safari**: ✅ Full support
- **Edge**: ✅ Full support
- **Mobile**: ✅ Responsive design

## 📚 Documentation

- [Component Library](./docs/components.md)
- [Design System](./docs/design-system.md)
- [API Reference](./docs/api.md)
- [Deployment Guide](./docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test across devices
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Svelte/SvelteKit**: Amazing framework
- **Lucide Icons**: Beautiful icon library
- **Inter Font**: Excellent typography
- **Tailwind CSS**: Utility-first CSS framework

---

<div align="center">

**Made with ❤️ for the Docker community**

[Website](https://wakedock.com) • [Documentation](https://docs.wakedock.com) • [GitHub](https://github.com/wakedock/wakedock)

</div>