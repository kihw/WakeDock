<!-- Refactored Login Page -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { auth, isAuthenticated } from '$lib/stores/auth';
  import { csrf, rateLimit } from '$lib/utils/validation';
  import { setupGlobalErrorHandling, safeSanitizeInput, safeEmailValidation } from '$lib/utils/errorHandling';
  import { secureAccessibility } from '$lib/utils/accessibility';
  import { debugConfig } from '$lib/config/environment';
  import LoginForm from '$lib/components/auth/login/LoginForm.svelte';

  // Login state
  let loading = false;
  let error = '';
  let csrfToken = '';
  let attemptCount = 0;
  let rateLimited = false;
  let loginFormRef;

  // Cleanup functions
  let unsubscribeAuth;
  let cleanupErrorHandling;

  // Security and accessibility setup
  onMount(async () => {
    // Debug configuration
    debugConfig();

    // Generate CSRF token
    try {
      csrfToken = csrf.generateToken();
      csrf.storeToken(csrfToken);
    } catch (err) {
      console.debug('CSRF token generation fallback:', err);
      csrfToken = crypto.randomUUID(); // Fallback
    }

    // Check existing authentication
    unsubscribeAuth = isAuthenticated.subscribe((authenticated) => {
      if (authenticated) {
        const redirectTo = $page.url.searchParams.get('redirect') || '/';
        goto(redirectTo);
      }
    });

    // Setup error handling
    cleanupErrorHandling = setupGlobalErrorHandling();
  });

  onDestroy(() => {
    // Cleanup subscriptions
    if (unsubscribeAuth) unsubscribeAuth();
    if (cleanupErrorHandling) cleanupErrorHandling();
  });

  // Field validation functions
  function validateField(field, value) {
    const errors = [];

    switch (field) {
      case 'usernameOrEmail':
        const sanitized = safeSanitizeInput(value);
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isEmail = emailRegex.test(sanitized);

        if (!sanitized) {
          errors.push('Username or email is required');
        } else if (isEmail) {
          try {
            const validation = safeEmailValidation(sanitized);
            if (!validation.valid) {
              errors.push(validation.message || 'Invalid email format');
            }
          } catch (err) {
            errors.push('Invalid email format');
          }
        } else {
          // Username validation
          if (sanitized.length < 3) {
            errors.push('Username must be at least 3 characters');
          } else if (!/^[a-zA-Z0-9_-]+$/.test(sanitized)) {
            errors.push('Username can only contain letters, numbers, underscores, and hyphens');
          }
        }
        break;

      case 'password':
        if (!value) {
          errors.push('Password is required');
        } else if (value.length < 3) {
          errors.push('Password is too short');
        }
        break;

    }

    return errors;
  }

  // Rate limiting check
  function checkRateLimit(usernameOrEmail) {
    const rateLimitKey = `login_attempt_${usernameOrEmail}`;
    rateLimited = rateLimit.isLimited(rateLimitKey, 10, 5 * 60 * 1000);
    
    if (rateLimited) {
      error = 'Too many login attempts. Please try again in 5 minutes.';
      secureAccessibility.form.announceError('Rate limit exceeded');
      return false;
    }
    
    return true;
  }

  // Generate device fingerprint
  async function generateFingerprint() {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 2, 2);
        return canvas.toDataURL();
      }
    } catch (err) {
      console.debug('Canvas fingerprint failed:', err);
    }
    
    // Fallback fingerprint
    return `${navigator.userAgent}-${screen.width}x${screen.height}-${new Date().getTimezoneOffset()}`;
  }

  // Handle form submission
  async function handleSubmit(event) {
    const { usernameOrEmail, password } = event.detail;

    // Reset state
    error = '';
    loading = true;

    // Validate fields
    const usernameErrors = validateField('usernameOrEmail', usernameOrEmail);
    const passwordErrors = validateField('password', password);

    if (usernameErrors.length > 0 || passwordErrors.length > 0) {
      error = 'Please correct the errors above';
      loading = false;
      return;
    }

    // Check rate limiting
    if (!checkRateLimit(usernameOrEmail)) {
      loading = false;
      return;
    }

    // Validate CSRF token
    const isCSRFValid = csrf.validateToken(csrfToken);
    if (!isCSRFValid) {
      error = 'Security token validation failed. Please refresh the page.';
      loading = false;
      return;
    }

    try {
      attemptCount++;
      
      const result = await auth.login(usernameOrEmail, password);

      // Success - redirect
      secureAccessibility.form.announceChange('Login successful. Redirecting...');
      const redirectTo = $page.url.searchParams.get('redirect') || '/';
      goto(redirectTo);

    } catch (err) {
      console.error('Login error:', err);
      error = err instanceof Error ? err.message : 'Login failed. Please check your credentials.';
      
      secureAccessibility.form.announceError(error);
      
      // Clear sensitive data on error
      if (loginFormRef) {
        loginFormRef.clearSensitiveData();
      }
    } finally {
      loading = false;
    }
  }

  // Handle field validation
  function handleFieldValidation(event) {
    const { field, value } = event.detail;
    const errors = validateField(field, value);
    
    // Update form errors (this would be handled by the form component)
    if (errors.length > 0) {
      console.debug(`Validation errors for ${field}:`, errors);
    }
  }

  // Handle rate limiting
  function handleRateLimit(event) {
    attemptCount = event.detail.attempts;
  }
</script>

<svelte:head>
  <title>Sign In - WakeDock</title>
  <meta name="description" content="Sign in to your WakeDock account to manage your containers and services." />
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<LoginForm
  bind:this={loginFormRef}
  {loading}
  {error}
  {csrfToken}
  {rateLimited}
  {attemptCount}
  on:submit={handleSubmit}
  on:validateField={handleFieldValidation}
  on:rateLimit={handleRateLimit}
/>

<style>
  /* Global login page styles */
  :global(body) {
    @apply bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800;
  }
</style>
