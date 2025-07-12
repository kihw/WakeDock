<script lang="ts">
  import {
    Cpu,
    HardDrive,
    Activity,
    Container,
    TrendingUp,
    TrendingDown,
    Zap,
    Clock,
    Shield,
    AlertTriangle,
  } from 'lucide-svelte';
  import type { Writable } from 'svelte/store';

  export let stats: Writable<{
    services: {
      total: number;
      running: number;
      stopped: number;
      error: number;
    };
    system: {
      cpu_usage: number;
      memory_usage: number;
      disk_usage: number;
      uptime: number;
    };
    docker: {
      version: string;
      api_version: string;
      status: string;
    };
    caddy: {
      version: string;
      status: string;
      active_routes: number;
    };
  }>;

  function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  function formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }

  function getUsageColor(percentage: number) {
    if (percentage > 80)
      return { color: 'text-red-600', bg: 'bg-red-50 border-red-200', fill: 'high' };
    if (percentage > 60)
      return { color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200', fill: 'medium' };
    return { color: 'text-green-600', bg: 'bg-green-50 border-green-200', fill: 'low' };
  }

  function getHealthStatus(status: string) {
    return status === 'healthy'
      ? { icon: Shield, color: 'text-green-600', bg: 'bg-green-50' }
      : { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50' };
  }

  // Mock trend data (in real app this would come from props)
  const trends = {
    services: { change: +2, period: '24h' },
    cpu: { change: -5.2, period: '1h' },
    memory: { change: +1.8, period: '1h' },
    uptime: { change: +24, period: '24h' },
  };

  function getTrendIcon(change: number) {
    return change >= 0 ? TrendingUp : TrendingDown;
  }

  function getTrendColor(change: number) {
    return change >= 0 ? 'text-green-600' : 'text-red-600';
  }
</script>

<div class="stats-grid">
  <!-- Services Overview -->
  <div class="stat-card primary">
    <div class="card-header">
      <div class="stat-icon-wrapper primary">
        <Container size={24} />
      </div>
      <div class="trend-indicator">
        <svelte:component
          this={getTrendIcon(trends.services.change)}
          size={16}
          class={getTrendColor(trends.services.change)}
        />
        <span class="trend-value {getTrendColor(trends.services.change)}">
          {trends.services.change > 0 ? '+' : ''}{trends.services.change}
        </span>
      </div>
    </div>

    <div class="stat-content">
      <div class="stat-value-section">
        <div class="stat-value">{$stats?.services?.total || 0}</div>
        <div class="stat-label">Total Services</div>
      </div>

      <div class="stat-breakdown">
        <div class="breakdown-item">
          <div class="breakdown-dot running"></div>
          <span class="breakdown-label">Running</span>
          <span class="breakdown-value">{$stats?.services?.running || 0}</span>
        </div>
        <div class="breakdown-item">
          <div class="breakdown-dot stopped"></div>
          <span class="breakdown-label">Stopped</span>
          <span class="breakdown-value">{$stats?.services?.stopped || 0}</span>
        </div>
        {#if ($stats?.services?.error || 0) > 0}
          <div class="breakdown-item">
            <div class="breakdown-dot error"></div>
            <span class="breakdown-label">Error</span>
            <span class="breakdown-value">{$stats?.services?.error || 0}</span>
          </div>
        {/if}
      </div>
    </div>

    <div class="stat-footer">
      <span class="stat-trend">
        {trends.services.change > 0 ? 'Increased' : 'Decreased'} by {Math.abs(
          trends.services.change
        )} in {trends.services.period}
      </span>
    </div>
  </div>

  <!-- CPU Usage -->
  <div class="stat-card">
    <div class="card-header">
      <div class="stat-icon-wrapper {getUsageColor($stats?.system?.cpu_usage || 0).color}">
        <Cpu size={24} />
      </div>
      <div class="trend-indicator">
        <svelte:component
          this={getTrendIcon(trends.cpu.change)}
          size={16}
          class={getTrendColor(trends.cpu.change)}
        />
        <span class="trend-value {getTrendColor(trends.cpu.change)}">
          {trends.cpu.change > 0 ? '+' : ''}{trends.cpu.change}%
        </span>
      </div>
    </div>

    <div class="stat-content">
      <div class="stat-value-section">
        <div class="stat-value {getUsageColor($stats?.system?.cpu_usage || 0).color}">
          {(typeof $stats?.system?.cpu_usage === 'number' ? $stats.system.cpu_usage : 0).toFixed(
            1
          )}%
        </div>
        <div class="stat-label">CPU Usage</div>
      </div>

      <div class="usage-bar">
        <div
          class="usage-fill {getUsageColor($stats?.system?.cpu_usage || 0).fill}"
          style="width: {Math.min(
            typeof $stats?.system?.cpu_usage === 'number' ? $stats.system.cpu_usage : 0,
            100
          )}%"
        ></div>
      </div>
    </div>

    <div class="stat-footer">
      <span class="stat-trend">
        {trends.cpu.change > 0 ? 'Increased' : 'Decreased'} by {Math.abs(trends.cpu.change)}% in {trends
          .cpu.period}
      </span>
    </div>
  </div>

  <!-- Memory Usage -->
  <div class="stat-card">
    <div class="card-header">
      <div class="stat-icon-wrapper {getUsageColor($stats?.system?.memory_usage || 0).color}">
        <HardDrive size={24} />
      </div>
      <div class="trend-indicator">
        <svelte:component
          this={getTrendIcon(trends.memory.change)}
          size={16}
          class={getTrendColor(trends.memory.change)}
        />
        <span class="trend-value {getTrendColor(trends.memory.change)}">
          {trends.memory.change > 0 ? '+' : ''}{trends.memory.change}%
        </span>
      </div>
    </div>

    <div class="stat-content">
      <div class="stat-value-section">
        <div class="stat-value {getUsageColor($stats?.system?.memory_usage || 0).color}">
          {(typeof $stats?.system?.memory_usage === 'number'
            ? $stats.system.memory_usage
            : 0
          ).toFixed(1)}%
        </div>
        <div class="stat-label">Memory Usage</div>
      </div>

      <div class="usage-bar">
        <div
          class="usage-fill {getUsageColor($stats?.system?.memory_usage || 0).fill}"
          style="width: {Math.min(
            typeof $stats?.system?.memory_usage === 'number' ? $stats.system.memory_usage : 0,
            100
          )}%"
        ></div>
      </div>
    </div>

    <div class="stat-footer">
      <span class="stat-trend">
        {trends.memory.change > 0 ? 'Increased' : 'Decreased'} by {Math.abs(trends.memory.change)}%
        in {trends.memory.period}
      </span>
    </div>
  </div>

  <!-- System Uptime -->
  <div class="stat-card success">
    <div class="card-header">
      <div class="stat-icon-wrapper success">
        <Clock size={24} />
      </div>
      <div class="trend-indicator">
        <svelte:component
          this={getTrendIcon(trends.uptime.change)}
          size={16}
          class={getTrendColor(trends.uptime.change)}
        />
        <span class="trend-value {getTrendColor(trends.uptime.change)}">
          +{trends.uptime.change}h
        </span>
      </div>
    </div>

    <div class="stat-content">
      <div class="stat-value-section">
        <div class="stat-value">{formatUptime($stats?.system?.uptime || 0)}</div>
        <div class="stat-label">System Uptime</div>
      </div>

      <div class="uptime-indicator">
        <div class="uptime-dot"></div>
        <span class="uptime-status">System Online</span>
      </div>
    </div>

    <div class="stat-footer">
      <span class="stat-trend">
        Running for {formatUptime($stats?.system?.uptime || 0)} continuously
      </span>
    </div>
  </div>

  <!-- Docker Status -->
  <div class="stat-card {getHealthStatus($stats?.docker?.status || 'unknown').bg}">
    <div class="card-header">
      <div class="stat-icon-wrapper {getHealthStatus($stats?.docker?.status || 'unknown').color}">
        <svelte:component
          this={getHealthStatus($stats?.docker?.status || 'unknown').icon}
          size={24}
        />
      </div>
      <div class="version-badge">
        v{$stats?.docker?.version || 'unknown'}
      </div>
    </div>

    <div class="stat-content">
      <div class="stat-value-section">
        <div class="stat-value {getHealthStatus($stats?.docker?.status || 'unknown').color}">
          {($stats?.docker?.status || 'unknown') === 'healthy' ? 'Healthy' : 'Unhealthy'}
        </div>
        <div class="stat-label">Docker Engine</div>
      </div>

      <div class="service-info">
        <div class="info-item">
          <span class="info-label">API Version</span>
          <span class="info-value">{$stats?.docker?.api_version || 'unknown'}</span>
        </div>
      </div>
    </div>

    <div class="stat-footer">
      <span class="stat-trend"> Engine running normally </span>
    </div>
  </div>

  <!-- Caddy Status -->
  <div class="stat-card {getHealthStatus($stats?.caddy?.status || 'unknown').bg}">
    <div class="card-header">
      <div class="stat-icon-wrapper {getHealthStatus($stats?.caddy?.status || 'unknown').color}">
        <Zap size={24} />
      </div>
      <div class="routes-badge">
        {$stats?.caddy?.active_routes || 0} routes
      </div>
    </div>

    <div class="stat-content">
      <div class="stat-value-section">
        <div class="stat-value {getHealthStatus($stats?.caddy?.status || 'unknown').color}">
          {($stats?.caddy?.status || 'unknown') === 'healthy' ? 'Healthy' : 'Unhealthy'}
        </div>
        <div class="stat-label">Caddy Server</div>
      </div>

      <div class="service-info">
        <div class="info-item">
          <span class="info-label">Version</span>
          <span class="info-value">{$stats?.caddy?.version || 'unknown'}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Active Routes</span>
          <span class="info-value">{$stats?.caddy?.active_routes || 0}</span>
        </div>
      </div>
    </div>

    <div class="stat-footer">
      <span class="stat-trend"> Proxy server operational </span>
    </div>
  </div>
</div>

<style>
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-2xl);
  }

  .stat-card {
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: var(--spacing-lg);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: var(--shadow-md);
  }

  .stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  }

  .stat-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
    border-color: var(--color-primary-light);
  }

  .stat-card.primary {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
    border-color: rgba(59, 130, 246, 0.2);
  }

  .stat-card.success {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%);
    border-color: rgba(16, 185, 129, 0.2);
  }

  /* Card Header */
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
  }

  .stat-icon-wrapper {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all var(--transition-normal);
  }

  .stat-icon-wrapper.primary {
    background: var(--gradient-primary);
    color: white;
    box-shadow: var(--shadow-md);
  }

  .stat-icon-wrapper.success {
    background: var(--gradient-success);
    color: white;
    box-shadow: var(--shadow-md);
  }

  .trend-indicator {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-full);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }

  .trend-value {
    font-size: 0.75rem;
    font-weight: 600;
    font-family: monospace;
  }

  .version-badge,
  .routes-badge {
    padding: var(--spacing-xs) var(--spacing-sm);
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text-secondary);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }

  /* Card Content */
  .stat-content {
    margin-bottom: var(--spacing-lg);
  }

  .stat-value-section {
    margin-bottom: var(--spacing-md);
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: var(--spacing-xs);
    color: var(--color-text);
  }

  .stat-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  /* Service Breakdown */
  .stat-breakdown {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .breakdown-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xs) 0;
  }

  .breakdown-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .breakdown-dot.running {
    background: var(--color-success);
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
  }

  .breakdown-dot.stopped {
    background: var(--color-text-secondary);
  }

  .breakdown-dot.error {
    background: var(--color-error);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
  }

  .breakdown-label {
    font-size: 0.8rem;
    color: var(--color-text-secondary);
    flex: 1;
  }

  .breakdown-value {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--color-text);
    font-family: monospace;
  }

  /* Usage Bars */
  .usage-bar {
    height: 8px;
    background: rgba(0, 0, 0, 0.1);
    border-radius: var(--radius-full);
    overflow: hidden;
    margin-bottom: var(--spacing-sm);
  }

  .usage-fill {
    height: 100%;
    border-radius: var(--radius-full);
    transition: width var(--transition-slow);
    position: relative;
  }

  .usage-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: shimmer 2s infinite;
  }

  .usage-fill.low {
    background: var(--gradient-success);
  }

  .usage-fill.medium {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  }

  .usage-fill.high {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  }

  /* Uptime Indicator */
  .uptime-indicator {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(16, 185, 129, 0.1);
    border-radius: var(--radius);
    border: 1px solid rgba(16, 185, 129, 0.2);
  }

  .uptime-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-success);
    animation: pulse 2s infinite;
  }

  .uptime-status {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-success);
  }

  /* Service Info */
  .service-info {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .info-label {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .info-value {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text);
    font-family: monospace;
  }

  /* Card Footer */
  .stat-footer {
    border-top: 1px solid var(--color-border-light);
    padding-top: var(--spacing-md);
  }

  .stat-trend {
    font-size: 0.75rem;
    color: var(--color-text-muted);
    font-style: italic;
  }

  /* Responsive Design */
  @media (max-width: 640px) {
    .stats-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .stat-card {
      padding: var(--spacing-md);
    }

    .stat-value {
      font-size: 1.75rem;
    }

    .breakdown-item {
      padding: var(--spacing-xs);
    }
  }

  @media (max-width: 480px) {
    .card-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-sm);
    }

    .trend-indicator,
    .version-badge,
    .routes-badge {
      align-self: flex-end;
    }
  }

  /* Animations */
  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
</style>
