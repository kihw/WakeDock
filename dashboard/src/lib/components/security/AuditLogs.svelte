<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Card } from '$lib/components/ui/atoms';
  import Button from '$lib/components/ui/atoms/Button.svelte';
  import Input from '$lib/components/ui/atoms/Input.svelte';
  import Select from '$lib/components/ui/molecules/Select.svelte';
  import DateRangePicker from '$lib/components/ui/molecules/DateRangePicker.svelte';
  import SecureTable from '$lib/components/tables/SecureTable.svelte';
  import ConfirmModal from '$lib/components/ui/organisms/ConfirmModal.svelte';

  export let logs: AuditLog[] = [];
  export let loading = false;
  export let error = '';
  export let filterCategory = '';
  export let filterAction = '';
  export let filterStatus = '';
  export let filterText = '';
  export let startDate: Date | null = null;
  export let endDate: Date | null = null;

  const dispatch = createEventDispatcher<{
    refresh: void;
    clearLogs: void;
    export: { format: 'csv' | 'json' };
    filter: {
      category: string;
      action: string;
      status: string;
      text: string;
      startDate: Date | null;
      endDate: Date | null;
    };
    logSelect: { log: AuditLog };
  }>();

  interface AuditLog {
    id: string;
    timestamp: string;
    category: string;
    action: string;
    status: 'success' | 'failure';
    targetResource: string;
    userId: string;
    details?: any;
  }

  let showClearConfirm = false;
  let selectedLog: AuditLog | null = null;

  const categoryOptions = [
    { value: '', label: 'All Categories' },
    { value: 'authentication', label: 'Authentication' },
    { value: 'authorization', label: 'Authorization' },
    { value: 'data_access', label: 'Data Access' },
    { value: 'system_admin', label: 'System Admin' },
    { value: 'user_management', label: 'User Management' },
    { value: 'service_management', label: 'Service Management' },
  ];

  const actionOptions = [
    { value: '', label: 'All Actions' },
    { value: 'login', label: 'Login' },
    { value: 'logout', label: 'Logout' },
    { value: 'create', label: 'Create' },
    { value: 'read', label: 'Read' },
    { value: 'update', label: 'Update' },
    { value: 'delete', label: 'Delete' },
    { value: 'deploy', label: 'Deploy' },
    { value: 'stop', label: 'Stop' },
    { value: 'restart', label: 'Restart' },
  ];

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'success', label: 'Success' },
    { value: 'failure', label: 'Failure' },
  ];

  const auditColumns = [
    { key: 'timestamp', header: 'Timestamp', sortable: true },
    { key: 'category', header: 'Category', sortable: true },
    { key: 'action', header: 'Action', sortable: true },
    { key: 'status', header: 'Status', sortable: true },
    { key: 'targetResource', header: 'Resource', sortable: true },
    { key: 'userId', header: 'User', sortable: true },
  ];

  $: filteredLogs = logs.filter((log) => {
    const matchesCategory = !filterCategory || log.category === filterCategory;
    const matchesAction = !filterAction || log.action === filterAction;
    const matchesStatus = !filterStatus || log.status === filterStatus;
    const matchesText =
      !filterText ||
      log.targetResource?.toLowerCase().includes(filterText.toLowerCase()) ||
      log.userId?.toLowerCase().includes(filterText.toLowerCase());

    const logDate = new Date(log.timestamp);
    const matchesDateRange =
      (!startDate || logDate >= startDate) && (!endDate || logDate <= endDate);

    return matchesCategory && matchesAction && matchesStatus && matchesText && matchesDateRange;
  });

  function handleRefresh() {
    dispatch('refresh');
  }

  function handleClearLogs() {
    showClearConfirm = true;
  }

  function confirmClearLogs() {
    dispatch('clearLogs');
    showClearConfirm = false;
  }

  function handleExport(format: 'csv' | 'json') {
    dispatch('export', { format });
  }

  function handleFilterChange() {
    dispatch('filter', {
      category: filterCategory,
      action: filterAction,
      status: filterStatus,
      text: filterText,
      startDate,
      endDate,
    });
  }

  function handleLogSelect(log: AuditLog) {
    selectedLog = log;
    dispatch('logSelect', { log });
  }

  function formatTimestamp(timestamp: string) {
    return new Date(timestamp).toLocaleString();
  }

  function getStatusBadge(status: string) {
    return status === 'success'
      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
  }
</script>

<Card>
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Audit Logs</h2>
    <div class="flex items-center gap-2">
      <Button variant="outline" size="sm" on:click={handleRefresh} disabled={loading}>
        {loading ? 'Loading...' : 'Refresh'}
      </Button>
      <Button variant="outline" size="sm" on:click={() => handleExport('csv')}>Export CSV</Button>
      <Button variant="outline" size="sm" on:click={() => handleExport('json')}>Export JSON</Button>
      <Button variant="danger" size="sm" on:click={handleClearLogs}>Clear Logs</Button>
    </div>
  </div>

  {#if error}
    <div
      class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
    >
      <p class="text-red-700 dark:text-red-400">{error}</p>
    </div>
  {/if}

  <!-- Filters -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
    <Select
      options={categoryOptions}
      value={filterCategory}
      on:change={(e) => {
        filterCategory = e.detail.value;
        handleFilterChange();
      }}
      placeholder="Category"
    />
    <Select
      options={actionOptions}
      value={filterAction}
      on:change={(e) => {
        filterAction = e.detail.value;
        handleFilterChange();
      }}
      placeholder="Action"
    />
    <Select
      options={statusOptions}
      value={filterStatus}
      on:change={(e) => {
        filterStatus = e.detail.value;
        handleFilterChange();
      }}
      placeholder="Status"
    />
    <Input
      type="search"
      placeholder="Search logs..."
      value={filterText}
      on:input={(e) => {
        filterText = e.target.value;
        handleFilterChange();
      }}
    />
    <DateRangePicker bind:startDate bind:endDate on:change={handleFilterChange} />
    <div class="text-sm text-gray-500 dark:text-gray-400 flex items-center">
      {filteredLogs.length} of {logs.length} logs
    </div>
  </div>

  <!-- Logs Table -->
  {#if loading}
    <div class="p-8 text-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-2 text-gray-500 dark:text-gray-400">Loading audit logs...</p>
    </div>
  {:else}
    <SecureTable
      columns={auditColumns}
      data={filteredLogs}
      on:rowClick={(e) => handleLogSelect(e.detail)}
      emptyMessage="No audit logs found"
    >
      <svelte:fragment slot="cell" let:column let:row>
        {#if column.key === 'timestamp'}
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {formatTimestamp(row.timestamp)}
          </span>
        {:else if column.key === 'status'}
          <span
            class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusBadge(
              row.status
            )}"
          >
            {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
          </span>
        {:else if column.key === 'category'}
          <span class="text-sm font-medium text-gray-900 dark:text-white capitalize">
            {row.category.replace(/_/g, ' ')}
          </span>
        {:else if column.key === 'action'}
          <span class="text-sm text-gray-700 dark:text-gray-300 capitalize">
            {row.action.replace(/_/g, ' ')}
          </span>
        {:else}
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {row[column.key] || '-'}
          </span>
        {/if}
      </svelte:fragment>
    </SecureTable>
  {/if}
</Card>

<!-- Clear Confirmation Modal -->
<ConfirmModal
  bind:show={showClearConfirm}
  title="Clear Audit Logs"
  message="Are you sure you want to clear all audit logs? This action cannot be undone."
  confirmText="Clear Logs"
  confirmVariant="danger"
  on:confirm={confirmClearLogs}
/>
