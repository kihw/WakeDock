# 🎨 FRONTEND MODERNE - WakeDock

**Priorité: 🔴 HAUTE**  
**Timeline: 2-3 semaines**  
**Équipe: Frontend Lead + UI/UX Designer + Senior Frontend Dev**

## 📋 Vue d'Ensemble

Ce document détaille la modernisation complète du frontend SvelteKit de WakeDock. L'audit révèle des composants géants (1000+ lignes), du code dupliqué, et des patterns obsolètes nécessitant une refactorisation urgente pour améliorer la maintenabilité et l'expérience utilisateur.

---

## 🎯 OBJECTIFS CLÉS

### 🧩 Modularisation des Composants
- Split des composants géants (1000+ lignes)  
- Design System consistant avec Tailwind CSS
- Composants réutilisables et atomiques
- Props typing strict avec TypeScript

### ⚡ Performance et UX
- Lazy loading intelligent des composants
- State management optimisé avec Svelte stores
- Animations fluides et micro-interactions
- PWA capabilities avec offline support

### 🔧 Developer Experience
- Hot module replacement optimisé
- TypeScript strict mode
- ESLint + Prettier configuration
- Component documentation automatique

---

## 🚨 COMPOSANTS GÉANTS À REFACTORER

### 1. `dashboard/src/routes/register/+page.svelte` - **1,343 lignes** 🔥

**Problème:** Formulaire monolithique avec logique mélangée

**Solution - Composants atomiques:**

```
src/lib/components/auth/
├── RegisterForm/
│   ├── RegisterForm.svelte           # Container principal
│   ├── PersonalInfoStep.svelte       # Étape info personnelles
│   ├── AccountCredentialsStep.svelte # Étape credentials  
│   ├── SecuritySetupStep.svelte      # Étape 2FA/sécurité
│   ├── CompanyInfoStep.svelte        # Étape info entreprise
│   └── ConfirmationStep.svelte       # Étape confirmation
├── FormFields/
│   ├── TextInput.svelte
│   ├── PasswordInput.svelte
│   ├── EmailInput.svelte
│   ├── SelectField.svelte
│   └── CheckboxField.svelte
└── Validation/
    ├── FieldValidator.svelte
    ├── FormValidator.svelte
    └── PasswordStrength.svelte
```

**Nouveau RegisterForm.svelte (< 150 lignes):**

```svelte
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { slide } from 'svelte/transition';
  import { registerStore } from '$lib/stores/register';
  import PersonalInfoStep from './PersonalInfoStep.svelte';
  import AccountCredentialsStep from './AccountCredentialsStep.svelte';
  import SecuritySetupStep from './SecuritySetupStep.svelte';
  import CompanyInfoStep from './CompanyInfoStep.svelte';
  import ConfirmationStep from './ConfirmationStep.svelte';

  const dispatch = createEventDispatcher<{
    complete: { user: User };
    cancel: void;
  }>();

  const steps = [
    { id: 'personal', title: 'Informations personnelles', component: PersonalInfoStep },
    { id: 'credentials', title: 'Identifiants', component: AccountCredentialsStep },
    { id: 'security', title: 'Sécurité', component: SecuritySetupStep },
    { id: 'company', title: 'Entreprise', component: CompanyInfoStep },
    { id: 'confirmation', title: 'Confirmation', component: ConfirmationStep }
  ];

  $: currentStep = $registerStore.currentStep;
  $: isValid = $registerStore.isCurrentStepValid;
  $: isLoading = $registerStore.isLoading;
</script>

<!-- Progress Indicator -->
<div class="progress-bar mb-8">
  {#each steps as step, index}
    <div 
      class="step" 
      class:active={index === currentStep}
      class:completed={index < currentStep}
    >
      <span class="step-number">{index + 1}</span>
      <span class="step-title">{step.title}</span>
    </div>
  {/each}
</div>

<!-- Step Content -->
<div class="step-content">
  {#each steps as step, index}
    {#if index === currentStep}
      <div in:slide={{ duration: 300 }} out:slide={{ duration: 200 }}>
        <svelte:component 
          this={step.component}
          on:next={registerStore.nextStep}
          on:previous={registerStore.previousStep}
          on:complete={() => dispatch('complete', { user: $registerStore.userData })}
        />
      </div>
    {/if}
  {/each}
</div>

<!-- Navigation -->
<div class="step-navigation">
  <button 
    type="button"
    disabled={currentStep === 0}
    on:click={registerStore.previousStep}
    class="btn btn-secondary"
  >
    Précédent
  </button>
  
  <button 
    type="button"
    disabled={!isValid || isLoading}
    on:click={registerStore.nextStep}
    class="btn btn-primary"
  >
    {#if isLoading}
      <LoadingSpinner size="sm" />
    {/if}
    {currentStep === steps.length - 1 ? 'Créer le compte' : 'Suivant'}
  </button>
</div>
```

---

### 2. `dashboard/src/lib/components/Header.svelte` - **1,163 lignes** 🔥

**Problème:** Header monolithique avec navigation, user menu, search

**Solution - Composants spécialisés:**

```
src/lib/components/layout/Header/
├── Header.svelte                 # Container principal (< 100 lignes)
├── Navigation/
│   ├── MainNavigation.svelte     # Navigation principale
│   ├── MobileNavigation.svelte   # Navigation mobile  
│   ├── NavItem.svelte           # Item de navigation
│   └── NavDropdown.svelte       # Dropdown navigation
├── Search/
│   ├── GlobalSearch.svelte       # Recherche globale
│   ├── SearchInput.svelte        # Input de recherche
│   ├── SearchResults.svelte      # Résultats recherche
│   └── SearchFilters.svelte      # Filtres recherche
├── UserMenu/
│   ├── UserMenu.svelte          # Menu utilisateur
│   ├── UserAvatar.svelte        # Avatar utilisateur
│   ├── UserDropdown.svelte      # Dropdown utilisateur
│   └── NotificationPanel.svelte  # Panneau notifications
└── Breadcrumbs/
    ├── Breadcrumbs.svelte
    └── BreadcrumbItem.svelte
```

**Nouveau Header.svelte modulaire:**

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import { authStore } from '$lib/stores/auth';
  import { notificationStore } from '$lib/stores/notifications';
  import MainNavigation from './Navigation/MainNavigation.svelte';
  import MobileNavigation from './Navigation/MobileNavigation.svelte';
  import GlobalSearch from './Search/GlobalSearch.svelte';
  import UserMenu from './UserMenu/UserMenu.svelte';
  import Breadcrumbs from './Breadcrumbs/Breadcrumbs.svelte';
  
  export let variant: 'default' | 'compact' | 'minimal' = 'default';
  
  $: user = $authStore.user;
  $: currentPath = $page.url.pathname;
  $: unreadNotifications = $notificationStore.unreadCount;
  
  let isMobileMenuOpen = false;
  let isSearchOpen = false;
</script>

<header class="header" class:compact={variant === 'compact'}>
  <!-- Logo -->
  <div class="header-brand">
    <a href="/" class="brand-link">
      <img src="/logo.svg" alt="WakeDock" class="brand-logo" />
      <span class="brand-text">WakeDock</span>
    </a>
  </div>

  <!-- Desktop Navigation -->
  {#if variant !== 'minimal'}
    <div class="header-nav hidden lg:flex">
      <MainNavigation {currentPath} />
    </div>
  {/if}

  <!-- Search -->
  {#if variant === 'default'}
    <div class="header-search hidden md:block">
      <GlobalSearch bind:isOpen={isSearchOpen} />
    </div>
  {/if}

  <!-- User Actions -->
  <div class="header-actions">
    {#if user}
      <UserMenu {user} {unreadNotifications} />
    {:else}
      <a href="/login" class="btn btn-primary">Se connecter</a>
    {/if}
    
    <!-- Mobile Menu Toggle -->
    <button 
      class="mobile-menu-toggle lg:hidden"
      on:click={() => isMobileMenuOpen = !isMobileMenuOpen}
      aria-label="Toggle menu"
    >
      <MenuIcon />
    </button>
  </div>

  <!-- Mobile Navigation -->
  {#if isMobileMenuOpen}
    <MobileNavigation 
      {currentPath} 
      on:close={() => isMobileMenuOpen = false} 
    />
  {/if}
</header>

<!-- Breadcrumbs -->
{#if variant === 'default' && $page.data.breadcrumbs}
  <Breadcrumbs items={$page.data.breadcrumbs} />
{/if}
```

---

### 3. `dashboard/src/routes/+page.svelte` - **1,056 lignes** 🔥

**Problème:** Dashboard monolithique avec widgets mélangés

**Solution - Architecture widget modulaire:**

```
src/lib/components/dashboard/
├── Dashboard.svelte              # Container principal
├── widgets/
│   ├── base/
│   │   ├── Widget.svelte         # Widget base component
│   │   ├── WidgetHeader.svelte   # Header widget standardisé
│   │   └── WidgetContent.svelte  # Content widget standardisé
│   ├── system/
│   │   ├── SystemOverviewWidget.svelte
│   │   ├── CPUUsageWidget.svelte
│   │   ├── MemoryUsageWidget.svelte
│   │   └── DiskUsageWidget.svelte
│   ├── services/
│   │   ├── ServicesOverviewWidget.svelte
│   │   ├── RunningServicesWidget.svelte
│   │   ├── RecentDeploymentsWidget.svelte
│   │   └── ServiceStatusWidget.svelte
│   ├── monitoring/
│   │   ├── AlertsWidget.svelte
│   │   ├── LogsWidget.svelte
│   │   ├── MetricsWidget.svelte
│   │   └── UptimeWidget.svelte
│   └── quick-actions/
│       ├── QuickActionsWidget.svelte
│       ├── DeployServiceWidget.svelte
│       └── SystemControlWidget.svelte
├── layouts/
│   ├── GridLayout.svelte         # Layout en grille
│   ├── StackedLayout.svelte      # Layout empilé
│   └── CustomLayout.svelte       # Layout personnalisable
└── charts/
    ├── LineChart.svelte
    ├── BarChart.svelte
    ├── PieChart.svelte
    └── GaugeChart.svelte
```

**Dashboard.svelte modernisé:**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { dashboardStore } from '$lib/stores/dashboard';
  import { userPreferencesStore } from '$lib/stores/preferences';
  import GridLayout from './layouts/GridLayout.svelte';
  import SystemOverviewWidget from './widgets/system/SystemOverviewWidget.svelte';
  import ServicesOverviewWidget from './widgets/services/ServicesOverviewWidget.svelte';
  import RunningServicesWidget from './widgets/services/RunningServicesWidget.svelte';
  import AlertsWidget from './widgets/monitoring/AlertsWidget.svelte';
  import QuickActionsWidget from './widgets/quick-actions/QuickActionsWidget.svelte';
  
  // Configuration des widgets selon les préférences utilisateur
  $: widgetConfig = $userPreferencesStore.dashboardLayout || defaultLayout;
  $: dashboardData = $dashboardStore.data;
  $: isLoading = $dashboardStore.isLoading;
  
  const defaultLayout = [
    { id: 'system-overview', component: SystemOverviewWidget, size: 'large', position: { x: 0, y: 0 } },
    { id: 'services-overview', component: ServicesOverviewWidget, size: 'medium', position: { x: 1, y: 0 } },
    { id: 'running-services', component: RunningServicesWidget, size: 'medium', position: { x: 0, y: 1 } },
    { id: 'alerts', component: AlertsWidget, size: 'small', position: { x: 1, y: 1 } },
    { id: 'quick-actions', component: QuickActionsWidget, size: 'small', position: { x: 2, y: 0 } }
  ];

  onMount(() => {
    dashboardStore.initialize();
    
    // Auto-refresh toutes les 30 secondes
    const interval = setInterval(() => {
      dashboardStore.refresh();
    }, 30000);
    
    return () => clearInterval(interval);
  });
</script>

<svelte:head>
  <title>Dashboard - WakeDock</title>
</svelte:head>

<div class="dashboard">
  <!-- Dashboard Header -->
  <div class="dashboard-header">
    <h1 class="dashboard-title">Dashboard</h1>
    <div class="dashboard-actions">
      <button 
        class="btn btn-secondary" 
        on:click={dashboardStore.refresh}
        disabled={isLoading}
      >
        {#if isLoading}
          <RefreshIcon class="animate-spin" />
        {:else}
          <RefreshIcon />
        {/if}
        Actualiser
      </button>
      <button class="btn btn-primary" on:click={openCustomizeModal}>
        <SettingsIcon />
        Personnaliser
      </button>
    </div>
  </div>

  <!-- Widgets Grid -->
  <div class="dashboard-content">
    {#if isLoading && !dashboardData}
      <div class="dashboard-skeleton">
        <!-- Loading skeleton -->
        {#each Array(6) as _}
          <div class="widget-skeleton"></div>
        {/each}
      </div>
    {:else}
      <GridLayout widgets={widgetConfig} {dashboardData} />
    {/if}
  </div>
</div>
```

---

## 🎨 DESIGN SYSTEM MODERNE

### Composants Atomiques

```
src/lib/components/ui/
├── atoms/
│   ├── Button/
│   │   ├── Button.svelte
│   │   ├── IconButton.svelte
│   │   └── ButtonGroup.svelte
│   ├── Input/
│   │   ├── TextInput.svelte
│   │   ├── NumberInput.svelte
│   │   ├── SearchInput.svelte
│   │   └── PasswordInput.svelte
│   ├── Typography/
│   │   ├── Heading.svelte
│   │   ├── Text.svelte
│   │   └── Code.svelte
│   └── Icons/
│       ├── Icon.svelte
│       └── index.ts
├── molecules/
│   ├── Card/
│   │   ├── Card.svelte
│   │   ├── CardHeader.svelte
│   │   └── CardContent.svelte
│   ├── Modal/
│   │   ├── Modal.svelte
│   │   ├── ModalHeader.svelte
│   │   └── ModalContent.svelte
│   ├── Toast/
│   │   ├── Toast.svelte
│   │   └── ToastContainer.svelte
│   └── Dropdown/
│       ├── Dropdown.svelte
│       └── DropdownItem.svelte
└── organisms/
    ├── DataTable/
    ├── FormBuilder/
    └── ChartContainer/
```

### Système de Tokens Design

```typescript
// src/lib/design-tokens/tokens.ts
export const designTokens = {
  colors: {
    // Semantic colors
    primary: {
      50: '#eff6ff',
      100: '#dbeafe', 
      500: '#3b82f6',
      600: '#2563eb',
      900: '#1e3a8a'
    },
    semantic: {
      success: '#10b981',
      warning: '#f59e0b', 
      error: '#ef4444',
      info: '#3b82f6'
    },
    // Component colors
    background: {
      primary: '#ffffff',
      secondary: '#f8fafc',
      tertiary: '#f1f5f9'
    }
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'sans-serif'],
      mono: ['Fira Code', 'monospace']
    },
    fontSize: {
      xs: ['0.75rem', { lineHeight: '1rem' }],
      sm: ['0.875rem', { lineHeight: '1.25rem' }],
      base: ['1rem', { lineHeight: '1.5rem' }],
      lg: ['1.125rem', { lineHeight: '1.75rem' }],
      xl: ['1.25rem', { lineHeight: '1.75rem' }]
    }
  },
  spacing: {
    px: '1px',
    0: '0',
    1: '0.25rem',
    2: '0.5rem',
    4: '1rem',
    8: '2rem'
  },
  borderRadius: {
    sm: '0.125rem',
    md: '0.375rem', 
    lg: '0.5rem',
    full: '9999px'
  }
} as const;
```

---

## ⚡ STATE MANAGEMENT OPTIMISÉ

### Store Architecture Modulaire

```typescript
// src/lib/stores/index.ts - Store Registry
export interface StoreRegistry {
  auth: AuthStore;
  dashboard: DashboardStore;
  services: ServicesStore;
  notifications: NotificationStore;
  preferences: UserPreferencesStore;
  realtime: RealtimeStore;
}

// Store composition pattern
export const stores = createStoreRegistry();

// src/lib/stores/dashboard.ts
interface DashboardState {
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  selectedTimeRange: TimeRange;
}

export const dashboardStore = createStore<DashboardState>({
  initialState: {
    data: null,
    isLoading: false,
    error: null,
    lastUpdated: null,
    selectedTimeRange: '1h'
  },
  
  actions: {
    async initialize() {
      this.setState({ isLoading: true, error: null });
      
      try {
        const data = await api.getSystemOverview();
        this.setState({ 
          data, 
          isLoading: false, 
          lastUpdated: new Date() 
        });
      } catch (error) {
        this.setState({ 
          isLoading: false, 
          error: error.message 
        });
      }
    },
    
    async refresh() {
      // Refresh sans spinner si données déjà présentes
      const currentData = this.getState().data;
      if (!currentData) {
        return this.initialize();
      }
      
      try {
        const data = await api.getSystemOverview();
        this.setState({ data, lastUpdated: new Date() });
      } catch (error) {
        // Garder les anciennes données en cas d'erreur
        console.error('Dashboard refresh failed:', error);
      }
    },
    
    setTimeRange(range: TimeRange) {
      this.setState({ selectedTimeRange: range });
      this.refresh();
    }
  },
  
  computed: {
    servicesStats: (state) => ({
      total: state.data?.services.total || 0,
      running: state.data?.services.running || 0,
      stopped: state.data?.services.stopped || 0,
      healthyPercentage: state.data ? 
        (state.data.services.running / state.data.services.total) * 100 : 0
    }),
    
    systemHealth: (state) => {
      if (!state.data) return 'unknown';
      
      const { cpu_usage, memory_usage, disk_usage } = state.data.system;
      const avgUsage = (cpu_usage + memory_usage + disk_usage) / 3;
      
      if (avgUsage < 60) return 'healthy';
      if (avgUsage < 80) return 'warning';
      return 'critical';
    }
  }
});
```

### WebSocket Store Réactif

```typescript
// src/lib/stores/realtime.ts
export const realtimeStore = createRealtimeStore({
  channels: {
    'system:metrics': {
      handler: (data) => dashboardStore.updateMetrics(data),
      autoReconnect: true,
      bufferSize: 100
    },
    'services:events': {
      handler: (data) => servicesStore.handleEvent(data),
      autoReconnect: true
    },
    'notifications': {
      handler: (data) => notificationStore.addNotification(data),
      autoReconnect: true
    }
  },
  
  onConnect: () => {
    console.log('WebSocket connected');
    notificationStore.showSuccess('Connexion temps réel établie');
  },
  
  onDisconnect: () => {
    console.log('WebSocket disconnected');
    notificationStore.showWarning('Connexion temps réel interrompue');
  },
  
  onReconnect: () => {
    console.log('WebSocket reconnected');
    notificationStore.showSuccess('Connexion temps réel rétablie');
    
    // Refresh data after reconnection
    dashboardStore.refresh();
    servicesStore.refresh();
  }
});
```

---

## 🎭 ANIMATIONS ET MICRO-INTERACTIONS

### Animation System

```typescript
// src/lib/animations/transitions.ts
export const transitions = {
  // Page transitions
  page: {
    in: { duration: 300, easing: 'cubic-bezier(0.4, 0, 0.2, 1)' },
    out: { duration: 200, easing: 'cubic-bezier(0.4, 0, 0.2, 1)' }
  },
  
  // Modal transitions
  modal: {
    backdrop: { duration: 200 },
    content: { duration: 300, easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)' }
  },
  
  // List items
  list: {
    stagger: 50, // Delay entre items
    item: { duration: 200 }
  },
  
  // Loading states
  skeleton: {
    pulse: { duration: 1500, loop: true }
  }
};

// Animations prédéfinies
export const animations = {
  fadeIn: (node: Element, { duration = 300, delay = 0 } = {}) => ({
    duration,
    delay,
    css: (t: number) => `
      opacity: ${t};
      transform: translateY(${(1 - t) * 10}px);
    `
  }),
  
  slideIn: (node: Element, { duration = 300, direction = 'left' } = {}) => ({
    duration,
    css: (t: number) => {
      const x = direction === 'left' ? -100 : 100;
      return `
        transform: translateX(${(1 - t) * x}px);
        opacity: ${t};
      `;
    }
  }),
  
  scaleIn: (node: Element, { duration = 200, start = 0.8 } = {}) => ({
    duration,
    css: (t: number) => `
      transform: scale(${start + (1 - start) * t});
      opacity: ${t};
    `
  })
};
```

### Micro-interactions Composants

```svelte
<!-- src/lib/components/ui/atoms/Button/Button.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { scale } from 'svelte/transition';
  
  export let variant: 'primary' | 'secondary' | 'danger' = 'primary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let loading = false;
  export let disabled = false;
  export let ripple = true;
  
  const dispatch = createEventDispatcher<{ click: MouseEvent }>();
  
  let buttonElement: HTMLButtonElement;
  let rippleEffect = false;
  
  function handleClick(event: MouseEvent) {
    if (loading || disabled) return;
    
    if (ripple) {
      rippleEffect = true;
      setTimeout(() => rippleEffect = false, 300);
    }
    
    dispatch('click', event);
  }
</script>

<button
  bind:this={buttonElement}
  class="btn btn-{variant} btn-{size}"
  class:loading
  class:ripple-effect={rippleEffect}
  {disabled}
  on:click={handleClick}
>
  {#if loading}
    <div class="loading-spinner" in:scale={{ duration: 200 }}>
      <svg class="animate-spin" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
        <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  {/if}
  
  <span class="btn-content" class:loading>
    <slot />
  </span>
  
  {#if ripple && rippleEffect}
    <div class="ripple" in:scale={{ duration: 300 }} />
  {/if}
</button>

<style>
  .btn {
    @apply relative overflow-hidden transition-all duration-200;
    @apply focus:outline-none focus:ring-2 focus:ring-offset-2;
    @apply active:scale-95;
  }
  
  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700;
    @apply focus:ring-blue-500;
  }
  
  .ripple {
    @apply absolute inset-0 bg-white bg-opacity-30 rounded-full;
    transform: scale(0);
    animation: ripple 300ms ease-out;
  }
  
  @keyframes ripple {
    to {
      transform: scale(2);
      opacity: 0;
    }
  }
  
  .loading-spinner {
    @apply absolute inset-0 flex items-center justify-center;
  }
  
  .btn-content.loading {
    @apply opacity-0;
  }
</style>
```

---

## 📱 PWA ET OFFLINE SUPPORT

### Service Worker Configuration

```typescript
// src/service-worker.ts
import { build, files, version } from '$service-worker';

const CACHE_NAME = `wakedock-cache-${version}`;
const STATIC_CACHE = `wakedock-static-${version}`;
const RUNTIME_CACHE = `wakedock-runtime-${version}`;

// Files to cache
const STATIC_ASSETS = [...build, ...files];

// API endpoints to cache
const CACHEABLE_ROUTES = [
  '/api/v1/system/overview',
  '/api/v1/services',
  '/api/v1/auth/me'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys
          .filter(key => key !== STATIC_CACHE && key !== RUNTIME_CACHE)
          .map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Network-first strategy for API calls
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache successful responses
          if (response.ok && CACHEABLE_ROUTES.some(route => 
            url.pathname.startsWith(route))) {
            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE)
              .then(cache => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache
          return caches.match(request);
        })
    );
    return;
  }
  
  // Cache-first for static assets
  if (STATIC_ASSETS.includes(url.pathname)) {
    event.respondWith(
      caches.match(request)
        .then(response => response || fetch(request))
    );
  }
});
```

### Offline Indicator

```svelte
<!-- src/lib/components/ui/OfflineIndicator.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { slide } from 'svelte/transition';
  import { networkStore } from '$lib/stores/network';
  
  $: isOnline = $networkStore.isOnline;
  $: lastSync = $networkStore.lastSync;
  
  let showOfflineBanner = false;
  
  $: {
    if (!isOnline) {
      showOfflineBanner = true;
    } else {
      // Cache le banner après 3 secondes de reconnexion
      setTimeout(() => showOfflineBanner = false, 3000);
    }
  }
</script>

{#if showOfflineBanner}
  <div 
    class="offline-banner"
    class:online={isOnline}
    transition:slide={{ duration: 300 }}
  >
    <div class="offline-content">
      {#if isOnline}
        <CheckIcon class="text-green-500" />
        <span>Connexion rétablie</span>
        {#if lastSync}
          <span class="last-sync">
            Dernière sync: {new Date(lastSync).toLocaleTimeString()}
          </span>
        {/if}
      {:else}
        <OfflineIcon class="text-orange-500" />
        <span>Mode hors ligne</span>
        <span class="offline-message">
          Certaines fonctionnalités sont limitées
        </span>
      {/if}
    </div>
  </div>
{/if}

<style>
  .offline-banner {
    @apply fixed top-0 left-0 right-0 z-50;
    @apply bg-orange-100 border-b border-orange-200;
    @apply text-orange-800 text-sm;
  }
  
  .offline-banner.online {
    @apply bg-green-100 border-green-200 text-green-800;
  }
  
  .offline-content {
    @apply flex items-center justify-center gap-2 p-2;
  }
  
  .last-sync, .offline-message {
    @apply text-xs opacity-75;
  }
</style>
```

---

## 🧪 TESTING MODERNE

### Component Testing

```typescript
// src/lib/components/ui/atoms/Button/Button.test.ts
import { render, fireEvent, screen } from '@testing-library/svelte';
import { vi } from 'vitest';
import Button from './Button.svelte';

describe('Button', () => {
  it('renders with correct variant class', () => {
    render(Button, { variant: 'primary' });
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn-primary');
  });

  it('dispatches click event when clicked', async () => {
    const { component } = render(Button);
    const clickHandler = vi.fn();
    
    component.$on('click', clickHandler);
    
    const button = screen.getByRole('button');
    await fireEvent.click(button);
    
    expect(clickHandler).toHaveBeenCalledTimes(1);
  });

  it('shows loading state correctly', () => {
    render(Button, { loading: true });
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
  });

  it('is disabled when loading', () => {
    render(Button, { loading: true });
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });
});
```

### E2E Testing avec Playwright

```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/');
  });

  test('displays system overview correctly', async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="system-overview-widget"]');
    
    // Check widget presence
    await expect(page.locator('[data-testid="cpu-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="memory-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="disk-usage"]')).toBeVisible();
  });

  test('refreshes data when refresh button clicked', async ({ page }) => {
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    await refreshButton.click();
    
    // Check loading state
    await expect(refreshButton).toHaveClass(/animate-spin/);
    
    // Wait for refresh to complete
    await expect(refreshButton).not.toHaveClass(/animate-spin/);
  });

  test('opens customize modal', async ({ page }) => {
    await page.click('[data-testid="customize-button"]');
    await expect(page.locator('[data-testid="customize-modal"]')).toBeVisible();
  });
});
```

---

## 🚀 PLAN D'EXÉCUTION

### Semaine 1: Refactoring Composants Géants
- [ ] Split `RegisterForm` en composants atomiques
- [ ] Refactoring `Header` modulaire  
- [ ] Split `Dashboard` en widgets
- [ ] Setup Design System base

### Semaine 2: State Management & Performance
- [ ] Implémentation stores modulaires
- [ ] WebSocket store réactif
- [ ] Lazy loading composants
- [ ] PWA configuration

### Semaine 3: Polish & Testing
- [ ] Animations et micro-interactions
- [ ] Tests composants complets
- [ ] E2E tests critiques
- [ ] Documentation composants

---

## 📈 STATUS DU REFACTORING (Juillet 2025)

### ✅ Terminé
- **Sidebar.svelte** (782 → 14 lignes): Refactorisé en 6 composants modulaires
  - `SidebarHeader.svelte` (107 lignes)
  - `NavigationSection.svelte` (57 lignes)
  - `NavigationItem.svelte` (198 lignes)
  - `QuickActions.svelte` (53 lignes)
  - `SystemStatus.svelte` (204 lignes)
  - `SidebarFooter.svelte` (38 lignes)
  - `SidebarModular.svelte` (373 lignes) - Nouveau composant principal

- **Security Dashboard** (830 → 70 lignes): Refactorisé en 4 composants modulaires
  - `SecurityMetrics.svelte`, `SecurityEventsTable.svelte`, `AuditLogs.svelte`, `SecurityTabs.svelte`

- **Register Page** (1,343 → 209 lignes): Déjà refactorisé

### ✅ Terminé (suite)
- **login/+page.svelte** (795 → 264 lignes): Refactorisé en 6 composants modulaires
  - `LoginForm.svelte` (132 lignes) - Composant principal
  - `LoginHeader.svelte` (75 lignes) - En-tête avec branding
  - `LoginFields.svelte` (208 lignes) - Champs de saisie
  - `TwoFactorSection.svelte` (226 lignes) - Section 2FA
  - `LoginActions.svelte` (211 lignes) - Actions et boutons
  - `LoginFooter.svelte` (132 lignes) - Pied de page

### 🔄 En cours / Suivant
- **settings/+page.svelte** (598 lignes) - Prochaine priorité
- **dashboard/+page.svelte** (287 lignes) - Ensuite
- **Header.svelte** (189 lignes) - Dernière priorité (déjà raisonnable)

### 📊 Métriques
- **Composants refactorisés**: 4/8 (50%)
- **Lignes économisées**: ~1,931 lignes
- **Composants créés**: 19 nouveaux composants modulaires
- **Prochaine cible**: settings/+page.svelte (598 lignes)