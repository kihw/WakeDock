# 🐳 WakeDock - Enhanced UI

![WakeDock Banner](https://img.shields.io/badge/WakeDock-Docker%20Management-blue?style=for-the-badge&logo=docker)

**WakeDock** is a modern, intelligent Docker orchestration and service management platform with a beautiful, responsive web interface. This enhanced version features a complete UI overhaul with glassmorphism design, smooth animations, and improved user experience.

## ✨ New UI Features

### 🎨 Modern Design System
- **Glassmorphism Effects**: Translucent backgrounds with blur effects
- **Custom CSS Variables**: Consistent theming throughout the app
- **Gradient Accents**: Beautiful gradients for primary elements
- **Enhanced Typography**: Inter font family with proper weight variations
- **Micro-animations**: Smooth transitions and hover effects

### 🏗️ Enhanced Components

#### 📊 **StatsCards**
- Real-time metrics with trend indicators
- Usage bars with color-coded status
- Service breakdown with visual dots
- System health indicators
- Resource monitoring with progress bars

#### 🔧 **ServiceCard**
- Modern card layout with glassmorphism
- Resource usage meters
- Interactive dropdown menus
- Status indicators with animations
- Port tags and service metadata
- Quick action buttons

#### 🧭 **Navigation**
- **Enhanced Sidebar**: Navigation sections, system status, quick actions
- **Smart Header**: Search bar, notifications dropdown, user menu
- **Breadcrumbs**: Clear navigation path
- **Theme Toggle**: Dark/light mode support

#### 📱 **Responsive Design**
- Mobile-first approach
- Adaptive layouts for all screen sizes
- Touch-friendly interactions
- Collapsible sidebar on mobile

### 🎭 **Theme System**
- **Light Mode**: Clean, modern aesthetic
- **Dark Mode**: Easy on the eyes with proper contrast
- **Auto Mode**: Follows system preference
- **Custom Properties**: Easy theme customization

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