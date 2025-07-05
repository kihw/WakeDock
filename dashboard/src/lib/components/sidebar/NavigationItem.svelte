<!-- Navigation Item Component -->
<script lang="ts">
  import { announceToScreenReader } from '$lib/utils/accessibility';

  export let item: {
    label: string;
    href: string;
    icon: any;
    description: string;
    shortcut: string;
  };
  export let isActive: boolean = false;
  export let index: number;
  export let sectionType: 'main' | 'admin' = 'main';
  export let onNavigate: (item: any) => void;

  function handleClick() {
    announceToScreenReader(`Navigating to ${item.label} - ${item.description}`);
    onNavigate(item);
  }
</script>

<a
  href={item.href}
  class="nav-item"
  class:active={isActive}
  on:click={handleClick}
  role="menuitem"
  tabindex="0"
  aria-label="{item.label} - {item.description}"
  aria-describedby="nav-{sectionType}-{index}-desc"
  aria-current={isActive ? 'page' : undefined}
  data-shortcut={item.shortcut}
>
  <div class="nav-item-icon" aria-hidden="true">
    <svelte:component this={item.icon} size={20} />
  </div>
  <div class="nav-item-content">
    <span class="nav-item-label">{item.label}</span>
    <span
      id="nav-{sectionType}-{index}-desc"
      class="nav-item-description"
      aria-label="Description: {item.description}"
    >
      {item.description}
    </span>
  </div>
  <kbd class="nav-shortcut" aria-label="Keyboard shortcut {item.shortcut}">
    {item.shortcut}
  </kbd>
  {#if isActive}
    <div class="nav-item-indicator" aria-hidden="true"></div>
  {/if}
</a>

<style>
  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md) var(--spacing-sm);
    border-radius: var(--radius-lg);
    color: var(--color-text-secondary);
    text-decoration: none;
    margin-bottom: var(--spacing-xs);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
  }

  .nav-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity var(--transition-normal);
    z-index: -1;
  }

  .nav-item:hover {
    color: var(--color-text);
    transform: translateX(4px);
    background: rgba(255, 255, 255, 0.05);
  }

  .nav-item.active {
    color: white;
    background: var(--gradient-primary);
    box-shadow: var(--shadow-md);
  }

  .nav-item.active::before {
    opacity: 1;
  }

  .nav-item-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius);
    background: rgba(255, 255, 255, 0.1);
    transition: all var(--transition-normal);
    flex-shrink: 0;
  }

  .nav-item:hover .nav-item-icon {
    background: rgba(255, 255, 255, 0.15);
    transform: scale(1.05);
  }

  .nav-item.active .nav-item-icon {
    background: rgba(255, 255, 255, 0.2);
  }

  .nav-item-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    min-width: 0;
  }

  .nav-item-label {
    font-weight: 500;
    font-size: 0.9rem;
    line-height: 1.2;
  }

  .nav-item-description {
    font-size: 0.75rem;
    opacity: 0.8;
    line-height: 1.2;
  }

  .nav-item-indicator {
    position: absolute;
    right: var(--spacing-sm);
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    animation: pulse 2s infinite;
  }

  .nav-shortcut {
    position: absolute;
    right: var(--spacing-md);
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--spacing-xs);
    padding: 2px 6px;
    font-size: 0.7rem;
    font-family: monospace;
    color: var(--color-text-muted);
    opacity: 0;
    transition: opacity var(--transition-normal);
  }

  .nav-item:hover .nav-shortcut,
  .nav-item:focus .nav-shortcut {
    opacity: 1;
  }

  .nav-item:focus {
    background: var(--color-primary);
    color: white;
    outline: 2px solid rgba(255, 255, 255, 0.5);
    outline-offset: -2px;
  }

  .nav-item:focus .nav-item-description {
    opacity: 1;
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

  @media (prefers-reduced-motion: reduce) {
    .nav-item-indicator {
      animation: none;
    }
  }
</style>
