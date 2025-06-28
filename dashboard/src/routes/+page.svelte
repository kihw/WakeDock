<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import ServiceCard from '$lib/components/ServiceCard.svelte';
  import StatsCards from '$lib/components/StatsCards.svelte';
  import {
    Container,
    Play,
    Square,
    Plus,
    Zap,
    Activity,
    TrendingUp,
    RefreshCw,
    Search,
    Filter,
  } from 'lucide-svelte';

  interface Service {
    id: string;
    name: string;
    subdomain: string;
    status: string;
    docker_image?: string;
    docker_compose?: string;
    ports: string[];
    last_accessed?: string;
    resource_usage?: {
      cpu_percent: number;
      memory_usage: number;
      memory_percent: number;
    };
  }

  let services: Service[] = [];
  let loading = true;
  let error = '';
  let searchTerm = '';
  let statusFilter = 'all';
  let refreshing = false;

  // Initialize with safe defaults to prevent SSR errors
  let quickStats = {
    total: 0,
    running: 0,
    stopped: 0,
    error: 0,
  };

  const stats = writable({
    services: {
      total: 0,
      running: 0,
      stopped: 0,
      error: 0,
    },
    system: {
      cpu_usage: 0,
      memory_usage: 0,
      disk_usage: 0,
      uptime: 0,
    },
    docker: {
      version: 'unknown',
      api_version: 'unknown',
      status: 'unknown',
    },
    caddy: {
      version: 'unknown',
      status: 'unknown',
      active_routes: 0,
    },
  });

  // Filtered services based on search and status
  $: filteredServices = services.filter((service) => {
    const matchesSearch =
      service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      service.subdomain.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || service.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Quick stats for the filtered services (update the initialized defaults)
  $: if (filteredServices) {
    quickStats = {
      total: filteredServices.length || 0,
      running: filteredServices.filter((s) => s.status === 'running').length || 0,
      stopped: filteredServices.filter((s) => s.status === 'stopped').length || 0,
      error: filteredServices.filter((s) => s.status === 'error').length || 0,
    };
  }

  // Status filter options (reactive to ensure SSR compatibility)
  $: statusOptions = [
    { value: 'all', label: 'All Services', count: quickStats.total },
    { value: 'running', label: 'Running', count: quickStats.running },
    { value: 'stopped', label: 'Stopped', count: quickStats.stopped },
    { value: 'error', label: 'Error', count: quickStats.error },
  ];

  onMount(async () => {
    await loadServices();
    await loadStats();

    // Refresh data every 30 seconds
    const interval = setInterval(async () => {
      await refreshData();
    }, 30000);

    return () => clearInterval(interval);
  });

  async function loadServices() {
    try {
      loading = true;
      error = '';

      // Try to load from API, fallback to mock data
      try {
        // Import the API - handle SSR case
        if (typeof window !== 'undefined') {
          const { api } = await import('$lib/api');
          const apiServices = await api.services.getAll();
          services = apiServices.map((service) => ({
            id: service.id,
            name: service.name,
            subdomain: service.name.toLowerCase(),
            status: service.status,
            docker_image: service.image,
            ports: service.ports.map((p) => `${p.host}:${p.container}`),
            last_accessed: service.updated_at,
            resource_usage: {
              cpu_percent: Math.random() * 50,
              memory_usage: Math.random() * 512 * 1024 * 1024,
              memory_percent: Math.random() * 30,
            },
          }));
        } else {
          // SSR fallback
          services = [];
        }
      } catch (apiError) {
        console.warn('API not available, using mock data:', apiError);
        // Fallback to mock data
        const mockServices: Service[] = [
          {
            id: '1',
            name: 'nginx-proxy',
            subdomain: 'proxy',
            status: 'running',
            docker_image: 'nginx:alpine',
            ports: ['80:80', '443:443'],
            last_accessed: new Date(Date.now() - 300000).toISOString(),
            resource_usage: {
              cpu_percent: 12.5,
              memory_usage: 64 * 1024 * 1024,
              memory_percent: 8.2,
            },
          },
          {
            id: '2',
            name: 'postgres-db',
            subdomain: 'db',
            status: 'running',
            docker_image: 'postgres:15',
            ports: ['5432:5432'],
            last_accessed: new Date(Date.now() - 600000).toISOString(),
            resource_usage: {
              cpu_percent: 5.8,
              memory_usage: 128 * 1024 * 1024,
              memory_percent: 16.4,
            },
          },
          {
            id: '3',
            name: 'redis-cache',
            subdomain: 'cache',
            status: 'stopped',
            docker_image: 'redis:7-alpine',
            ports: ['6379:6379'],
            last_accessed: new Date(Date.now() - 3600000).toISOString(),
          },
          {
            id: '4',
            name: 'web-app',
            subdomain: 'app',
            status: 'starting',
            docker_image: 'node:18-alpine',
            ports: ['3000:3000'],
            last_accessed: new Date(Date.now() - 1800000).toISOString(),
          },
        ];

        services = mockServices;
      }
      error = '';
    } catch (e) {
      error = 'Network error loading services';
      console.error('Failed to load services:', e);
    } finally {
      loading = false;
    }
  }

  async function loadStats() {
    try {
      // Mock data - replace with actual API call
      const mockStats = {
        services: {
          total: services.length,
          running: services.filter((s) => s.status === 'running').length,
          stopped: services.filter((s) => s.status === 'stopped').length,
          error: services.filter((s) => s.status === 'error').length,
        },
        system: {
          cpu_usage: 24.5,
          memory_usage: 68.2,
          disk_usage: 45.8,
          uptime: 1234567,
        },
        docker: {
          version: '24.0.7',
          api_version: '1.43',
          status: 'healthy',
        },
        caddy: {
          version: '2.7.6',
          status: 'healthy',
          active_routes: 12,
        },
      };

      stats.set(mockStats);
    } catch (e) {
      console.error('Failed to load stats:', e);
    }
  }

  async function refreshData() {
    refreshing = true;
    try {
      await Promise.all([loadServices(), loadStats()]);
    } finally {
      refreshing = false;
    }
  }

  async function wakeService(serviceId: string) {
    try {
      // Find and update service status optimistically
      services = services.map((s) => (s.id === serviceId ? { ...s, status: 'starting' } : s));

      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Update to running
      services = services.map((s) => (s.id === serviceId ? { ...s, status: 'running' } : s));

      await loadStats(); // Refresh stats
    } catch (e) {
      console.error('Failed to wake service:', e);
      // Revert optimistic update
      await loadServices();
    }
  }

  async function sleepService(serviceId: string) {
    try {
      // Find and update service status optimistically
      services = services.map((s) => (s.id === serviceId ? { ...s, status: 'stopping' } : s));

      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Update to stopped
      services = services.map((s) => (s.id === serviceId ? { ...s, status: 'stopped' } : s));

      await loadStats(); // Refresh stats
    } catch (e) {
      console.error('Failed to sleep service:', e);
      // Revert optimistic update
      await loadServices();
    }
  }
</script>

<svelte:head>
  <title>Dashboard - WakeDock</title>
</svelte:head>

<div class="dashboard">
  <!-- Hero Section -->
  <div class="hero-section">
    <div class="hero-content">
      <div class="hero-text">
        <h1 class="hero-title">
          <Container size={40} />
          WakeDock Dashboard
        </h1>
        <p class="hero-description">
          Intelligent Docker orchestration and service management platform
        </p>
        <div class="hero-stats">
          <div class="hero-stat">
            <div class="hero-stat-value">{quickStats.total}</div>
            <div class="hero-stat-label">Total Services</div>
          </div>
          <div class="hero-stat">
            <div class="hero-stat-value text-green-600">{quickStats.running}</div>
            <div class="hero-stat-label">Running</div>
          </div>
          <div class="hero-stat">
            <div class="hero-stat-value text-gray-600">{quickStats.stopped}</div>
            <div class="hero-stat-label">Stopped</div>
          </div>
        </div>
      </div>

      <div class="hero-actions">
        <a href="/services/new" class="btn btn-primary btn-lg">
          <Plus size={20} />
          Deploy Service
        </a>
        <button class="btn btn-secondary btn-lg" on:click={refreshData} disabled={refreshing}>
          <RefreshCw size={20} class={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>
    </div>

    <!-- Background Elements -->
    <div class="hero-bg">
      <div class="hero-circle circle-1"></div>
      <div class="hero-circle circle-2"></div>
      <div class="hero-circle circle-3"></div>
    </div>
  </div>

  <!-- Stats Cards -->
  <StatsCards {stats} />

  <!-- Services Section -->
  <div class="services-section">
    <div class="section-header">
      <div class="section-title">
        <h2>Services</h2>
        <p class="section-description">
          {filteredServices.length} service{filteredServices.length !== 1 ? 's' : ''}
          {searchTerm || statusFilter !== 'all' ? 'matching filters' : 'configured'}
        </p>
      </div>

      <!-- Controls -->
      <div class="section-controls">
        <!-- Search -->
        <div class="search-container">
          <div class="search-input-wrapper">
            <Search size={16} class="search-icon" />
            <input
              type="text"
              placeholder="Search services..."
              class="search-input"
              bind:value={searchTerm}
            />
          </div>
        </div>

        <!-- Filter -->
        <div class="filter-container">
          <Filter size={16} class="filter-icon" />
          <select class="filter-select" bind:value={statusFilter}>
            {#each statusOptions as option}
              <option value={option.value}>
                {option.label} ({option.count})
              </option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <!-- Services Content -->
    {#if loading}
      <div class="loading-state">
        <div class="loading-grid">
          {#each Array(4) as _}
            <div class="loading-card">
              <div class="loading-shimmer"></div>
            </div>
          {/each}
        </div>
        <p class="loading-text">Loading services...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <div class="error-icon">
          <Activity size={48} />
        </div>
        <h3 class="error-title">Failed to Load Services</h3>
        <p class="error-message">{error}</p>
        <button class="btn btn-primary" on:click={loadServices}>
          <RefreshCw size={16} />
          Try Again
        </button>
      </div>
    {:else if filteredServices.length === 0}
      <div class="empty-state">
        {#if searchTerm || statusFilter !== 'all'}
          <!-- No results for filters -->
          <div class="empty-icon">
            <Search size={48} />
          </div>
          <h3 class="empty-title">No services found</h3>
          <p class="empty-message">Try adjusting your search or filter criteria</p>
          <button
            class="btn btn-secondary"
            on:click={() => {
              searchTerm = '';
              statusFilter = 'all';
            }}
          >
            Clear Filters
          </button>
        {:else}
          <!-- No services at all -->
          <div class="empty-icon">
            <Container size={48} />
          </div>
          <h3 class="empty-title">No services configured</h3>
          <p class="empty-message">Get started by deploying your first service</p>
          <div class="empty-actions">
            <a href="/services/new" class="btn btn-primary">
              <Plus size={16} />
              Deploy Your First Service
            </a>
            <a href="/docs/quickstart" class="btn btn-secondary"> View Documentation </a>
          </div>
        {/if}
      </div>
    {:else}
      <div class="services-grid">
        {#each filteredServices as service (service.id)}
          <ServiceCard
            {service}
            on:wake={() => wakeService(service.id)}
            on:sleep={() => sleepService(service.id)}
          />
        {/each}
      </div>
    {/if}
  </div>

  <!-- Quick Actions -->
  <div class="quick-actions-section">
    <div class="quick-actions-header">
      <h3>Quick Actions</h3>
      <p>Common tasks and shortcuts</p>
    </div>

    <div class="quick-actions-grid">
      <a href="/services/new" class="quick-action-card">
        <div class="quick-action-icon">
          <Plus size={24} />
        </div>
        <div class="quick-action-content">
          <h4>Deploy Service</h4>
          <p>Add a new Docker service</p>
        </div>
      </a>

      <a href="/monitoring" class="quick-action-card">
        <div class="quick-action-icon">
          <Activity size={24} />
        </div>
        <div class="quick-action-content">
          <h4>System Monitor</h4>
          <p>View system metrics</p>
        </div>
      </a>

      <a href="/settings" class="quick-action-card">
        <div class="quick-action-icon">
          <Zap size={24} />
        </div>
        <div class="quick-action-content">
          <h4>Configuration</h4>
          <p>Manage system settings</p>
        </div>
      </a>

      <button class="quick-action-card" on:click={() => wakeAllServices()}>
        <div class="quick-action-icon">
          <Play size={24} />
        </div>
        <div class="quick-action-content">
          <h4>Start All</h4>
          <p>Wake all stopped services</p>
        </div>
      </button>
    </div>
  </div>
</div>

<style>
  .dashboard {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 var(--spacing-lg);
  }

  /* Hero Section */
  .hero-section {
    position: relative;
    padding: var(--spacing-3xl) 0;
    margin-bottom: var(--spacing-2xl);
    overflow: hidden;
    border-radius: var(--radius-xl);
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
  }

  .hero-content {
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-2xl);
  }

  .hero-text {
    flex: 1;
    max-width: 600px;
  }

  .hero-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: var(--spacing-md);
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .hero-description {
    font-size: 1.25rem;
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-xl);
    line-height: 1.6;
  }

  .hero-stats {
    display: flex;
    gap: var(--spacing-xl);
  }

  .hero-stat {
    text-align: center;
  }

  .hero-stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: var(--spacing-xs);
  }

  .hero-stat-label {
    font-size: 0.875rem;
    color: var(--color-text-muted);
    font-weight: 500;
  }

  .hero-actions {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    flex-shrink: 0;
  }

  /* Hero Background */
  .hero-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1;
    overflow: hidden;
  }

  .hero-circle {
    position: absolute;
    border-radius: 50%;
    background: var(--gradient-primary);
    opacity: 0.1;
    animation: float 6s ease-in-out infinite;
  }

  .circle-1 {
    width: 200px;
    height: 200px;
    top: -100px;
    right: -100px;
    animation-delay: 0s;
  }

  .circle-2 {
    width: 150px;
    height: 150px;
    bottom: -75px;
    left: -75px;
    animation-delay: 2s;
  }

  .circle-3 {
    width: 100px;
    height: 100px;
    top: 50%;
    right: 20%;
    animation-delay: 4s;
  }

  /* Section Header */
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-xl);
    gap: var(--spacing-lg);
  }

  .section-title h2 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: var(--spacing-xs);
    color: var(--color-text);
  }

  .section-description {
    color: var(--color-text-secondary);
    margin: 0;
  }

  .section-controls {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
    flex-shrink: 0;
  }

  /* Search and Filter */
  .search-container {
    position: relative;
  }

  .search-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-input {
    width: 300px;
    padding: var(--spacing-sm) var(--spacing-md);
    padding-left: 2.5rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-full);
    background: var(--color-surface-glass);
    color: var(--color-text);
    font-size: 0.875rem;
    transition: all var(--transition-normal);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    width: 350px;
  }

  .search-icon {
    position: absolute;
    left: var(--spacing-sm);
    color: var(--color-text-muted);
    pointer-events: none;
  }

  .filter-container {
    position: relative;
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .filter-icon {
    color: var(--color-text-muted);
  }

  .filter-select {
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    background: var(--color-surface-glass);
    color: var(--color-text);
    font-size: 0.875rem;
    cursor: pointer;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }

  /* Services Grid */
  .services-grid {
    display: grid;
    gap: var(--spacing-lg);
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    margin-bottom: var(--spacing-2xl);
  }

  /* Loading State */
  .loading-state {
    text-align: center;
    padding: var(--spacing-3xl) 0;
  }

  .loading-grid {
    display: grid;
    gap: var(--spacing-lg);
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    margin-bottom: var(--spacing-xl);
  }

  .loading-card {
    height: 300px;
    border-radius: var(--radius-xl);
    overflow: hidden;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
  }

  .loading-shimmer {
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      var(--color-surface) 25%,
      rgba(255, 255, 255, 0.4) 50%,
      var(--color-surface) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 2s infinite;
  }

  .loading-text {
    color: var(--color-text-secondary);
    font-size: 1.125rem;
  }

  /* Error State */
  .error-state {
    text-align: center;
    padding: var(--spacing-3xl) 0;
  }

  .error-icon {
    color: var(--color-error);
    margin-bottom: var(--spacing-lg);
  }

  .error-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: var(--spacing-sm);
  }

  .error-message {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-lg);
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: var(--spacing-3xl) 0;
  }

  .empty-icon {
    color: var(--color-text-muted);
    margin-bottom: var(--spacing-lg);
  }

  .empty-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: var(--spacing-sm);
  }

  .empty-message {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-lg);
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
  }

  .empty-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: center;
    flex-wrap: wrap;
  }

  /* Quick Actions */
  .quick-actions-section {
    margin-top: var(--spacing-3xl);
    padding: var(--spacing-2xl) 0;
    border-top: 1px solid var(--color-border-light);
  }

  .quick-actions-header {
    text-align: center;
    margin-bottom: var(--spacing-xl);
  }

  .quick-actions-header h3 {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: var(--spacing-xs);
  }

  .quick-actions-header p {
    color: var(--color-text-secondary);
    margin: 0;
  }

  .quick-actions-grid {
    display: grid;
    gap: var(--spacing-lg);
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    max-width: 800px;
    margin: 0 auto;
  }

  .quick-action-card {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    text-decoration: none;
    color: var(--color-text);
    transition: all var(--transition-normal);
    cursor: pointer;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
  }

  .quick-action-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--color-primary-light);
  }

  .quick-action-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius);
    background: var(--gradient-primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .quick-action-content h4 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    margin-bottom: var(--spacing-xs);
  }

  .quick-action-content p {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin: 0;
  }

  /* Responsive Design */
  @media (max-width: 1024px) {
    .services-grid {
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    }
  }

  @media (max-width: 768px) {
    .dashboard {
      padding: 0 var(--spacing-md);
    }

    .hero-content {
      flex-direction: column;
      text-align: center;
      gap: var(--spacing-xl);
    }

    .hero-title {
      font-size: 2rem;
    }

    .hero-stats {
      justify-content: center;
    }

    .hero-actions {
      flex-direction: row;
      justify-content: center;
    }

    .section-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .section-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .search-input {
      width: 100%;
    }

    .search-input:focus {
      width: 100%;
    }

    .services-grid {
      grid-template-columns: 1fr;
    }

    .quick-actions-grid {
      grid-template-columns: 1fr;
    }

    .quick-action-card {
      flex-direction: column;
      text-align: center;
    }
  }

  @media (max-width: 480px) {
    .hero-actions {
      flex-direction: column;
    }

    .empty-actions {
      flex-direction: column;
      align-items: center;
    }
  }

  /* Animations */
  @keyframes float {
    0%,
    100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-20px);
    }
  }

  @keyframes shimmer {
    0% {
      background-position: -200% 0;
    }
    100% {
      background-position: 200% 0;
    }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
