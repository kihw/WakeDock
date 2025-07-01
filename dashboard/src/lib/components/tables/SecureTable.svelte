<script lang="ts">
  export let data: any[] = [];
  export let columns: any[] = [];
  export let sortable: boolean = false;
  export let pagination: boolean = false;
  export let pageSize: number = 10;
  export let className: string = '';

  // Allow `class` prop as well
  let cssClass = '';
  export { cssClass as class };

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  let currentPage = 0;
  let sortBy: string | null = null;
  let sortDirection: 'asc' | 'desc' = 'asc';

  $: totalPages = pagination ? Math.ceil(data.length / pageSize) : 1;
  $: paginatedData = pagination
    ? data.slice(currentPage * pageSize, (currentPage + 1) * pageSize)
    : data;

  function handleSort(column: any) {
    if (!sortable || !column.sortable) return;

    if (sortBy === column.key) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = column.key;
      sortDirection = 'asc';
    }

    dispatch('sort', { sortBy, sortDirection });
  }

  function handleRowClick(item: any) {
    dispatch('rowClick', item);
  }
</script>

<div class="secure-table {className} {cssClass}">
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          {#each columns as column}
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              class:sortable={sortable && column.sortable}
              on:click={() => handleSort(column)}
            >
              <div class="flex items-center space-x-1">
                <span>{column.label}</span>
                {#if sortable && column.sortable && sortBy === column.key}
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    {#if sortDirection === 'asc'}
                      <path
                        fill-rule="evenodd"
                        d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                        clip-rule="evenodd"
                      />
                    {:else}
                      <path
                        fill-rule="evenodd"
                        d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                        clip-rule="evenodd"
                      />
                    {/if}
                  </svg>
                {/if}
              </div>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        {#each paginatedData as item, index}
          <tr class="hover:bg-gray-50 cursor-pointer" on:click={() => handleRowClick(item)}>
            {#each columns as column}
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {#if column.render}
                  {@html column.render(item[column.key], item)}
                {:else}
                  {item[column.key] || ''}
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  {#if pagination && totalPages > 1}
    <div class="flex items-center justify-between px-6 py-3 bg-gray-50 border-t">
      <div class="text-sm text-gray-700">
        Showing {currentPage * pageSize + 1} to {Math.min(
          (currentPage + 1) * pageSize,
          data.length
        )} of {data.length} results
      </div>
      <div class="flex space-x-2">
        <button
          class="px-3 py-1 text-sm border rounded disabled:opacity-50"
          disabled={currentPage === 0}
          on:click={() => currentPage--}
        >
          Previous
        </button>
        <button
          class="px-3 py-1 text-sm border rounded disabled:opacity-50"
          disabled={currentPage >= totalPages - 1}
          on:click={() => currentPage++}
        >
          Next
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .sortable:hover {
    background-color: #f9fafb;
  }
</style>
