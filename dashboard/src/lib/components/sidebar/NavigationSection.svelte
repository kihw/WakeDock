<!-- Navigation Section Component -->
<script lang="ts">
  import NavigationItem from './NavigationItem.svelte';

  export let title: string;
  export let titleId: string;
  export let items: Array<{
    label: string;
    href: string;
    icon: any;
    description: string;
    shortcut: string;
  }>;
  export let currentPath: string;
  export let sectionType: 'main' | 'admin' = 'main';
  export let onNavigate: (item: any) => void;

  function isActive(href: string): boolean {
    if (href === '/') {
      return currentPath === '/';
    }
    return currentPath.startsWith(href);
  }
</script>

<div class="nav-section" role="group" aria-labelledby={titleId}>
  <h2 id={titleId} class="nav-section-title">{title}</h2>
  {#each items as item, index}
    <NavigationItem {item} {index} {sectionType} {onNavigate} isActive={isActive(item.href)} />
  {/each}
</div>

<style>
  .nav-section {
    margin-bottom: var(--spacing-xl);
  }

  .nav-section:last-child {
    margin-bottom: 0;
  }

  .nav-section-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-text-muted);
    margin: 0 0 var(--spacing-md) 0;
    padding: 0 var(--spacing-sm);
  }
</style>
