<script lang="ts">
  export let data: any[] = [];
  export let columns: Array<{
    key: string;
    label: string;
    sortable?: boolean;
    width?: string;
    align?: 'left' | 'center' | 'right';
  }> = [];
  export let renderCell: (item: any, column: any) => string = (item, column) =>
    item[column.key] || '';
  export let sortBy: string | null = null;
  export let sortDirection: 'asc' | 'desc' = 'asc';
  export let className: string = '';

  let sortedData = data;

  $: {
    if (sortBy && typeof sortBy === 'string') {
      sortedData = [...data].sort((a, b) => {
        const aVal = a[sortBy as string];
        const bVal = b[sortBy as string];

        if (aVal === bVal) return 0;

        let result = 0;
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          result = aVal.localeCompare(bVal);
        } else if (typeof aVal === 'number' && typeof bVal === 'number') {
          result = aVal - bVal;
        } else if (aVal instanceof Date && bVal instanceof Date) {
          result = aVal.getTime() - bVal.getTime();
        } else {
          result = String(aVal).localeCompare(String(bVal));
        }

        return sortDirection === 'desc' ? -result : result;
      });
    } else {
      sortedData = data;
    }
  }

  function handleSort(column: any) {
    if (!column.sortable) return;

    if (sortBy === column.key) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = column.key;
      sortDirection = 'asc';
    }
  }

  function getSortIcon(column: any) {
    if (!column.sortable) return '';
    if (sortBy !== column.key) return '↕️';
    return sortDirection === 'asc' ? '↑' : '↓';
  }

  function getAlignClass(align: string = 'left') {
    switch (align) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-right';
      default:
        return 'text-left';
    }
  }
</script>

<div class="overflow-x-auto">
  <table class="min-w-full divide-y divide-gray-200 {className}">
    <thead class="bg-gray-50">
      <tr>
        {#each columns as column}
          <th
            class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider {getAlignClass(
              column.align
            )} {column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''}"
            style={column.width ? `width: ${column.width}` : ''}
            on:click={() => handleSort(column)}
            on:keydown={(e) => e.key === 'Enter' && handleSort(column)}
            tabindex={column.sortable ? 0 : -1}
            role={column.sortable ? 'button' : 'columnheader'}
            aria-sort={sortBy === column.key
              ? sortDirection === 'asc'
                ? 'ascending'
                : 'descending'
              : 'none'}
          >
            <div class="flex items-center justify-between">
              <span>{column.label}</span>
              {#if column.sortable}
                <span class="ml-2 text-gray-400">{getSortIcon(column)}</span>
              {/if}
            </div>
          </th>
        {/each}
      </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
      {#each sortedData as item, index}
        <tr class="hover:bg-gray-50">
          {#each columns as column}
            <td
              class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 {getAlignClass(
                column.align
              )}"
              style={column.width ? `width: ${column.width}` : ''}
            >
              <slot name="cell" {item} {column} {index}>
                {renderCell(item, column)}
              </slot>
            </td>
          {/each}
        </tr>
      {:else}
        <tr>
          <td colspan={columns.length} class="px-6 py-4 text-center text-gray-500">
            <slot name="empty">No data available</slot>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  th[role='button']:focus {
    outline: 2px solid #3b82f6;
    outline-offset: -2px;
  }
</style>
