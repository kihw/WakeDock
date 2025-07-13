<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Card } from '$lib/components/ui/atoms';
  import Input from '$lib/components/ui/atoms/Input.svelte';
  import Select from '$lib/components/ui/molecules/Select.svelte';

  export let events: SecurityEvent[] = [];
  export let loading = false;
  export let searchTerm = '';
  export let selectedType = 'all';

  const dispatch = createEventDispatcher<{
    search: { term: string };
    filter: { type: string };
    eventClick: { event: SecurityEvent };
  }>();

  interface SecurityEvent {
    id: string;
    type: 'success' | 'warning' | 'error' | 'info';
    message: string;
    timestamp: string;
    ipAddress?: string;
    userAgent?: string;
    userId?: string;
  }

  const typeOptions = [
    { value: 'all', label: 'All Events' },
    { value: 'success', label: 'Success' },
    { value: 'warning', label: 'Warning' },
    { value: 'error', label: 'Error' },
    { value: 'info', label: 'Info' },
  ];

  $: filteredEvents = events.filter((event) => {
    const matchesType = selectedType === 'all' || event.type === selectedType;
    const matchesSearch =
      !searchTerm ||
      event.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.ipAddress?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.userId?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesType && matchesSearch;
  });

  function handleSearch(event: Event) {
    const target = event.target as HTMLInputElement;
    searchTerm = target.value;
    dispatch('search', { term: searchTerm });
  }

  function handleFilter(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedType = target.value;
    dispatch('filter', { type: selectedType });
  }

  function handleEventClick(event: SecurityEvent) {
    dispatch('eventClick', { event });
  }

  function getEventIcon(type: string) {
    switch (type) {
      case 'success':
        return { icon: '✓', class: 'text-green-500 bg-green-100 dark:bg-green-900' };
      case 'warning':
        return { icon: '⚠', class: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900' };
      case 'error':
        return { icon: '✗', class: 'text-red-500 bg-red-100 dark:bg-red-900' };
      default:
        return { icon: 'ℹ', class: 'text-blue-500 bg-blue-100 dark:bg-blue-900' };
    }
  }

  function formatTimestamp(timestamp: string) {
    return new Date(timestamp).toLocaleString();
  }
</script>

<Card>
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Security Events</h2>
    <div class="text-sm text-gray-500 dark:text-gray-400">
      {filteredEvents.length} of {events.length} events
    </div>
  </div>

  <!-- Filters -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
    <Input
      type="search"
      placeholder="Search events, IPs, users..."
      value={searchTerm}
      on:input={handleSearch}
    />
    <Select options={typeOptions} value={selectedType} on:change={handleFilter} />
  </div>

  <!-- Events Table -->
  <div class="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
    {#if loading}
      <div class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-500 dark:text-gray-400">Loading events...</p>
      </div>
    {:else if filteredEvents.length === 0}
      <div class="p-8 text-center">
        <p class="text-gray-500 dark:text-gray-400">
          {events.length === 0 ? 'No security events found' : 'No events match your filters'}
        </p>
      </div>
    {:else}
      <div class="max-h-96 overflow-y-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-800 sticky top-0">
            <tr>
              <th
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              >
                Type
              </th>
              <th
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              >
                Message
              </th>
              <th
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              >
                Timestamp
              </th>
              <th
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              >
                IP Address
              </th>
              <th
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              >
                User
              </th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {#each filteredEvents as event (event.id)}
              <tr
                class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                on:click={() => handleEventClick(event)}
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  {@const iconInfo = getEventIcon(event.type)}
                  <div class="flex items-center">
                    <span
                      class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium {iconInfo.class}"
                    >
                      {iconInfo.icon}
                    </span>
                    <span class="ml-2 text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {event.type}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm text-gray-900 dark:text-white max-w-xs truncate">
                    {event.message}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {formatTimestamp(event.timestamp)}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {event.ipAddress || '-'}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {event.userId || 'Anonymous'}
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</Card>
