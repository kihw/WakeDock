<!--
  Enhanced ErrorBoundary Component
  Advanced error boundary with recovery, retry, and detailed reporting
-->
<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { logger } from '../utils/logger';
  import { notifications } from '../services/notifications';
  import { monitoring } from '../services/monitoring';
  import {
    getErrorBoundary,
    captureError,
    retryFromError,
    clearError,
    getUserFriendlyMessage,
    type ErrorInfo,
  } from '../utils/errorHandling';
  import Icon from './Icon.svelte';
  import LoadingSpinner from './LoadingSpinner.svelte';

  // Props
  export let fallback: boolean = true;
  export let showDetails: boolean = false;
  export let reportErrors: boolean = true;
  export let showRetry: boolean = true;
  export let showReport: boolean = true;
  export let boundaryId: string = `boundary_${Math.random().toString(36).substr(2, 9)}`;
  export let maxRetries: number = 3;
  export let customFallback: string = '';
  export let autoRecover: boolean = false;
  export let autoRecoverDelay: number = 5000;
  export let onError: ((error: Error, context?: any) => void) | undefined = undefined;

  const dispatch = createEventDispatcher();

  // Error boundary state
  $: boundaryStore = getErrorBoundary(boundaryId);
  $: boundaryState = $boundaryStore;
  $: hasError = boundaryState.hasError;
  $: errorInfo = boundaryState.error;
  $: canRetry = boundaryState.canRetry;
  $: retryCount = boundaryState.retryCount;

  // Recovery state
  let isRecovering = false;
  let autoRecoverTimer: number | null = null;
  let showDetailedError = false;
  let errorId: string | null = null;

  // Error handling
  function handleError(err: ErrorEvent | PromiseRejectionEvent | Error, context?: any) {
    let errorObj: Error;

    if (err instanceof Error) {
      errorObj = err;
    } else if ('error' in err) {
      errorObj = err.error || new Error(err.message || 'Unknown error');
    } else if ('reason' in err) {
      errorObj = err.reason instanceof Error ? err.reason : new Error(String(err.reason));
    } else {
      errorObj = new Error('Unknown error occurred');
    }

    // Capture error in boundary
    captureError(boundaryId, errorObj, context);

    // Call onError callback if provided
    if (onError) {
      try {
        onError(errorObj, context);
      } catch (callbackError) {
        logger.error('Error in onError callback', callbackError);
      }
    }

    // Dispatch error event
    dispatch('error', { error: errorObj, context });

    // Log error
    logger.error('Error caught by ErrorBoundary', errorObj, context);

    // Report to monitoring if enabled
    if (reportErrors) {
      monitoring.reportError(errorObj, {
        boundary: boundaryId,
        context,
        retryCount,
        userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined,
        url: typeof window !== 'undefined' ? window.location.href : undefined,
      });
    }

    // Show notification
    notifications.show({
      type: 'error',
      title: 'An error occurred',
      message: getUserFriendlyMessage(
        errorInfo || {
          error: errorObj,
          level: 'error',
          source: boundaryId,
          id: '',
          timestamp: new Date(),
        }
      ),
      persistent: true,
      actions: canRetry
        ? [
            {
              label: 'Retry',
              action: () => handleRetry(),
            },
          ]
        : [],
    });

    // Auto-recover if enabled
    if (autoRecover && !autoRecoverTimer) {
      autoRecoverTimer = setTimeout(() => {
        handleRetry();
      }, autoRecoverDelay);
    }
  }

  // Retry handler
  function handleRetry() {
    if (autoRecoverTimer) {
      clearTimeout(autoRecoverTimer);
      autoRecoverTimer = null;
    }

    isRecovering = true;

    setTimeout(() => {
      retryFromError(boundaryId);
      isRecovering = false;
      dispatch('retry', { retryCount: retryCount + 1 });
    }, 100);
  }

  // Clear error handler
  function handleClearError() {
    if (autoRecoverTimer) {
      clearTimeout(autoRecoverTimer);
      autoRecoverTimer = null;
    }

    clearError(boundaryId);
    showDetailedError = false;
    dispatch('recover');
  }

  // Report error handler
  function handleReportError() {
    if (!errorInfo) return;

    try {
      const reportData = {
        error: {
          name: errorInfo.error.name,
          message: errorInfo.error.message,
          stack: errorInfo.error.stack,
        },
        boundary: boundaryId,
        timestamp: errorInfo.timestamp,
        url: errorInfo.url,
        userAgent: errorInfo.userAgent,
        retryCount,
        additionalInfo: prompt(
          'Please describe what you were doing when the error occurred (optional):'
        ),
      };

      // Send report (implement your reporting logic here)
      logger.info('Error report', reportData);

      notifications.show({
        type: 'success',
        title: 'Error Report Sent',
        message: 'Thank you for reporting this error. We will investigate and fix it.',
        duration: 5000,
      });

      // Generate an error ID for tracking
      errorId = `ERR_${Date.now().toString(36)}_${Math.random().toString(36).substr(2, 5)}`;
    } catch (callbackError) {
      logger.error('Error in error reporting', callbackError);
    }
  }

  function reportError() {
    if (!errorInfo || !errorId) return;

    // Ouvrir un modal de rapport d'erreur ou rediriger vers un formulaire
    const subject = encodeURIComponent(`Erreur WakeDock: ${errorInfo.error.message}`);
    const body = encodeURIComponent(`
ID d'erreur: ${errorId}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}
Timestamp: ${new Date().toISOString()}

Détails:
${errorInfo.error.stack || errorInfo.error.message}

Informations supplémentaires:
${JSON.stringify(errorInfo, null, 2)}
    `);

    window.open(`mailto:support@wakedock.com?subject=${subject}&body=${body}`, '_blank');
  }

  function retry() {
    hasError = false;
    errorId = null;
    handleRetry();
  }

  // Lifecycle
  onMount(() => {
    // Listen for global errors
    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleError);
  });

  onDestroy(() => {
    // Clean up
    window.removeEventListener('error', handleError);
    window.removeEventListener('unhandledrejection', handleError);

    if (autoRecoverTimer) {
      clearTimeout(autoRecoverTimer);
      autoRecoverTimer = null;
    }
  });
</script>

{#if hasError && fallback}
  <div class="error-boundary {isRecovering ? 'recovering' : ''}" data-testid="error-boundary">
    <div class="error-content">
      {#if isRecovering}
        <div class="recovering-indicator">
          <LoadingSpinner size="medium" />
          <p>Recovering...</p>
        </div>
      {:else if customFallback}
        {@html customFallback}
      {:else}
        <div class="error-header">
          <Icon name="alert-circle" size={24} />
          <h2>Something went wrong</h2>
        </div>

        <div class="error-message">
          <p>{getUserFriendlyMessage(errorInfo)}</p>
        </div>

        {#if showDetails && errorInfo}
          <div class="error-details">
            <button
              class="toggle-details"
              on:click={() => (showDetailedError = !showDetailedError)}
              aria-expanded={showDetailedError}
            >
              {showDetailedError ? 'Hide' : 'Show'} technical details
            </button>

            {#if showDetailedError}
              <div class="details-content">
                <pre>{errorInfo.error.stack || errorInfo.error.message}</pre>
                <p><strong>Error ID:</strong> {errorId || 'Not available'}</p>
                <p><strong>Time:</strong> {errorInfo.timestamp.toLocaleString()}</p>
              </div>
            {/if}
          </div>
        {/if}

        <div class="actions">
          {#if showRetry && canRetry && retryCount < maxRetries}
            <button class="retry-button" on:click={handleRetry} disabled={isRecovering}>
              <Icon name="refresh-cw" size={16} />
              Try again ({maxRetries - retryCount} attempts left)
            </button>
          {/if}

          <button class="clear-button" on:click={handleClearError} disabled={isRecovering}>
            <Icon name="x" size={16} />
            Dismiss
          </button>

          {#if showReport}
            <button class="report-button" on:click={handleReportError} disabled={isRecovering}>
              <Icon name="flag" size={16} />
              Report this issue
            </button>
          {/if}
        </div>
      {/if}
    </div>
  </div>
{:else}
  <slot />
{/if}

<style>
  .error-boundary {
    background-color: var(--color-error-bg, #fff1f0);
    border: 1px solid var(--color-error-border, #ffccc7);
    border-radius: 4px;
    padding: 1.5rem;
    margin: 1rem 0;
    max-width: 100%;
    overflow: hidden;
    position: relative;
  }

  .error-boundary.recovering {
    opacity: 0.7;
    pointer-events: none;
  }

  .error-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: var(--color-error, #f5222d);
  }

  .error-message {
    margin-bottom: 1rem;
    font-size: 1rem;
    line-height: 1.5;
  }

  .error-details {
    margin: 1rem 0;
  }

  .toggle-details {
    background: none;
    border: none;
    color: var(--color-link, #1890ff);
    cursor: pointer;
    padding: 0;
    font-size: 0.875rem;
    text-decoration: underline;
  }

  .details-content {
    background-color: var(--color-code-bg, #f5f5f5);
    border-radius: 4px;
    padding: 1rem;
    margin-top: 0.5rem;
    font-family: monospace;
    font-size: 0.875rem;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 300px;
    overflow: auto;
  }

  .actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
    flex-wrap: wrap;
  }

  button {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
    transition:
      background-color 0.2s,
      color 0.2s;
  }

  .retry-button {
    background-color: var(--color-primary, #1890ff);
    color: white;
    border: none;
  }

  .retry-button:hover {
    background-color: var(--color-primary-dark, #096dd9);
  }

  .clear-button {
    background-color: transparent;
    color: var(--color-text, #333);
    border: 1px solid var(--color-border, #d9d9d9);
  }

  .clear-button:hover {
    background-color: var(--color-bg-hover, #f5f5f5);
  }

  .report-button {
    background-color: transparent;
    color: var(--color-warning, #faad14);
    border: 1px solid var(--color-warning-border, #ffe58f);
  }

  .report-button:hover {
    background-color: var(--color-warning-bg, #fffbe6);
  }

  .recovering-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
  }
</style>
