<!-- Sidebar Header with Logo and Close Button -->
<script lang="ts">
  import { Container, X } from 'lucide-svelte';
  import { announceToScreenReader } from '$lib/utils/accessibility';

  export let onClose: () => void;

  function handleClose() {
    onClose();
    announceToScreenReader('Sidebar closed');
  }
</script>

<div class="sidebar-header">
  <div class="logo">
    <div class="logo-icon" role="img" aria-label="WakeDock logo">
      <Container size={28} />
    </div>
    <div class="logo-text">
      <span class="logo-name">WakeDock</span>
      <span class="logo-tagline">Docker Manager</span>
    </div>
  </div>
  <button
    class="close-btn"
    on:click={handleClose}
    aria-label="Close sidebar navigation"
    type="button"
  >
    <X size={20} />
  </button>
</div>

<style>
  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-light);
    background: rgba(255, 255, 255, 0.05);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .logo-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-lg);
    background: var(--gradient-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: var(--shadow-md);
  }

  .logo-text {
    display: flex;
    flex-direction: column;
  }

  .logo-name {
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--color-text);
    line-height: 1.2;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .logo-tagline {
    font-size: 0.75rem;
    color: var(--color-text-muted);
    line-height: 1.2;
  }

  .close-btn {
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    padding: var(--spacing-xs);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-normal);
  }

  .close-btn:hover {
    background: var(--color-surface-hover);
    color: var(--color-text);
    transform: scale(1.1);
  }

  :global(.keyboard-navigation) .close-btn:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
</style>
