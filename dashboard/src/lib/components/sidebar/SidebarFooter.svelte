<!-- Sidebar Footer Component -->
<script lang="ts">
  // No specific logic needed for footer
</script>

<div class="sidebar-footer" role="contentinfo">
  <div class="version">
    <p class="version-text" aria-label="WakeDock version 1.0.0">WakeDock v1.0.0</p>
    <p class="build-info" aria-label="Build version 2024.1.1">Build 2024.1.1</p>
  </div>
</div>

<style>
  .sidebar-footer {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--color-border-light);
    background: rgba(255, 255, 255, 0.02);
  }

  .version {
    text-align: center;
  }

  .version-text {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text-muted);
    margin: 0 0 var(--spacing-xs) 0;
  }

  .build-info {
    font-size: 0.7rem;
    color: var(--color-text-muted);
    opacity: 0.7;
    margin: 0;
    font-family: monospace;
  }
</style>
