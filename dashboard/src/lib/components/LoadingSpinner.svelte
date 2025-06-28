<script lang="ts">
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let color: string = 'var(--color-primary)';
  export let text: string = '';
  export let center: boolean = false;
  export let className: string = '';

  // Size mappings
  const sizeClasses = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large',
  };

  const textSizes = {
    small: '0.8rem',
    medium: '0.9rem',
    large: '1.1rem',
  };
</script>

<div class="spinner-container {sizeClasses[size]} {className}" class:center>
  <div class="spinner" style="border-top-color: {color}">
    <div class="spinner-inner"></div>
  </div>
  {#if text}
    <p class="spinner-text" style="font-size: {textSizes[size]}">{text}</p>
  {/if}
</div>

<style>
  .spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .spinner-container.center {
    justify-content: center;
    min-height: 200px;
  }

  .spinner {
    position: relative;
    border: 2px solid var(--color-border);
    border-top: 2px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .spinner-inner {
    position: absolute;
    top: 2px;
    left: 2px;
    right: 2px;
    bottom: 2px;
    border: 1px solid transparent;
    border-top: 1px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite reverse;
    opacity: 0.6;
  }

  .spinner-small .spinner {
    width: 16px;
    height: 16px;
    border-width: 1px;
  }

  .spinner-small .spinner-inner {
    border-width: 0.5px;
    top: 1px;
    left: 1px;
    right: 1px;
    bottom: 1px;
  }

  .spinner-medium .spinner {
    width: 24px;
    height: 24px;
  }

  .spinner-large .spinner {
    width: 40px;
    height: 40px;
    border-width: 3px;
  }

  .spinner-large .spinner-inner {
    border-width: 1.5px;
    top: 3px;
    left: 3px;
    right: 3px;
    bottom: 3px;
  }

  .spinner-text {
    margin: 0;
    color: var(--color-text-secondary);
    font-weight: 500;
    text-align: center;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  /* Pulse variant for different loading states */
  .spinner-container.pulse .spinner {
    animation: pulse 1.5s ease-in-out infinite;
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

  /* Dots variant */
  .spinner-container.dots .spinner {
    display: none;
  }

  .spinner-container.dots::after {
    content: '';
    display: inline-block;
    width: 40px;
    height: 10px;
    background: linear-gradient(
      90deg,
      var(--color-primary) 0%,
      var(--color-primary) 25%,
      transparent 25%,
      transparent 75%,
      var(--color-primary) 75%
    );
    background-size: 10px 10px;
    animation: dots 1.2s infinite linear;
  }

  @keyframes dots {
    0% {
      background-position: 0 0;
    }
    100% {
      background-position: 40px 0;
    }
  }
</style>
