# WakeDock Dashboard

A modern, responsive web dashboard for managing Docker services with WakeDock. Built with SvelteKit, TypeScript, and Tailwind CSS.

## Features

- 🐳 **Docker Service Management**: Start, stop, restart, and monitor Docker services
- 👥 **User Management**: Admin interface for managing users and permissions
- 📊 **Real-time Monitoring**: Live updates via WebSocket connections
- 🔒 **Security Dashboard**: Monitor security events and configure settings
- 📈 **Analytics**: Service usage statistics and system metrics
- 🔔 **Notifications**: Real-time alerts and system notifications
- 🌙 **Dark/Light Mode**: Automatic theme detection and manual toggle
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **Framework**: SvelteKit
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Svelte stores
- **API Client**: Custom fetch-based client
- **WebSocket**: Real-time updates
- **Icons**: Heroicons
- **Build Tool**: Vite

## Development Setup

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running WakeDock API server

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd WakeDock/dashboard
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

5. **Open browser**:
   Navigate to http://localhost:5173

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# API Configuration
PUBLIC_API_URL=http://localhost:8000
PUBLIC_WS_URL=ws://localhost:8000/ws

# Feature toggles
PUBLIC_FEATURE_ANALYTICS=true
PUBLIC_FEATURE_NOTIFICATIONS=true
PUBLIC_FEATURE_REALTIME=true
```

See `.env.example` for all available options.

## Building for Production

### Standard Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Docker Build

```bash
# Development
docker build -f Dockerfile.dev -t wakedock-dashboard:dev .

# Production
docker build -f Dockerfile.prod -t wakedock-dashboard:prod .
```

## Project Structure

```
src/
├── lib/
│   ├── api.ts                 # API client
│   ├── websocket.ts           # WebSocket client
│   ├── components/            # Reusable Svelte components
│   ├── stores/                # Svelte stores for state management
│   ├── services/              # Business logic services
│   ├── utils/                 # Utility functions
│   ├── config/                # Configuration files
│   ├── middleware/            # Request/response middleware
│   └── types/                 # TypeScript type definitions
├── routes/                    # SvelteKit pages and layouts
├── app.html                   # HTML template
├── app.css                    # Global styles
└── hooks.server.ts            # Server-side hooks
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
- `npm run check` - Run Svelte type checking
- `npm run test` - Run tests (when implemented)

## API Integration

The dashboard communicates with the WakeDock API server for:

- **Authentication**: Login, logout, user management
- **Services**: CRUD operations on Docker services
- **System**: Health checks and system information
- **Real-time Updates**: WebSocket connections for live data

### API Client Usage

```typescript
import { api } from '$lib/api';

// Get all services
const services = await api.getServices();

// Start a service
await api.startService('service-id');

// User authentication
await api.auth.login({ username, password });
```

## State Management

The dashboard uses Svelte stores for state management:

```typescript
import { services, auth, notifications } from '$lib/stores';

// Subscribe to services
$: console.log('Services:', $services);

// Trigger actions
services.start('service-id');
auth.login(username, password);
notifications.success('Success!', 'Operation completed');
```

## WebSocket Integration

Real-time updates are handled via WebSocket:

```typescript
import { wsClient, subscribeToServices } from '$lib/websocket';

// Subscribe to service updates
subscribeToServices();

// Listen for updates
wsClient.serviceUpdates.subscribe(updates => {
  console.log('Service updates:', updates);
});
```

## Styling

The dashboard uses Tailwind CSS for styling:

- **Responsive design**: Mobile-first approach
- **Dark mode**: Automatic and manual theme switching
- **Component library**: Reusable UI components
- **Custom design system**: Consistent colors and spacing

## Security

- **Authentication**: JWT-based authentication
- **HTTPS**: Force HTTPS in production
- **CSP**: Content Security Policy headers
- **Input validation**: Client and server-side validation
- **CORS**: Proper CORS configuration

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Add tests if applicable
5. Commit: `git commit -m "Add new feature"`
6. Push: `git push origin feature/new-feature`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

## Roadmap

- [ ] Progressive Web App (PWA) support
- [ ] Offline functionality
- [ ] Advanced analytics and reporting
- [ ] Plugin system for extensions
- [ ] Multi-language support
- [ ] Advanced security features
- [ ] Integration with monitoring tools
