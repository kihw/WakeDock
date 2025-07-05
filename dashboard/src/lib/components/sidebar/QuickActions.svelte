<!-- Quick Actions Section -->
<script lang="ts">
  import { Zap } from 'lucide-svelte';

  export let onQuickDeploy: () => void = () => {};
</script>

<div class="quick-actions" role="group" aria-label="Quick actions">
  <button
    class="quick-action primary"
    on:click={onQuickDeploy}
    aria-label="Deploy new service quickly"
    title="Deploy new service"
    type="button"
  >
    <Zap size={16} aria-hidden="true" />
    <span>Quick Deploy</span>
  </button>
</div>

<style>
  .quick-actions {
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-light);
  }

  .quick-action {
    width: 100%;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    border-radius: var(--radius);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-normal);
    background: var(--gradient-primary);
    color: white;
    box-shadow: var(--shadow-sm);
  }

  .quick-action:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  :global(.keyboard-navigation) .quick-action:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
</style>
