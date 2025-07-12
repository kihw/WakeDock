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
  import LoadingSpinner from './ui/atoms/LoadingSpinner.svelte';

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
        logger.error('Error in onError callback', callbackError as Error);
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
    notifications.error(
      'An error occurred',
      getUserFriendlyMessage(
        errorInfo || {
          error: errorObj,
          level: 'error',
          source: boundaryId,
          id: '',
          timestamp: new Date(),
        }
      )
    );

    // Auto-recover if enabled
    if (autoRecover && !autoRecoverTimer) {
      autoRecoverTimer = window.setTimeout(() => {
        handleRetry();
      }, autoRecoverDelay) as unknown as number;
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

      notifications.success(
        'Error Report Sent',
        'Thank you for reporting this error. We will investigate and fix it.'
      );

      // Generate an error ID for tracking
      errorId = `ERR_${Date.now().toString(36)}_${Math.random().toString(36).substr(2, 5)}`;
    } catch (callbackError) {
      logger.error('Error in error reporting', callbackError as Error);
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
Message: ${errorInfo.error.message}
Stack: ${errorInfo.error.stack || 'Non disponible'}
    `);

    window.open(`mailto:support@wakedock.com?subject=${subject}&body=${body}`);
  }

  // Cleanup on destroy
  onDestroy(() => {
    if (autoRecoverTimer) {
      clearTimeout(autoRecoverTimer);
      autoRecoverTimer = null;
    }
  });

  // Setup error handlers
  onMount(() => {
    const handleGlobalError = (event: ErrorEvent) => {
      // Only handle errors for this boundary's children
      if (event.defaultPrevented) return;

      const targetElement = event.target as Node;
      const boundaryElement = document.getElementById(boundaryId);

      if (boundaryElement && boundaryElement.contains(targetElement)) {
        event.preventDefault();
        handleError(event);
      }
    };

    const handleRejection = (event: PromiseRejectionEvent) => {
      // For promise rejections, we can't easily determine if they belong to this boundary
      // So we'll handle all unhandled rejections globally
      handleError(event);
    };

    // Add global error handlers
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleRejection);

    return () => {
      window.removeEventListener('error', handleGlobalError);
      window.removeEventListener('unhandledrejection', handleRejection);
    };
  });
</script>

<!-- Error Boundary UI -->
{#if hasError}
  {#if fallback}
    <div
      class="error-boundary {$$restProps.class || ''}"
      role="alert"
      aria-live="assertive"
      id={boundaryId}
    >
      {#if customFallback}
        {@html customFallback}
      {:else}
        <div class="error-container">
          <div class="error-icon">
            <Icon name="alert-triangle" size="xl" />
          </div>

          <div class="error-content">
            <h3 class="error-title">An error occurred</h3>

            <p class="error-message">
              {errorInfo ? getUserFriendlyMessage(errorInfo) : 'An unexpected error occurred'}
            </p>

            {#if errorId}
              <p class="error-id">
                Error ID: <code>{errorId}</code>
              </p>
            {/if}

            <div class="error-actions">
              {#if showRetry && canRetry && retryCount < maxRetries}
                <button
                  type="button"
                  class="retry-button"
                  on:click={handleRetry}
                  disabled={isRecovering}
                >
                  {#if isRecovering}
                    <LoadingSpinner size="small" />
                    <span>Retrying...</span>
                  {:else}
                    <Icon name="refresh-cw" />
                    <span>Retry</span>
                  {/if}
                </button>
              {/if}

              <button type="button" class="clear-button" on:click={handleClearError}>
                <Icon name="x" />
                <span>Dismiss</span>
              </button>

              {#if showReport}
                <button type="button" class="report-button" on:click={handleReportError}>
                  <Icon name="flag" />
                  <span>Report</span>
                </button>
              {/if}

              {#if showDetails}
                <button
                  type="button"
                  class="details-button"
                  on:click={() => (showDetailedError = !showDetailedError)}
                  aria-expanded={showDetailedError ? 'true' : 'false'}
                >
                  <Icon name={showDetailedError ? 'chevron-up' : 'chevron-down'} />
                  <span>{showDetailedError ? 'Hide' : 'Show'} Details</span>
                </button>
              {/if}
            </div>

            {#if showDetailedError && errorInfo}
              <div class="error-details">
                <h4>Error Details</h4>
                <p><strong>Name:</strong> {errorInfo.error.name}</p>
                <p><strong>Message:</strong> {errorInfo.error.message}</p>
                <p><strong>Time:</strong> {new Date(errorInfo.timestamp).toLocaleString()}</p>

                {#if errorInfo.error.stack}
                  <details>
                    <summary>Stack Trace</summary>
                    <pre>{errorInfo.error.stack}</pre>
                  </details>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>
  {/if}
{:else}
  <slot />
{/if}

<style>
  .error-boundary {
    padding: 1rem;
    border: 1px solid #e53e3e;
    border-radius: 0.375rem;
    background-color: #fff5f5;
    color: #c53030;
    margin: 1rem 0;
    width: 100%;
  }

  .error-container {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
  }

  .error-icon {
    flex-shrink: 0;
    color: #e53e3e;
  }

  .error-content {
    flex-grow: 1;
  }

  .error-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-top: 0;
    margin-bottom: 0.5rem;
  }

  .error-message {
    margin-bottom: 1rem;
  }

  .error-id {
    font-size: 0.875rem;
    color: #4a5568;
    margin-bottom: 1rem;
  }

  .error-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  button {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem 0.75rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .retry-button {
    background-color: #3182ce;
    color: white;
    border: none;
  }

  .retry-button:hover {
    background-color: #2c5282;
  }

  .retry-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .clear-button {
    background-color: transparent;
    color: #4a5568;
    border: 1px solid #e2e8f0;
  }

  .clear-button:hover {
    background-color: #f7fafc;
  }

  .report-button {
    background-color: #4a5568;
    color: white;
    border: none;
  }

  .report-button:hover {
    background-color: #2d3748;
  }

  .details-button {
    background-color: transparent;
    color: #4a5568;
    border: 1px solid #e2e8f0;
  }

  .details-button:hover {
    background-color: #f7fafc;
  }

  .error-details {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #f7fafc;
    border-radius: 0.25rem;
    font-size: 0.875rem;
  }

  .error-details h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    font-size: 1rem;
  }

  pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    background-color: #edf2f7;
    padding: 0.5rem;
    border-radius: 0.25rem;
    overflow-x: auto;
    font-size: 0.75rem;
    max-height: 300px;
    overflow-y: auto;
  }
</style>
