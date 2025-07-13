<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import {
    Play,
    Square,
    ExternalLink,
    Settings,
    Cpu,
    HardDrive,
    Clock,
    Globe,
    AlertCircle,
    CheckCircle,
    Activity,
    MoreVertical,
  } from 'lucide-svelte';

  export let service: {
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
  };

  const dispatch = createEventDispatcher();

  let showDropdown = false;

  function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  function formatLastAccessed(dateString?: string): string {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  function getStatusConfig(status: string) {
    switch (status) {
      case 'running':
        return {
          class: 'status-running',
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50 border-green-200',
          label: 'Running',
        };
      case 'stopped':
        return {
          class: 'status-stopped',
          icon: Square,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50 border-gray-200',
          label: 'Stopped',
        };
      case 'starting':
        return {
          class: 'status-starting',
          icon: Activity,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50 border-blue-200',
          label: 'Starting',
        };
      case 'error':
        return {
          class: 'status-error',
          icon: AlertCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50 border-red-200',
          label: 'Error',
        };
      default:
        return {
          class: 'status-stopped',
          icon: Square,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50 border-gray-200',
          label: 'Unknown',
        };
    }
  }

  $: statusConfig = getStatusConfig(service.status);
  $: isRunning = service.status === 'running';
  $: isLoading = service.status === 'starting' || service.status === 'stopping';

  function getResourceStatus(percentage: number) {
    if (percentage > 80) return { class: 'high', color: 'text-red-600' };
    if (percentage > 60) return { class: 'medium', color: 'text-yellow-600' };
    return { class: 'low', color: 'text-green-600' };
  }
</script>

<div class="service-card" class:loading={isLoading}>
  <!-- Card Header -->
  <div class="card-header">
    <div class="service-header">
      <div class="service-icon">
        <svelte:component this={statusConfig.icon} size={20} />
      </div>
      <div class="service-meta">
        <h3 class="service-name">{service.name}</h3>
        <div class="service-url">
          <Globe size={14} />
          <span>{service.subdomain}.yourdomain.com</span>
        </div>
      </div>
    </div>

    <div class="card-actions">
      <div class="status-badge {statusConfig.class}">
        <span class="status-dot"></span>
        {statusConfig.label}
      </div>

      <div class="dropdown">
        <button
          class="dropdown-trigger"
          on:click={() => (showDropdown = !showDropdown)}
          aria-label="More options"
        >
          <MoreVertical size={16} />
        </button>

        {#if showDropdown}
          <div class="dropdown-menu">
            <button class="dropdown-item" on:click={() => dispatch('configure')}>
              <Settings size={14} />
              Configure
            </button>
            <button class="dropdown-item" on:click={() => dispatch('logs')}>
              <Activity size={14} />
              View Logs
            </button>
            {#if isRunning}
              <a
                href={`https://${service.subdomain}.yourdomain.com`}
                target="_blank"
                class="dropdown-item"
              >
                <ExternalLink size={14} />
                Open Service
              </a>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Card Body -->
  <div class="card-body">
    <!-- Service Details -->
    <div class="service-details">
      <div class="detail-grid">
        <div class="detail-item">
          <span class="detail-label">Type</span>
          <span class="detail-value">
            {service.docker_compose ? 'Compose' : 'Image'}
          </span>
        </div>

        <div class="detail-item">
          <span class="detail-label">Source</span>
          <span
            class="detail-value truncate"
            title={service.docker_compose || service.docker_image || 'N/A'}
          >
            {service.docker_compose || service.docker_image || 'N/A'}
          </span>
        </div>

        {#if service.ports.length > 0}
          <div class="detail-item">
            <span class="detail-label">Ports</span>
            <div class="port-tags">
              {#each service.ports.slice(0, 2) as port}
                <span class="port-tag">{port}</span>
              {/each}
              {#if service.ports.length > 2}
                <span class="port-tag more">+{service.ports.length - 2}</span>
              {/if}
            </div>
          </div>
        {/if}

        <div class="detail-item">
          <span class="detail-label">Last accessed</span>
          <div class="last-accessed">
            <Clock size={12} />
            <span>{formatLastAccessed(service.last_accessed)}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Resource Usage -->
    {#if service.resource_usage && isRunning}
      <div class="resource-usage">
        <h4 class="resource-title">Resource Usage</h4>
        <div class="resource-grid">
          <div class="resource-metric">
            <div class="metric-header">
              <div class="metric-icon">
                <Cpu size={16} />
              </div>
              <div class="metric-info">
                <span class="metric-label">CPU</span>
                <span
                  class="metric-value {getResourceStatus(service.resource_usage.cpu_percent).color}"
                >
                  {(typeof service.resource_usage.cpu_percent === 'number'
                    ? service.resource_usage.cpu_percent
                    : 0
                  ).toFixed(1)}%
                </span>
              </div>
            </div>
            <div class="metric-bar">
              <div
                class="metric-fill {getResourceStatus(service.resource_usage.cpu_percent).class}"
                style="width: {Math.min(service.resource_usage.cpu_percent, 100)}%"
              ></div>
            </div>
          </div>

          <div class="resource-metric">
            <div class="metric-header">
              <div class="metric-icon">
                <HardDrive size={16} />
              </div>
              <div class="metric-info">
                <span class="metric-label">Memory</span>
                <span
                  class="metric-value {getResourceStatus(service.resource_usage.memory_percent)
                    .color}"
                >
                  {formatBytes(service.resource_usage.memory_usage)}
                </span>
              </div>
            </div>
            <div class="metric-bar">
              <div
                class="metric-fill {getResourceStatus(service.resource_usage.memory_percent).class}"
                style="width: {Math.min(service.resource_usage.memory_percent, 100)}%"
              ></div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Card Footer -->
  <div class="card-footer">
    <div class="action-buttons">
      {#if isRunning}
        <button
          class="btn btn-warning btn-sm"
          on:click={() => dispatch('sleep')}
          disabled={isLoading}
        >
          <Square size={14} />
          Sleep
        </button>
      {:else}
        <button
          class="btn btn-success btn-sm"
          on:click={() => dispatch('wake')}
          disabled={isLoading}
        >
          <Play size={14} />
          Wake
        </button>
      {/if}

      <a href={`/services/${service.id}`} class="btn btn-secondary btn-sm">
        <Settings size={14} />
        Manage
      </a>

      {#if isRunning}
        <a
          href={`https://${service.subdomain}.yourdomain.com`}
          target="_blank"
          class="btn btn-primary btn-sm"
        >
          <ExternalLink size={14} />
          Visit
        </a>
      {/if}
    </div>
  </div>
</div>

<!-- Click outside to close dropdown -->
<svelte:window
  on:click={(e) => {
    const target = e.target;
    if (target && target instanceof Element && target.closest && !target.closest('.dropdown')) {
      showDropdown = false;
    }
  }}
/>

<style>
  .service-card {
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    overflow: hidden;
    transition: all var(--transition-normal);
    position: relative;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: var(--shadow-md);
  }

  .service-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  }

  .service-card:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-xl);
    border-color: var(--color-primary-light);
  }

  .service-card.loading {
    position: relative;
    overflow: hidden;
  }

  .service-card.loading::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    animation: shimmer 2s infinite;
  }

  /* Card Header */
  .card-header {
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-light);
    background: rgba(255, 255, 255, 0.05);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .service-header {
    display: flex;
    gap: var(--spacing-md);
    align-items: flex-start;
    flex: 1;
    min-width: 0;
  }

  .service-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-lg);
    background: var(--gradient-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
    box-shadow: var(--shadow-sm);
  }

  .service-meta {
    flex: 1;
    min-width: 0;
  }

  .service-name {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0;
    margin-bottom: var(--spacing-xs);
    color: var(--color-text);
    line-height: 1.3;
  }

  .service-url {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: 0.8rem;
    color: var(--color-text-muted);
    font-family: monospace;
  }

  .card-actions {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-sm);
    flex-shrink: 0;
  }

  /* Status Badge */
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    position: relative;
  }

  .status-dot::after {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    border-radius: 50%;
    opacity: 0.3;
    animation: pulse 2s infinite;
  }

  .status-running {
    background: rgba(16, 185, 129, 0.1);
    color: var(--color-success);
    border-color: rgba(16, 185, 129, 0.3);
  }

  .status-running .status-dot {
    background: var(--color-success);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
  }

  .status-running .status-dot::after {
    background: var(--color-success);
  }

  .status-stopped {
    background: rgba(107, 114, 128, 0.1);
    color: var(--color-text-secondary);
    border-color: rgba(107, 114, 128, 0.3);
  }

  .status-stopped .status-dot {
    background: var(--color-text-secondary);
  }

  .status-starting {
    background: rgba(59, 130, 246, 0.1);
    color: var(--color-primary);
    border-color: rgba(59, 130, 246, 0.3);
  }

  .status-starting .status-dot {
    background: var(--color-primary);
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
  }

  .status-starting .status-dot::after {
    background: var(--color-primary);
  }

  .status-error {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-error);
    border-color: rgba(239, 68, 68, 0.3);
  }

  .status-error .status-dot {
    background: var(--color-error);
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
  }

  .status-error .status-dot::after {
    background: var(--color-error);
  }

  /* Dropdown */
  .dropdown {
    position: relative;
  }

  .dropdown-trigger {
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    padding: var(--spacing-xs);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-normal);
  }

  .dropdown-trigger:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--color-text);
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 160px;
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-xl);
    z-index: 10;
    overflow: hidden;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    animation: slideIn 0.2s ease-out;
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    background: none;
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    text-decoration: none;
    cursor: pointer;
    transition: all var(--transition-normal);
  }

  .dropdown-item:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--color-text);
  }

  /* Card Body */
  .card-body {
    padding: var(--spacing-lg);
  }

  .service-details {
    margin-bottom: var(--spacing-lg);
  }

  .detail-grid {
    display: grid;
    gap: var(--spacing-md);
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .detail-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text-secondary);
    flex-shrink: 0;
  }

  .detail-value {
    font-size: 0.875rem;
    color: var(--color-text);
    text-align: right;
    flex: 1;
    min-width: 0;
  }

  .detail-value.truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .port-tags {
    display: flex;
    gap: var(--spacing-xs);
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .port-tag {
    background: var(--color-surface-glass);
    color: var(--color-text-secondary);
    font-size: 0.75rem;
    font-weight: 500;
    padding: 2px 6px;
    border-radius: var(--spacing-xs);
    font-family: monospace;
  }

  .port-tag.more {
    background: var(--color-primary);
    color: white;
  }

  .last-accessed {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: 0.875rem;
    color: var(--color-text-muted);
  }

  /* Resource Usage */
  .resource-usage {
    border-top: 1px solid var(--color-border-light);
    padding-top: var(--spacing-lg);
  }

  .resource-title {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: var(--spacing-md);
    color: var(--color-text);
  }

  .resource-grid {
    display: grid;
    gap: var(--spacing-md);
  }

  .resource-metric {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .metric-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .metric-icon {
    color: var(--color-text-muted);
  }

  .metric-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex: 1;
  }

  .metric-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .metric-value {
    font-size: 0.75rem;
    font-weight: 600;
    font-family: monospace;
  }

  .metric-bar {
    height: 6px;
    background: rgba(0, 0, 0, 0.1);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .metric-fill {
    height: 100%;
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .metric-fill.low {
    background: var(--gradient-success);
  }

  .metric-fill.medium {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  }

  .metric-fill.high {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  }

  /* Card Footer */
  .card-footer {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--color-border-light);
    background: rgba(0, 0, 0, 0.02);
  }

  .action-buttons {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .action-buttons .btn {
    flex: 1;
    min-width: fit-content;
  }

  /* Enhanced Responsive Design */

  /* Large screens - better spacing and layout */
  @media (min-width: 1200px) {
    .service-card {
      min-height: 400px;
    }

    .card-header {
      padding: var(--spacing-xl);
    }

    .card-body {
      padding: var(--spacing-xl);
    }

    .card-footer {
      padding: var(--spacing-xl);
    }

    .service-name {
      font-size: 1.25rem;
    }

    .resource-grid {
      grid-template-columns: 1fr 1fr;
      gap: var(--spacing-lg);
    }
  }

  /* Medium screens - maintain good proportions */
  @media (max-width: 992px) and (min-width: 769px) {
    .action-buttons {
      gap: var(--spacing-xs);
    }

    .action-buttons .btn {
      font-size: 0.75rem;
      padding: var(--spacing-xs) var(--spacing-sm);
    }
  }

  /* Tablet size - optimize for medium screens */
  @media (max-width: 768px) and (min-width: 577px) {
    .service-header {
      gap: var(--spacing-sm);
    }

    .service-icon {
      width: 40px;
      height: 40px;
    }

    .service-name {
      font-size: 1rem;
    }

    .action-buttons {
      flex-wrap: nowrap;
      gap: var(--spacing-xs);
    }

    .action-buttons .btn {
      flex: 1;
      min-width: 0;
      font-size: 0.75rem;
    }
  }

  /* Small screens - stack elements */
  @media (max-width: 576px) {
    .card-header {
      padding: var(--spacing-md);
    }

    .card-body {
      padding: var(--spacing-md);
    }

    .card-footer {
      padding: var(--spacing-md);
    }

    .action-buttons {
      flex-direction: column;
    }

    .action-buttons .btn {
      flex: none;
    }

    .service-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-sm);
    }

    .card-actions {
      align-self: flex-start;
    }
  }

  /* Loading Animation */
  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
</style>
