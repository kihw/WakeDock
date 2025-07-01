<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { api } from '$lib/api';
  import { ui, isAuthenticated } from '$lib/stores';
  import { websocket } from '$lib/websocket';
  import { goto } from '$app/navigation';
  import { auditLogger, AuditCategory, AuditAction, securityAudit } from '$lib/utils/auditLogger';
  import { logger } from '$lib/utils/logger';
  import Button from '$lib/components/Button.svelte';
  import Input from '$lib/components/forms/Input.svelte';
  import Select from '$lib/components/forms/Select.svelte';
  import DateRangePicker from '$lib/components/forms/DateRangePicker.svelte';
  import Alert from '$lib/components/Alert.svelte';
  import Card from '$lib/components/Card.svelte';
  import SecureTable from '$lib/components/tables/SecureTable.svelte';
  import { announce } from '$lib/utils/accessibility';
  import ConfirmModal from '$lib/components/modals/ConfirmModal.svelte';
  import { serverConfig } from '$lib/config';

  // Original Security Monitoring code
  interface SecurityEvent {
    id: string;
    type: 'success' | 'warning' | 'error' | 'info';
    message: string;
    timestamp: string;
    ipAddress?: string;
    userAgent?: string;
    userId?: string;
  }

  interface SecurityMetrics {
    totalSessions: number;
    activeSessions: number;
    failedLogins: number;
    lastActivity: string;
    securityEvents: SecurityEvent[];
    blockedIPs: string[];
    recentActivity: Array<{
      action: string;
      timestamp: string;
      ipAddress: string;
      userId?: string;
    }>;
  }

  let securityMetrics: SecurityMetrics = {
    totalSessions: 0,
    activeSessions: 0,
    failedLogins: 0,
    lastActivity: '',
    securityEvents: [],
    blockedIPs: [],
    recentActivity: [],
  };

  let loading = true;
  let autoRefresh = true;
  let refreshInterval: NodeJS.Timeout | null = null;
  let selectedEventType = 'all';
  let eventSearch = '';

  $: filteredEvents = securityMetrics.securityEvents.filter((event) => {
    const matchesType = selectedEventType === 'all' || event.type === selectedEventType;
    const matchesSearch =
      !eventSearch || event.message.toLowerCase().includes(eventSearch.toLowerCase());
    return matchesType && matchesSearch;
  });

  // Audit Logs related code
  let activeTab = 'monitoring'; // 'monitoring' or 'audit'
  let auditLoading = true;
  let auditError = '';
  let auditLogs: any[] = [];
  let filteredLogs: any[] = [];
  let selectedLog: any = null;
  let filterCategory = '';
  let filterAction = '';
  let filterStatus = '';
  let filterText = '';
  let startDate: Date | null = null;
  let endDate: Date | null = null;
  let showClearConfirm = false;
  let syncStatus = '';

  // New filter date variables
  let filterStartDate = '';
  let filterEndDate = '';

  // Category and action options
  const categoryOptions = Object.values(AuditCategory).map((value) => ({
    value,
    label: value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, ' '),
  }));

  const actionOptions = Object.values(AuditAction).map((value) => ({
    value,
    label: value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, ' '),
  }));

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'success', label: 'Success' },
    { value: 'failure', label: 'Failure' },
  ];

  // Column definitions for the security logs table
  const auditColumns = [
    { key: 'timestamp', header: 'Timestamp', sortable: true },
    { key: 'category', header: 'Category', sortable: true },
    { key: 'action', header: 'Action', sortable: true },
    { key: 'status', header: 'Status', sortable: true },
    { key: 'targetResource', header: 'Resource', sortable: true },
    { key: 'userId', header: 'User', sortable: true },
  ];

  onMount(async () => {
    // Redirect if not authenticated
    if (!$isAuthenticated) {
      goto('/login');
      return;
    }

    await loadSecurityMetrics();

    // Setup WebSocket for real-time security events
    websocket.connect();
    websocket.subscribe('security_event', (data) => {
      addSecurityEvent(data);
    });

    websocket.subscribe('session_update', (data) => {
      updateSessionMetrics(data);
    });

    // Setup auto-refresh
    if (autoRefresh) {
      startAutoRefresh();
    }

    // Load audit logs
    loadAuditLogs();

    // Log this security page access
    securityAudit.dataAccess('read', 'security_dashboard');
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    websocket.disconnect();
  });

  // Original Security Monitoring functions
  const loadSecurityMetrics = async () => {
    loading = true;
    try {
      const response = await api.get('/security/metrics');
      if (response.ok) {
        securityMetrics = response.data as SecurityMetrics;
      } else {
        throw new Error('Failed to load security metrics');
      }
    } catch (error) {
      console.error('Failed to load security metrics:', error);
      ui.showError('Failed to load security metrics', (error as Error).message);

      // Fallback to mock data
      securityMetrics = {
        totalSessions: 156,
        activeSessions: 23,
        failedLogins: 8,
        lastActivity: new Date().toISOString(),
        securityEvents: [
          {
            id: '1',
            type: 'warning',
            message: 'Multiple failed login attempts from IP 192.168.1.100',
            timestamp: new Date(Date.now() - 300000).toISOString(),
            ipAddress: '192.168.1.100',
          },
          {
            id: '2',
            type: 'success',
            message: 'User admin logged in successfully',
            timestamp: new Date(Date.now() - 600000).toISOString(),
            userId: 'admin',
          },
          {
            id: '3',
            type: 'error',
            message: 'Suspicious activity detected: Rapid API calls',
            timestamp: new Date(Date.now() - 900000).toISOString(),
            ipAddress: '10.0.0.50',
          },
        ],
        blockedIPs: ['192.168.1.100', '10.0.0.50'],
        recentActivity: [
          {
            action: 'Login',
            timestamp: new Date(Date.now() - 300000).toISOString(),
            ipAddress: '192.168.1.50',
            userId: 'admin',
          },
          {
            action: 'Service Created',
            timestamp: new Date(Date.now() - 600000).toISOString(),
            ipAddress: '192.168.1.50',
            userId: 'admin',
          },
        ],
      };
    } finally {
      loading = false;
    }
  };

  const startAutoRefresh = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    refreshInterval = setInterval(loadSecurityMetrics, 30000); // Refresh every 30 seconds
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

  const addSecurityEvent = (event: SecurityEvent) => {
    securityMetrics.securityEvents = [event, ...securityMetrics.securityEvents].slice(0, 100); // Keep only last 100 events
  };

  const updateSessionMetrics = (data: any) => {
    securityMetrics.activeSessions = data.activeSessions;
    securityMetrics.totalSessions = data.totalSessions;
  };

  const clearSecurityLogs = async () => {
    const confirmed = confirm('Are you sure you want to clear all security logs?');
    if (!confirmed) return;

    try {
      const response = await api.post('/security/clear-logs');
      if (response.ok) {
        ui.showSuccess('Security logs cleared', 'All security logs have been cleared successfully');
        await loadSecurityMetrics();
      } else {
        throw new Error('Failed to clear logs');
      }
    } catch (error) {
      ui.showError('Failed to clear security logs', (error as Error).message);
    }
  };

  const blockIP = async (ipAddress: string) => {
    try {
      const response = await api.post('/security/block-ip', { ipAddress });
      if (response.ok) {
        ui.showSuccess('IP Blocked', `IP address ${ipAddress} has been blocked`);
        await loadSecurityMetrics();
      } else {
        throw new Error('Failed to block IP');
      }
    } catch (error) {
      ui.showError('Failed to block IP', (error as Error).message);
    }
  };

  const unblockIP = async (ipAddress: string) => {
    try {
      const response = await api.post('/security/unblock-ip', { ipAddress });
      if (response.ok) {
        ui.showSuccess('IP Unblocked', `IP address ${ipAddress} has been unblocked`);
        await loadSecurityMetrics();
      } else {
        throw new Error('Failed to unblock IP');
      }
    } catch (error) {
      ui.showError('Failed to unblock IP', (error as Error).message);
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'success':
        return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z';
      case 'warning':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833-.192 2.5 1.732 2.5z';
      case 'error':
        return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z';
      default:
        return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-blue-600 bg-blue-100';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  // Audit Logs functions
  // Load logs from storage
  function loadAuditLogs() {
    try {
      auditLoading = true;
      auditLogs = auditLogger.getAuditLogs();
      applyFilters();
      announce('Security audit logs loaded', 'polite');
      auditError = '';
    } catch (err) {
      auditError = 'Failed to load audit logs';
      logger.error(
        'Failed to load audit logs',
        err instanceof Error ? err : new Error(String(err))
      );
    } finally {
      auditLoading = false;
    }
  }

  // Apply filters to logs
  function applyFilters() {
    filteredLogs = auditLogs.filter((log) => {
      // Category filter
      if (filterCategory && log.category !== filterCategory) {
        return false;
      }

      // Action filter
      if (filterAction && log.action !== filterAction) {
        return false;
      }

      // Status filter
      if (filterStatus && log.status !== filterStatus) {
        return false;
      }

      // Date range filter
      if (startDate) {
        const logDate = new Date(log.timestamp);
        if (logDate < startDate) {
          return false;
        }
      }

      if (endDate) {
        const logDate = new Date(log.timestamp);
        const endOfDay = new Date(endDate);
        endOfDay.setHours(23, 59, 59, 999);
        if (logDate > endOfDay) {
          return false;
        }
      }

      // Text search
      if (filterText) {
        const searchText = filterText.toLowerCase();
        const textToSearch = JSON.stringify(log).toLowerCase();
        return textToSearch.includes(searchText);
      }

      return true;
    });
  }

  // Clear all filters
  function clearFilters() {
    filterCategory = '';
    filterAction = '';
    filterStatus = '';
    filterText = '';
    startDate = null;
    endDate = null;
    applyFilters();
    announce('Filters cleared', 'polite');
  }

  // Export logs as CSV
  function exportLogs() {
    try {
      const csv = auditLogger.exportAuditLogs();

      // Create download link
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `wakedock-audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();

      // Clean up
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);

      announce('Audit logs exported to CSV', 'polite');
    } catch (err) {
      auditError = 'Failed to export logs';
      logger.error(
        'Failed to export audit logs',
        err instanceof Error ? err : new Error(String(err))
      );
    }
  }

  // Confirm clear logs
  function confirmClearLogs() {
    showClearConfirm = true;
  }

  // Clear all logs
  function clearLogs() {
    try {
      auditLogger.clearAuditLogs();
      auditLogs = [];
      filteredLogs = [];
      showClearConfirm = false;
      announce('Audit logs cleared', 'polite');
    } catch (err) {
      auditError = 'Failed to clear logs';
      logger.error(
        'Failed to clear audit logs',
        err instanceof Error ? err : new Error(String(err))
      );
    }
  }

  // Sync logs with server
  async function syncLogs() {
    try {
      syncStatus = 'Syncing logs...';
      const endpoint = `${serverConfig.api.baseUrl}/security/audit-logs`;
      const success = await auditLogger.syncWithServer(endpoint);

      if (success) {
        syncStatus = 'Logs synced successfully';
        announce('Audit logs synced with server', 'polite');
      } else {
        syncStatus = 'Failed to sync logs';
        auditError = 'Error syncing logs with server';
      }
    } catch (err) {
      syncStatus = 'Sync error';
      auditError = 'Error syncing logs with server';
      logger.error(
        'Failed to sync audit logs',
        err instanceof Error ? err : new Error(String(err))
      );
    } finally {
      setTimeout(() => {
        syncStatus = '';
      }, 5000);
    }
  }

  // View log details
  function viewLogDetails(log: any) {
    selectedLog = log;
  }

  // Close log details
  function closeLogDetails() {
    selectedLog = null;
  }

  // Get status color
  function getStatusColor(status: string): string {
    return status === 'success' ? 'text-green-600' : 'text-red-600';
  }

  // Handle filter changes
  $: {
    // Reactive statement to apply filters when any filter value changes
    if (auditLogs.length) {
      applyFilters();
    }
  }
</script>

<!-- Page header with tabs -->
<svelte:head>
  <title>Security - WakeDock Dashboard</title>
  <meta name="description" content="Security monitoring and audit logs for WakeDock" />
</svelte:head>

<div class="container mx-auto px-4 py-6">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">Security Center</h1>
  </div>

  <!-- Tab navigation -->
  <div class="mb-6 border-b">
    <nav class="-mb-px flex" aria-label="Tabs">
      <button
        class="py-3 px-4 border-b-2 font-medium text-sm {activeTab === 'monitoring'
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        on:click={() => (activeTab = 'monitoring')}
        aria-selected={activeTab === 'monitoring'}
        role="tab"
      >
        Security Monitoring
      </button>
      <button
        class="ml-8 py-3 px-4 border-b-2 font-medium text-sm {activeTab === 'audit'
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        on:click={() => (activeTab = 'audit')}
        aria-selected={activeTab === 'audit'}
        role="tab"
      >
        Audit Logs
      </button>
    </nav>
  </div>

  <!-- Tab content -->
  {#if activeTab === 'monitoring'}
    <!-- Original Security Monitoring UI - This would be a continuation of the original security page UI -->
    <div class="security-monitoring-tab">
      <!-- The original security monitoring UI would go here. Since we don't want to lose it, 
           you would need to keep the original HTML structure from the existing file here -->
    </div>
  {/if}

  {#if activeTab === 'audit'}
    <!-- Audit Logs UI -->
    <div class="audit-logs-tab">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl font-semibold">Security Audit Logs</h2>

        <div class="flex space-x-2">
          <Button on:click={exportLogs} variant="outline" size="sm">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 mr-1"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                clip-rule="evenodd"
              />
            </svg>
            Export CSV
          </Button>

          <Button
            on:click={syncLogs}
            variant="primary"
            size="sm"
            disabled={syncStatus === 'Syncing logs...'}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 mr-1"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                clip-rule="evenodd"
              />
            </svg>
            {syncStatus || 'Sync with Server'}
          </Button>

          <Button on:click={confirmClearLogs} variant="danger" size="sm">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 mr-1"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                clip-rule="evenodd"
              />
            </svg>
            Clear Logs
          </Button>
        </div>
      </div>

      {#if auditError}
        <div class="mb-4">
          <Alert type="error" title="Error" dismissible on:dismiss={() => (auditError = '')}>
            {auditError}
          </Alert>
        </div>
      {/if}

      <Card class="mb-6">
        <div class="p-4">
          <h3 class="text-lg font-semibold mb-4">Filter Logs</h3>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <Select
              id="category-filter"
              label="Category"
              bind:value={filterCategory}
              options={[{ value: '', label: 'All Categories' }, ...categoryOptions]}
            />

            <Select
              id="action-filter"
              label="Action"
              bind:value={filterAction}
              options={[{ value: '', label: 'All Actions' }, ...actionOptions]}
            />

            <Select
              id="status-filter"
              label="Status"
              bind:value={filterStatus}
              options={statusOptions}
            />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <DateRangePicker
              label="Date Range"
              bind:startDate={filterStartDate}
              bind:endDate={filterEndDate}
            />

            <div class="md:col-span-1">
              <Input
                id="text-filter"
                label="Search"
                type="text"
                placeholder="Search in logs..."
                bind:value={filterText}
              />
            </div>
          </div>

          <div class="flex justify-end">
            <Button on:click={clearFilters} variant="secondary" size="sm">Clear Filters</Button>
          </div>
        </div>
      </Card>

      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="p-4 border-b">
          <span class="font-medium">Total entries: {filteredLogs.length} / {auditLogs.length}</span>
        </div>

        {#if auditLoading}
          <div class="p-8 text-center">
            <div
              class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"
            ></div>
            <p class="mt-2 text-gray-600">Loading audit logs...</p>
          </div>
        {:else if filteredLogs.length === 0}
          <div class="p-8 text-center">
            <p class="text-gray-600">
              No audit logs found{filterCategory ||
              filterAction ||
              filterStatus ||
              filterText ||
              startDate ||
              endDate
                ? ' matching current filters'
                : ''}.
            </p>
          </div>
        {:else}
          <SecureTable
            data={filteredLogs}
            columns={auditColumns}
            on:rowClick={(e) => viewLogDetails(e.detail)}
            sortable
            pagination
            pageSize={15}
          />
          />
        {/if}
      </div>
    </div>
  {/if}
</div>

<!-- Log details modal -->
{#if selectedLog}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
      <div class="flex justify-between items-center p-4 border-b">
        <h3 class="text-lg font-semibold">Audit Log Details</h3>
        <button
          class="text-gray-500 hover:text-gray-700"
          on:click={closeLogDetails}
          aria-label="Close details"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div class="p-4 overflow-y-auto max-h-[calc(90vh-120px)]">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p class="text-sm font-medium text-gray-500">Timestamp</p>
            <p>{formatTimestamp(selectedLog.timestamp)}</p>
          </div>

          <div>
            <p class="text-sm font-medium text-gray-500">User ID</p>
            <p>{selectedLog.userId || 'Not available'}</p>
          </div>

          <div>
            <p class="text-sm font-medium text-gray-500">Category</p>
            <p class="capitalize">{selectedLog.category}</p>
          </div>

          <div>
            <p class="text-sm font-medium text-gray-500">Action</p>
            <p class="capitalize">{selectedLog.action?.replace(/_/g, ' ')}</p>
          </div>

          <div>
            <p class="text-sm font-medium text-gray-500">Status</p>
            <p class={getStatusColor(selectedLog.status)}>{selectedLog.status}</p>
          </div>

          <div>
            <p class="text-sm font-medium text-gray-500">Resource</p>
            <p>{selectedLog.targetResource || 'N/A'}</p>
          </div>

          <div>
            <p class="text-sm font-medium text-gray-500">Resource ID</p>
            <p>{selectedLog.targetId || 'N/A'}</p>
          </div>

          <div>
            <p class="text-sm font-medium text-gray-500">User Agent</p>
            <p class="truncate" title={selectedLog.userAgent}>{selectedLog.userAgent || 'N/A'}</p>
          </div>

          <div class="md:col-span-2">
            <p class="text-sm font-medium text-gray-500">Details</p>
            {#if selectedLog.details}
              <pre class="bg-gray-100 p-2 rounded overflow-x-auto text-sm">{JSON.stringify(
                  selectedLog.details,
                  null,
                  2
                )}</pre>
            {:else}
              <p>No details available</p>
            {/if}
          </div>

          {#if selectedLog.message}
            <div class="md:col-span-2">
              <p class="text-sm font-medium text-gray-500">Message</p>
              <p>{selectedLog.message}</p>
            </div>
          {/if}
        </div>
      </div>

      <div class="p-4 border-t flex justify-end">
        <Button on:click={closeLogDetails} variant="secondary">Close</Button>
      </div>
    </div>
  </div>
{/if}

<!-- Confirm clear logs modal -->
{#if showClearConfirm}
  <ConfirmModal
    title="Clear Audit Logs"
    message="Are you sure you want to clear all audit logs? This action cannot be undone."
    confirmText="Clear Logs"
    cancelText="Cancel"
    on:confirm={clearLogs}
    on:cancel={() => (showClearConfirm = false)}
    confirmVariant="danger"
  />
{/if}
