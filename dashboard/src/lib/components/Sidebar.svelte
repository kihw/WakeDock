<!-- Refactored Sidebar using modular components -->
<script lang="ts">
  import SidebarModular from './SidebarModular.svelte';
  import type { Writable } from 'svelte/store';

  export let open: Writable<boolean>;
</script>

<!-- Use the new modular sidebar -->
<SidebarModular {open} />

<style>
  /* Backward compatibility styles are maintained in SidebarModular.svelte */
</style>
