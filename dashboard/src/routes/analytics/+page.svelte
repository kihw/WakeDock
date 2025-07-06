<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { api } from '$lib/api';
  import { websocketClient } from '$lib/websocket';
  import { isAuthenticated } from '$lib/stores';
  import { goto } from '$app/navigation';

  interface AnalyticsData {
    overview: {
      totalRequests: number;
      successfulRequests: number;
      failedRequests: number;
      avgResponseTime: number;
    };
    serviceUsage: Array<{
      name: string;
      requests: number;
      percentage: number;
      uptime: number;
    }>;
    systemMetrics: {
      cpuUsage: number[];
      memoryUsage: number[];
      diskUsage: number[];
      networkIO: number[];
    };
    timeRange: string;
  }

  let analyticsData: AnalyticsData = {
    overview: {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      avgResponseTime: 0,
    },
    serviceUsage: [],
    systemMetrics: {
      cpuUsage: [],
      memoryUsage: [],
      diskUsage: [],
      networkIO: [],
    },
    timeRange: '24h',
  };

  let loading = true;
  let error = '';
  let selectedTimeRange = '24h';
  let autoRefresh = true;
  let refreshInterval: NodeJS.Timeout | null = null;

  onMount(async () => {
    // Redirect if not authenticated
    if (!$isAuthenticated) {
      goto('/login');
      return;
    }

    await loadAnalytics();

    // Setup WebSocket for real-time metrics
    websocketClient.connect();
    websocketClient.subscribe('system_metrics', (data) => {
      updateSystemMetrics(data);
    });

    websocketClient.subscribe('request_metrics', (data) => {
      updateRequestMetrics(data);
    });

    // Setup auto-refresh
    if (autoRefresh) {
      startAutoRefresh();
    }
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    websocketClient.disconnect();
  });

  const loadAnalytics = async () => {
    loading = true;
    error = '';

    try {
      const response = await api.get(`/analytics?timeRange=${selectedTimeRange}`);
      if (response.ok) {
        analyticsData = response.data as AnalyticsData;
      } else {
        throw new Error('Failed to fetch analytics data');
      }
    } catch (err) {
      error = 'Failed to load analytics data: ' + (err as Error).message;
      console.error('Analytics error:', err);

      // Fallback to mock data if API fails
      analyticsData = {
        overview: {
          totalRequests: 12847,
          successfulRequests: 12234,
          failedRequests: 613,
          avgResponseTime: 245,
        },
        serviceUsage: [
          { name: 'nginx-web', requests: 5432, percentage: 42.3, uptime: 99.9 },
          { name: 'redis-cache', requests: 3241, percentage: 25.2, uptime: 99.8 },
          { name: 'postgres-db', requests: 2156, percentage: 16.8, uptime: 99.5 },
          { name: 'api-gateway', requests: 2018, percentage: 15.7, uptime: 98.9 },
        ],
        systemMetrics: {
          cpuUsage: [23, 45, 32, 67, 54, 23, 45],
          memoryUsage: [56, 62, 58, 71, 68, 59, 63],
          diskUsage: [34, 35, 36, 37, 36, 35, 34],
          networkIO: [12, 18, 15, 22, 19, 14, 17],
        },
        timeRange: selectedTimeRange,
      };
    } finally {
      loading = false;
    }
  };

  const startAutoRefresh = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    refreshInterval = setInterval(loadAnalytics, 30000); // Refresh every 30 seconds
  };

  const stopAutoRefresh = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  };

  const toggleAutoRefresh = () => {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  };

  const updateSystemMetrics = (data: any) => {
    // Update system metrics with real-time data
    analyticsData.systemMetrics = {
      ...analyticsData.systemMetrics,
      cpuUsage: [...analyticsData.systemMetrics.cpuUsage.slice(1), data.cpu],
      memoryUsage: [...analyticsData.systemMetrics.memoryUsage.slice(1), data.memory],
      diskUsage: [...analyticsData.systemMetrics.diskUsage.slice(1), data.disk],
      networkIO: [...analyticsData.systemMetrics.networkIO.slice(1), data.network],
    };
  };

  const updateRequestMetrics = (data: any) => {
    // Update request metrics with real-time data
    analyticsData.overview = {
      ...analyticsData.overview,
      totalRequests: data.totalRequests,
      successfulRequests: data.successfulRequests,
      failedRequests: data.failedRequests,
      avgResponseTime: data.avgResponseTime,
    };
  };

  const handleTimeRangeChange = async (range: string) => {
    selectedTimeRange = range;
    await loadAnalytics();
  };
</script>

<svelte:head>
  <title>Analytics - WakeDock</title>
</svelte:head>

<div class="analytics-page">
  <div class="page-header">
    <h1>Analytics</h1>
    <p class="page-description">Monitor service usage, performance metrics, and system insights</p>
  </div>

  {#if loading}
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading analytics data...</p>
    </div>
  {:else if error}
    <div class="error-container">
      <div class="error-icon">⚠️</div>
      <h3>Error Loading Analytics</h3>
      <p>{error}</p>
      <button class="btn btn-primary" on:click={() => window.location.reload()}> Retry </button>
    </div>
  {:else}
    <div class="analytics-content">
      <!-- Overview Cards -->
      <div class="overview-section">
        <h2>Overview</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <div class="stat-value">{analyticsData.overview.totalRequests.toLocaleString()}</div>
              <div class="stat-label">Total Requests</div>
            </div>
          </div>

          <div class="stat-card success">
            <div class="stat-icon">✅</div>
            <div class="stat-content">
              <div class="stat-value">
                {analyticsData.overview.successfulRequests.toLocaleString()}
              </div>
              <div class="stat-label">Successful</div>
            </div>
          </div>

          <div class="stat-card error">
            <div class="stat-icon">❌</div>
            <div class="stat-content">
              <div class="stat-value">{analyticsData.overview.failedRequests.toLocaleString()}</div>
              <div class="stat-label">Failed</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">⚡</div>
            <div class="stat-content">
              <div class="stat-value">{analyticsData.overview.avgResponseTime}ms</div>
              <div class="stat-label">Avg Response Time</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Service Usage -->
      <div class="service-usage-section">
        <h2>Service Usage</h2>
        <div class="card">
          <div class="card-body">
            <div class="usage-chart">
              {#each analyticsData.serviceUsage as service}
                <div class="usage-item">
                  <div class="usage-info">
                    <span class="service-name">{service.name}</span>
                    <span class="request-count">{service.requests.toLocaleString()} requests</span>
                  </div>
                  <div class="usage-bar">
                    <div class="usage-fill" style="width: {service.percentage}%"></div>
                  </div>
                  <span class="usage-percentage">{service.percentage}%</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <!-- System Metrics -->
      <div class="metrics-section">
        <h2>System Metrics (Last 7 Days)</h2>
        <div class="metrics-grid">
          <div class="metric-card">
            <h3>CPU Usage</h3>
            <div class="mini-chart">
              {#each analyticsData.systemMetrics.cpuUsage as value, index}
                <div class="chart-bar" style="height: {value}%">
                  <span class="chart-value">{value}%</span>
                </div>
              {/each}
            </div>
          </div>

          <div class="metric-card">
            <h3>Memory Usage</h3>
            <div class="mini-chart">
              {#each analyticsData.systemMetrics.memoryUsage as value, index}
                <div class="chart-bar" style="height: {value}%">
                  <span class="chart-value">{value}%</span>
                </div>
              {/each}
            </div>
          </div>

          <div class="metric-card">
            <h3>Disk Usage</h3>
            <div class="mini-chart">
              {#each analyticsData.systemMetrics.diskUsage as value, index}
                <div class="chart-bar" style="height: {value}%">
                  <span class="chart-value">{value}%</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .analytics-page {
    max-width: 1400px;
    margin: 0 auto;
    padding: var(--spacing-lg);
  }

  .page-header {
    margin-bottom: var(--spacing-2xl);
  }

  .page-header h1 {
    margin-bottom: var(--spacing-sm);
  }

  .page-description {
    color: var(--color-text-secondary);
    font-size: 1.125rem;
    margin: 0;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    gap: var(--spacing-md);
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--color-border);
    border-top: 4px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .error-container {
    text-align: center;
    padding: var(--spacing-3xl);
    color: var(--color-error);
  }

  .error-icon {
    font-size: 3rem;
    margin-bottom: var(--spacing-lg);
  }

  .analytics-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2xl);
  }

  .overview-section h2,
  .service-usage-section h2,
  .metrics-section h2 {
    margin-bottom: var(--spacing-lg);
    color: var(--color-text);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-lg);
  }

  .stat-card {
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    transition: all var(--transition-normal);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
  }

  .stat-card.success {
    border-color: rgba(16, 185, 129, 0.3);
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(255, 255, 255, 0.9) 100%);
  }

  .stat-card.error {
    border-color: rgba(239, 68, 68, 0.3);
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(255, 255, 255, 0.9) 100%);
  }

  .stat-icon {
    font-size: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    background: rgba(59, 130, 246, 0.1);
    border-radius: var(--radius);
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text);
    line-height: 1;
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin-top: var(--spacing-xs);
  }

  .usage-chart {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .usage-item {
    display: grid;
    grid-template-columns: 1fr 200px 60px;
    gap: var(--spacing-md);
    align-items: center;
  }

  .usage-info {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .service-name {
    font-weight: 500;
    color: var(--color-text);
  }

  .request-count {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .usage-bar {
    height: 8px;
    background: var(--color-border);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .usage-fill {
    height: 100%;
    background: var(--gradient-primary);
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .usage-percentage {
    text-align: right;
    font-weight: 500;
    color: var(--color-text);
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-lg);
  }

  .metric-card {
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
  }

  .metric-card h3 {
    margin-bottom: var(--spacing-md);
    color: var(--color-text);
    font-size: 1.125rem;
  }

  .mini-chart {
    display: flex;
    align-items: end;
    gap: var(--spacing-xs);
    height: 100px;
  }

  .chart-bar {
    flex: 1;
    background: var(--gradient-primary);
    border-radius: var(--radius) var(--radius) 0 0;
    min-height: 20px;
    position: relative;
    transition: all var(--transition-normal);
    cursor: pointer;
  }

  .chart-bar:hover {
    opacity: 0.8;
  }

  .chart-value {
    position: absolute;
    top: -25px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.75rem;
    color: var(--color-text-secondary);
    opacity: 0;
    transition: opacity var(--transition-normal);
  }

  .chart-bar:hover .chart-value {
    opacity: 1;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 768px) {
    .analytics-page {
      padding: var(--spacing-md);
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .usage-item {
      grid-template-columns: 1fr;
      gap: var(--spacing-sm);
    }

    .usage-bar {
      order: 2;
    }

    .usage-percentage {
      order: 3;
      text-align: left;
    }

    .metrics-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
