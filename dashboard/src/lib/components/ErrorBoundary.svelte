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
    type ErrorInfo 
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
        url: typeof window !== 'undefined' ? window.location.href : undefined
      });
    }

    // Show notification
    notifications.show({
      type: 'error',
      title: 'An error occurred',
      message: getUserFriendlyMessage(errorInfo || { error: errorObj, level: 'error', source: boundaryId, id: '', timestamp: new Date() }),
      persistent: true,
      actions: canRetry ? [
        {
          label: 'Retry',
          action: () => handleRetry()
        }
      ] : []
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

    const reportData = {
      error: {
        name: errorInfo.error.name,
        message: errorInfo.error.message,
        stack: errorInfo.error.stack
      },
      boundary: boundaryId,
      timestamp: errorInfo.timestamp,
      url: errorInfo.url,
      userAgent: errorInfo.userAgent,
      retryCount,
      additionalInfo: prompt('Please describe what you were doing when the error occurred (optional):')
    };

    // Send report (implement your reporting logic here)
    logger.info('Error report', reportData);
    
    notifications.show({
      type: 'success',
      title: 'Error Report Sent',
      message: 'Thank you for reporting this error. We will investigate and fix it.',
      duration: 5000
    });
  }
      } catch (callbackError) {
        logger.error('Error in onError callback', callbackError);
      }
    }

    // Report to monitoring
    if (reportErrors) {
      errorId = monitoring.reportError(errorObj, context, 'high');
    }

    // Show notification
    notifications.error('Une erreur est survenue', errorObj.message, {
      persistent: true,
      actions: [
        {
          label: 'Recharger',
          action: () => window.location.reload(),
          style: 'primary',
        },
        {
          label: 'Signaler',
          action: () => reportError(),
          style: 'secondary',
        },
      ],
    });
  }

  function reportError() {
    if (!error || !errorId) return;

    // Ouvrir un modal de rapport d'erreur ou rediriger vers un formulaire
    const subject = encodeURIComponent(`Erreur WakeDock: ${error.message}`);
    const body = encodeURIComponent(`
ID d'erreur: ${errorId}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}
Timestamp: ${new Date().toISOString()}

Détails:
${error.stack || error.message}

Informations supplémentaires:
${JSON.stringify(errorInfo, null, 2)}
		`);

    window.open(`mailto:support@wakedock.com?subject=${subject}&body=${body}`, '_blank');
  }

  function retry() {
    hasError = false;
    error = null;
    errorInfo = null;
    errorId = null;
  }

  // Lifecycle
  onMount(() => {
    // Écouter les erreurs JavaScript non capturées
    window.addEventListener('error', handleError);

    // Écouter les promesses rejetées non capturées
    window.addEventListener('unhandledrejection', handleError);
  });

  onDestroy(() => {
    window.removeEventListener('error', handleError);
    window.removeEventListener('unhandledrejection', handleError);
  });

  // Helper pour formater la stack trace
  function formatStackTrace(stack: string): string[] {
    return stack
      .split('\n')
      .filter((line) => line.trim())
      .slice(0, 10); // Limiter à 10 lignes
  }
</script>

{#if hasError && fallback}
  <div class="error-boundary">
    <div class="error-container">
      <div class="error-icon">
        <Icon name="alert-triangle" size="48" color="currentColor" />
      </div>

      <div class="error-content">
        <h2 class="error-title">Oups ! Quelque chose s'est mal passé</h2>

        <p class="error-message">
          Une erreur inattendue s'est produite. L'équipe technique a été automatiquement notifiée.
        </p>

        {#if error}
          <div class="error-technical">
            <strong>Erreur:</strong>
            {error.message}
            {#if errorId}
              <br /><strong>ID:</strong> <code>{errorId}</code>
            {/if}
          </div>
        {/if}

        {#if showDetails && error?.stack}
          <details class="error-details">
            <summary>Détails techniques</summary>
            <pre class="error-stack">
							{#each formatStackTrace(error.stack) as line}
                <div>{line}</div>
              {/each}
						</pre>

            {#if errorInfo}
              <div class="error-context">
                <strong>Contexte:</strong>
                <pre>{JSON.stringify(errorInfo, null, 2)}</pre>
              </div>
            {/if}
          </details>
        {/if}

        <div class="error-actions">
          {#if showRetry}
            <button class="btn btn-primary" on:click={retry}>
              <Icon name="refresh-cw" size="16" />
              Réessayer
            </button>
          {/if}

          <button class="btn btn-secondary" on:click={() => window.location.reload()}>
            <Icon name="refresh-ccw" size="16" />
            Recharger la page
          </button>

          {#if showReport}
            <button class="btn btn-outline" on:click={reportError}>
              <Icon name="mail" size="16" />
              Signaler le problème
            </button>
          {/if}
        </div>
      </div>
    </div>
  </div>
{:else if !hasError}
  <slot />
{/if}

<style>
  .error-boundary {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    padding: 2rem;
    background: var(--color-background);
  }

  .error-container {
    max-width: 600px;
    text-align: center;
    background: var(--color-surface);
    border-radius: 12px;
    padding: 3rem;
    box-shadow: var(--shadow-lg);
    border: 1px solid var(--color-border);
  }

  .error-icon {
    color: var(--color-error);
    margin-bottom: 1.5rem;
  }

  .error-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0 0 1rem 0;
  }

  .error-message {
    color: var(--color-text-secondary);
    margin: 0 0 1.5rem 0;
    line-height: 1.6;
  }

  .error-technical {
    background: var(--color-error-light);
    border: 1px solid var(--color-error);
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: left;
    font-size: 0.875rem;
  }

  .error-technical code {
    background: var(--color-background);
    padding: 2px 4px;
    border-radius: 3px;
    font-family: var(--font-mono);
  }

  .error-details {
    text-align: left;
    margin: 1.5rem 0;
    border: 1px solid var(--color-border);
    border-radius: 6px;
  }

  .error-details summary {
    padding: 0.75rem;
    background: var(--color-background);
    cursor: pointer;
    font-weight: 500;
    border-radius: 6px 6px 0 0;
  }

  .error-details summary:hover {
    background: var(--color-surface-hover);
  }

  .error-stack {
    background: var(--color-background);
    padding: 1rem;
    margin: 0;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    line-height: 1.4;
    overflow-x: auto;
    border-top: 1px solid var(--color-border);
  }

  .error-context {
    padding: 1rem;
    border-top: 1px solid var(--color-border);
  }

  .error-context pre {
    background: var(--color-background);
    padding: 0.75rem;
    border-radius: 3px;
    margin: 0.5rem 0 0 0;
    font-size: 0.75rem;
    overflow-x: auto;
  }

  .error-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 2rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-weight: 500;
    text-decoration: none;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.875rem;
  }

  .btn-primary {
    background: var(--color-primary);
    color: var(--color-primary-contrast);
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
  }

  .btn-secondary {
    background: var(--color-secondary);
    color: var(--color-secondary-contrast);
  }

  .btn-secondary:hover {
    background: var(--color-secondary-hover);
  }

  .btn-outline {
    background: transparent;
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
  }

  .btn-outline:hover {
    background: var(--color-surface-hover);
    border-color: var(--color-primary);
  }

  @media (max-width: 640px) {
    .error-boundary {
      padding: 1rem;
    }

    .error-container {
      padding: 2rem 1.5rem;
    }

    .error-actions {
      flex-direction: column;
    }

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>
