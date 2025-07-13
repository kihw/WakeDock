<script lang="ts">
  import { themeManager, isDarkMode, currentThemeMode, currentVariant } from '$lib/design-system/theme-manager';
  import { variants } from '$lib/design-system/tokens';
  import type { ThemeMode, ThemeVariant } from '$lib/design-system/theme-manager';

  export let showVariants: boolean = true;
  export let compact: boolean = false;

  const modeOptions: { value: ThemeMode; label: string; icon: string }[] = [
    { value: 'light', label: 'Light', icon: '☀️' },
    { value: 'dark', label: 'Dark', icon: '🌙' },
    { value: 'auto', label: 'Auto', icon: '🔄' }
  ];

  const variantOptions: { value: ThemeVariant; label: string }[] = [
    { value: 'default', label: 'Default' },
    { value: 'compact', label: 'Compact' },
    { value: 'comfortable', label: 'Comfortable' }
  ];

  function handleModeChange(mode: ThemeMode) {
    themeManager.setMode(mode);
  }

  function handleVariantChange(variant: ThemeVariant) {
    themeManager.setVariant(variant);
  }

  function toggleMode() {
    themeManager.toggleMode();
  }
</script>

<div class="theme-switcher" class:compact>
  {#if compact}
    <!-- Compact mode: Just a toggle button -->
    <button
      type="button"
      on:click={toggleMode}
      class="{variants.button.ghost} theme-toggle-btn"
      title="Toggle theme"
      aria-label="Toggle between light and dark mode"
    >
      {$isDarkMode ? '🌙' : '☀️'}
    </button>
  {:else}
    <!-- Full theme switcher -->
    <div class="theme-section">
      <h3 class="section-title">Theme Mode</h3>
      <div class="mode-options">
        {#each modeOptions as option}
          <button
            type="button"
            on:click={() => handleModeChange(option.value)}
            class="mode-option {$currentThemeMode === option.value ? 'active' : ''}"
            aria-pressed={$currentThemeMode === option.value}
          >
            <span class="mode-icon">{option.icon}</span>
            <span class="mode-label">{option.label}</span>
          </button>
        {/each}
      </div>
    </div>

    {#if showVariants}
      <div class="theme-section">
        <h3 class="section-title">Theme Variant</h3>
        <div class="variant-options">
          {#each variantOptions as option}
            <button
              type="button"
              on:click={() => handleVariantChange(option.value)}
              class="variant-option {$currentVariant === option.value ? 'active' : ''}"
              aria-pressed={$currentVariant === option.value}
            >
              {option.label}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Theme actions -->
    <div class="theme-actions">
      <button
        type="button"
        on:click={() => themeManager.reset()}
        class="{variants.button.secondary} text-sm"
      >
        Reset to Default
      </button>
    </div>
  {/if}
</div>

<style>
  .theme-switcher {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
  }

  .theme-switcher.compact {
    padding: 0;
    background: none;
    border: none;
    gap: 0;
  }

  .theme-toggle-btn {
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    border-radius: 0.375rem;
    transition: all 0.2s ease;
  }

  .theme-toggle-btn:hover {
    background-color: var(--color-hover);
    transform: scale(1.05);
  }

  .theme-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .section-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
  }

  .mode-options {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .mode-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--color-border);
    background: var(--color-bg-primary);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .mode-option:hover {
    background: var(--color-hover);
    border-color: var(--color-primary);
  }

  .mode-option.active {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .mode-icon {
    font-size: 1rem;
  }

  .mode-label {
    font-weight: 500;
  }

  .variant-options {
    display: flex;
    gap: 0.25rem;
    background: var(--color-bg-secondary);
    padding: 0.25rem;
    border-radius: 0.5rem;
  }

  .variant-option {
    flex: 1;
    padding: 0.5rem 1rem;
    border: none;
    background: transparent;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .variant-option:hover {
    background: var(--color-hover);
    color: var(--color-text-primary);
  }

  .variant-option.active {
    background: var(--color-primary);
    color: white;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .theme-actions {
    padding-top: 0.5rem;
    border-top: 1px solid var(--color-border-light);
    display: flex;
    justify-content: center;
  }

  /* Dark mode adjustments */
  :global(.dark) .theme-switcher {
    background: var(--color-bg-tertiary);
    border-color: var(--color-border-dark);
  }

  :global(.dark) .mode-option {
    background: var(--color-bg-tertiary);
    border-color: var(--color-border-dark);
    color: var(--color-text-primary);
  }

  :global(.dark) .variant-options {
    background: var(--color-bg-primary);
  }

  :global(.dark) .theme-actions {
    border-color: var(--color-border-dark);
  }
</style>