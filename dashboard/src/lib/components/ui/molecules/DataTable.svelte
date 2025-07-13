<!--
  DataTable Molecule - Advanced table with sorting, pagination, and search
  Combines multiple atoms for a complete data display solution
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { fly, fade } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import Button from '../atoms/Button.svelte';
  import Badge from '../atoms/Badge.svelte';
  import LoadingSpinner from '../atoms/LoadingSpinner.svelte';
  import SearchInput from './SearchInput.svelte';
  import { variants } from '$lib/design-system/tokens';
  import { debounce, createMemoized } from '$lib/utils/debounce';

  // Types
  interface Column {
    key: string;
    label: string;
    sortable?: boolean;
    width?: string;
    align?: 'left' | 'center' | 'right';
    render?: (value: any, row: any) => string;
    component?: any;
  }

  interface Row {
    id: string | number;
    [key: string]: any;
  }

  // Props
  export let columns: Column[] = [];
  export let data: Row[] = [];
  export let loading = false;
  export let searchable = false;
  export let searchPlaceholder = 'Search...';
  export let sortable = true;
  export let paginated = false;
  export let pageSize = 10;
  export let currentPage = 1;
  export let totalPages = 1;
  export let selectable = false;
  export let selectedRows: (string | number)[] = [];
  export let striped = false;
  export let hoverable = true;
  export let bordered = false;
  export let compact = false;
  export let emptyMessage = 'No data available';
  export let stickyHeader = false;
  export let maxHeight: string | undefined = undefined;
  export let actions: Array<{
    label: string;
    icon?: string;
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
    action: (row: Row) => void;
  }> = [];
  export let testId: string | undefined = undefined;

  // Events
  const dispatch = createEventDispatcher<{
    sort: { column: string; direction: 'asc' | 'desc' };
    search: { query: string };
    select: { selectedRows: (string | number)[] };
    selectAll: { selected: boolean };
    pageChange: { page: number };
    rowClick: { row: Row };
    action: { action: string; row: Row };
  }>();

  // State
  let searchQuery = '';
  let debouncedSearchQuery = '';
  let sortColumn = '';
  let sortDirection: 'asc' | 'desc' = 'asc';
  let filteredData: Row[] = [];
  let paginatedData: Row[] = [];
  let allSelected = false;
  let indeterminate = false;
  
  // Performance optimizations
  let selectedRowsSet = new Set<string | number>();
  let columnAlignCache = new Map<string, string>();
  let columnWidthCache = new Map<string, string>();

  // Debounced search handler
  const debouncedSearch = debounce((query: string) => {
    debouncedSearchQuery = query;
  }, 300);

  // Memoized column utilities
  function getColumnAlign(column: Column): string {
    if (!columnAlignCache.has(column.key)) {
      columnAlignCache.set(column.key, column.align || 'left');
    }
    return columnAlignCache.get(column.key)!;
  }

  function getColumnWidth(column: Column): string {
    if (!columnWidthCache.has(column.key)) {
      columnWidthCache.set(column.key, column.width || 'auto');
    }
    return columnWidthCache.get(column.key)!;
  }

  // Optimized selection operations
  function updateSelectedRowsSet() {
    selectedRowsSet = new Set(selectedRows);
  }

  // Watch for changes to selectedRows and update Set
  $: selectedRows, updateSelectedRowsSet();

  // Optimized data processing - combined reactive statement to reduce cascading
  $: processedData = (() => {
    // Filter data
    const filtered = debouncedSearchQuery.trim() 
      ? data.filter((row) => {
          const query = debouncedSearchQuery.toLowerCase();
          return columns.some((col) => {
            const value = row[col.key];
            return value && value.toString().toLowerCase().includes(query);
          });
        })
      : data;
    
    // Sort data (avoid array spread by mutating filtered)
    const sorted = sortColumn && sortable 
      ? filtered.sort((a, b) => {
          const aVal = a[sortColumn];
          const bVal = b[sortColumn];

          if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
          if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
          return 0;
        })
      : filtered;
    
    // Paginate data
    const paginated = paginated 
      ? sorted.slice((currentPage - 1) * pageSize, currentPage * pageSize)
      : sorted;
    
    return { filtered, sorted, paginated };
  })();

  // Extract processed data
  $: ({ filtered: filteredData, sorted: sortedData, paginated: paginatedData } = processedData);

  // Computed properties
  $: hasActions = actions.length > 0;
  $: hasData = data.length > 0;
  $: showPagination = paginated && totalPages > 1;
  $: showSearch = searchable;
  $: showHeader = columns.length > 0;

  // Optimized pagination calculation
  $: paginationPages = (() => {
    if (totalPages <= 5) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    
    const start = Math.max(1, Math.min(totalPages - 4, currentPage - 2));
    return Array.from({ length: 5 }, (_, i) => start + i).filter(page => page <= totalPages);
  })();

  // Optimized pagination info
  $: paginationInfo = {
    start: (currentPage - 1) * pageSize + 1,
    end: Math.min(currentPage * pageSize, filteredData.length),
    total: filteredData.length
  };

  // Optimized selection state using Set for O(1) lookups
  $: visibleRowIds = paginatedData.map((row) => row.id);
  $: selectedVisibleRows = selectable 
    ? visibleRowIds.filter((id) => selectedRowsSet.has(id))
    : [];
  $: allSelected = selectable && selectedVisibleRows.length === paginatedData.length && paginatedData.length > 0;
  $: indeterminate = selectable && selectedVisibleRows.length > 0 && selectedVisibleRows.length < paginatedData.length;

  // Build table classes
  $: tableClasses = [
    'min-w-full divide-y divide-secondary-200',
    bordered ? 'border border-secondary-300' : '',
    compact ? 'text-sm' : '',
  ]
    .filter(Boolean)
    .join(' ');

  $: containerClasses = [
    'overflow-hidden',
    bordered ? 'border border-secondary-300 rounded-lg' : '',
    maxHeight ? 'overflow-y-auto' : '',
    'bg-white',
  ]
    .filter(Boolean)
    .join(' ');

  $: headerClasses = ['bg-secondary-50', stickyHeader ? 'sticky top-0 z-10' : '']
    .filter(Boolean)
    .join(' ');

  // Event handlers
  function handleSort(column: Column) {
    if (!column.sortable || !sortable) return;

    if (sortColumn === column.key) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column.key;
      sortDirection = 'asc';
    }

    dispatch('sort', { column: column.key, direction: sortDirection });
  }

  function handleSearch(event: CustomEvent<{ query: string }>) {
    searchQuery = event.detail.query;
    debouncedSearch(searchQuery); // Use debounced search
    currentPage = 1; // Reset to first page
    dispatch('search', { query: searchQuery });
  }

  function handleSelectAll() {
    if (allSelected) {
      // Deselect all visible rows - optimized with Set operations
      visibleRowIds.forEach(id => selectedRowsSet.delete(id));
      selectedRows = Array.from(selectedRowsSet);
    } else {
      // Select all visible rows - optimized with Set operations
      visibleRowIds.forEach(id => selectedRowsSet.add(id));
      selectedRows = Array.from(selectedRowsSet);
    }

    dispatch('select', { selectedRows });
    dispatch('selectAll', { selected: !allSelected });
  }

  function handleRowSelect(rowId: string | number) {
    // Optimized selection using Set operations (O(1) instead of O(n))
    if (selectedRowsSet.has(rowId)) {
      selectedRowsSet.delete(rowId);
    } else {
      selectedRowsSet.add(rowId);
    }
    selectedRows = Array.from(selectedRowsSet);

    dispatch('select', { selectedRows });
  }

  function handleRowClick(row: Row) {
    dispatch('rowClick', { row });
  }

  function handleAction(action: any, row: Row) {
    action.action(row);
    dispatch('action', { action: action.label, row });
  }

  function handlePageChange(page: number) {
    currentPage = page;
    dispatch('pageChange', { page });
  }

  function getCellValue(row: Row, column: Column) {
    const value = row[column.key];

    if (column.render) {
      return column.render(value, row);
    }

    return value;
  }

</script>

<div class="space-y-4" data-testid={testId}>
  <!-- Search -->
  {#if showSearch}
    <div class="flex justify-between items-center">
      <SearchInput
        bind:value={searchQuery}
        placeholder={searchPlaceholder}
        on:search={handleSearch}
        clearable
        fullWidth={false}
        size="md"
      />

      {#if selectable && selectedRows.length > 0}
        <div class="flex items-center space-x-2">
          <Badge variant="primary" size="sm">
            {selectedRows.length} selected
          </Badge>
          <Button
            variant="secondary"
            size="sm"
            on:click={() => {
              selectedRows = [];
              dispatch('select', { selectedRows: [] });
            }}
          >
            Clear selection
          </Button>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Table container -->
  <div class={containerClasses} style={maxHeight ? `max-height: ${maxHeight}` : ''}>
    {#if loading}
      <div class="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    {:else if !hasData}
      <div class="flex items-center justify-center p-8 text-secondary-500">
        <div class="text-center">
          <svg
            class="w-12 h-12 mx-auto mb-4 text-secondary-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p class="text-lg font-medium">{emptyMessage}</p>
        </div>
      </div>
    {:else}
      <table class={tableClasses}>
        <!-- Header -->
        {#if showHeader}
          <thead class={headerClasses}>
            <tr>
              {#if selectable}
                <th
                  class="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider w-12"
                >
                  <input
                    type="checkbox"
                    checked={allSelected}
                    {indeterminate}
                    on:change={handleSelectAll}
                    class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                  />
                </th>
              {/if}

              {#each columns as column}
                <th
                  class={`px-6 py-3 text-xs font-medium text-secondary-500 uppercase tracking-wider ${
                    getColumnAlign(column) === 'center'
                      ? 'text-center'
                      : getColumnAlign(column) === 'right'
                        ? 'text-right'
                        : 'text-left'
                  } ${column.sortable && sortable ? 'cursor-pointer hover:bg-secondary-100' : ''}`}
                  style={`width: ${getColumnWidth(column)}`}
                  on:click={() => handleSort(column)}
                  on:keydown={(e) => e.key === 'Enter' && handleSort(column)}
                  tabindex={column.sortable && sortable ? 0 : -1}
                  role={column.sortable && sortable ? 'button' : undefined}
                  aria-sort={column.sortable && sortable
                    ? sortColumn === column.key
                      ? sortDirection === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : 'none'
                    : undefined}
                >
                  <div class="flex items-center space-x-1">
                    <span>{column.label}</span>
                    {#if column.sortable && sortable}
                      <div class="flex flex-col">
                        <svg
                          class={`w-3 h-3 ${sortColumn === column.key && sortDirection === 'asc' ? 'text-primary-600' : 'text-secondary-400'}`}
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M5 15l7-7 7 7"
                          />
                        </svg>
                        <svg
                          class={`w-3 h-3 -mt-1 ${sortColumn === column.key && sortDirection === 'desc' ? 'text-primary-600' : 'text-secondary-400'}`}
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </div>
                    {/if}
                  </div>
                </th>
              {/each}

              {#if hasActions}
                <th
                  class="px-6 py-3 text-right text-xs font-medium text-secondary-500 uppercase tracking-wider"
                >
                  Actions
                </th>
              {/if}
            </tr>
          </thead>
        {/if}

        <!-- Body -->
        <tbody class={`bg-white divide-y divide-secondary-200 ${striped ? 'divide-y-0' : ''}`}>
          {#each paginatedData as row, index (row.id)}
            <tr
              class={`${striped && index % 2 === 1 ? 'bg-secondary-50' : 'bg-white'} ${
                hoverable ? 'hover:bg-secondary-50' : ''
              } ${selectedRows.includes(row.id) ? 'bg-primary-50' : ''} transition-colors duration-150`}
              on:click={() => handleRowClick(row)}
              on:keydown={(e) => e.key === 'Enter' && handleRowClick(row)}
              tabindex="0"
            >
              {#if selectable}
                <td class="px-6 py-4 whitespace-nowrap w-12">
                  <input
                    type="checkbox"
                    checked={selectedRows.includes(row.id)}
                    on:change={() => handleRowSelect(row.id)}
                    on:click={(e) => e.stopPropagation()}
                    class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                  />
                </td>
              {/if}

              {#each columns as column}
                <td
                  class={`px-6 py-4 whitespace-nowrap ${compact ? 'py-2' : ''} ${
                    getColumnAlign(column) === 'center'
                      ? 'text-center'
                      : getColumnAlign(column) === 'right'
                        ? 'text-right'
                        : 'text-left'
                  }`}
                  style={`width: ${getColumnWidth(column)}`}
                >
                  {#if column.component}
                    <svelte:component this={column.component} value={row[column.key]} {row} />
                  {:else}
                    <div class="text-sm text-secondary-900">
                      {getCellValue(row, column)}
                    </div>
                  {/if}
                </td>
              {/each}

              {#if hasActions}
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div class="flex space-x-2 justify-end">
                    {#each actions as action}
                      <Button
                        variant={action.variant || 'ghost'}
                        size="sm"
                        leftIcon={action.icon}
                        on:click={(e) => {
                          e.stopPropagation();
                          handleAction(action, row);
                        }}
                      >
                        {action.label}
                      </Button>
                    {/each}
                  </div>
                </td>
              {/if}
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  <!-- Pagination -->
  {#if showPagination}
    <div class="flex items-center justify-between">
      <div class="text-sm text-secondary-700">
        Showing {paginationInfo.start} to {paginationInfo.end} of {paginationInfo.total} results
      </div>

      <div class="flex space-x-2">
        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage === 1}
          on:click={() => handlePageChange(currentPage - 1)}
        >
          Previous
        </Button>

        {#each paginationPages as page}
          <Button
            variant={page === currentPage ? 'primary' : 'ghost'}
            size="sm"
            on:click={() => handlePageChange(page)}
          >
            {page}
          </Button>
        {/each}

        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage === totalPages}
          on:click={() => handlePageChange(currentPage + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Custom checkbox styles */
  input[type='checkbox']:indeterminate {
    background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M5.707 7.293a1 1 0 0 0-1.414 1.414l2 2a1 1 0 0 0 1.414 0l4-4a1 1 0 0 0-1.414-1.414L7 8.586 5.707 7.293z'/%3e%3c/svg%3e");
    background-color: #3b82f6;
    background-size: 100% 100%;
    background-position: 50%;
    background-repeat: no-repeat;
  }

  input[type='checkbox']:indeterminate {
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 16 16'%3e%3cpath stroke='white' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 8h8'/%3e%3c/svg%3e");
  }

  /* Table scrollbar styling */
  :global(.overflow-y-auto::-webkit-scrollbar) {
    width: 8px;
  }

  :global(.overflow-y-auto::-webkit-scrollbar-track) {
    background: #f1f1f1;
  }

  :global(.overflow-y-auto::-webkit-scrollbar-thumb) {
    background: #c1c1c1;
    border-radius: 4px;
  }

  :global(.overflow-y-auto::-webkit-scrollbar-thumb:hover) {
    background: #a8a8a8;
  }
</style>
