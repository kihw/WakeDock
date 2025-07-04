<!-- Enhanced Login Page with Security & Accessibility -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { auth, isAuthenticated } from '$lib/stores/auth';
  import {
    csrf,
    rateLimit,
    securityValidate,
    sanitizeInput,
    validateEmail,
    generateCSRFToken,
  } from '$lib/utils/validation';
  import {
    setupGlobalErrorHandling,
    safeEmailValidation,
    safeSanitizeInput,
    safeGenerateCSRFToken,
    safeCSRF,
  } from '$lib/utils/errorHandling';
  import { secureAccessibility } from '$lib/utils/accessibility';
  import { debugConfig } from '$lib/config/environment';
  // import { toastStore } from "$lib/stores/toastStore";

  let usernameOrEmail = 'admin'; // Pre-fill for development testing
  let password = 'admin123'; // Pre-fill for development (matches backend config)
  let twoFactorCode = '';
  let rememberMe = false;
  let loading = false;
  let error = '';
  let requiresTwoFactor = false;
  let showTwoFactorInput = false;
  let csrfToken = '';
  let formRef;
  let usernameOrEmailErrors = [];
  let passwordErrors = [];
  let twoFactorErrors = [];
  let attemptCount = 0;
  let rateLimited = false;

  // Security and accessibility enhancement
  onMount(async () => {
    // Debug configuration
    debugConfig();
    // Generate CSRF token with fallback
    try {
      csrfToken = csrf.generateToken();
      csrf.storeToken(csrfToken);
    } catch (error) {
      console.debug('Using fallback CSRF token generation:', error.message);
      try {
        csrfToken = safeGenerateCSRFToken();
      } catch (fallbackError) {
        // Ultimate fallback - generate manually
        csrfToken = generateCSRFToken();
      }
    }

    // Enhance form accessibility
    if (formRef) {
      secureAccessibility.form.enhanceForm(formRef, { enableSecurity: true });
    }

    // Check for existing authentication
    const unsubscribe = isAuthenticated.subscribe((authenticated) => {
      if (authenticated) {
        const redirectTo = $page.url.searchParams.get('redirect') || '/';
        goto(redirectTo);
      }
    });

    // Setup comprehensive error handling
    const cleanupErrorHandling = setupGlobalErrorHandling();

    return () => {
      unsubscribe();
      cleanupErrorHandling();
    };
  });

  onDestroy(() => {
    // Clear sensitive data from memory
    password = '';
    twoFactorCode = '';
    csrfToken = '';
  });

  // Enhanced validation functions with fallbacks
  function validateUsernameOrEmailField() {
    const sanitizedInput = safeSanitizeInput(usernameOrEmail);

    // Check if it's an email format or username
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isEmailFormat = emailRegex.test(sanitizedInput);
    
    let validation;
    if (isEmailFormat) {
      // Validate as email
      try {
        validation = validateEmail(sanitizedInput);
      } catch (error) {
        console.debug('Using fallback email validation:', error.message);
        validation = safeEmailValidation(sanitizedInput);
      }
    } else {
      // Validate as username (basic validation)
      const isValidUsername = sanitizedInput.length >= 3 && /^[a-zA-Z0-9_-]+$/.test(sanitizedInput);
      validation = {
        valid: isValidUsername,
        isValid: isValidUsername,
        message: isValidUsername ? '' : 'Username must be at least 3 characters and contain only letters, numbers, underscores, and hyphens'
      };
    }

    usernameOrEmailErrors = validation.valid ? [] : [validation.message || 'Invalid username or email'];
    usernameOrEmail = sanitizedInput; // Update with sanitized value

    return validation.valid;
  }

  function validatePasswordField() {
    if (!password) {
      passwordErrors = ['Password is required'];
      return false;
    }

    // Basic validation for login (detailed validation is for registration)
    if (password.length < 3) {
      passwordErrors = ['Password is too short'];
      return false;
    }

    passwordErrors = [];
    return true;
  }

  function validateTwoFactor() {
    if (requiresTwoFactor && !twoFactorCode) {
      twoFactorErrors = ['Two-factor authentication code is required'];
      return false;
    }

    if (requiresTwoFactor && !/^\d{6}$/.test(twoFactorCode)) {
      twoFactorErrors = ['Please enter a valid 6-digit code'];
      return false;
    }

    twoFactorErrors = [];
    return true;
  }

  function checkRateLimit() {
    const rateLimitKey = `login_attempt_${usernameOrEmail}`;
    // More generous rate limiting: 10 attempts per 5 minutes
    rateLimited = rateLimit.isLimited(rateLimitKey, 10, 5 * 60 * 1000);

    if (rateLimited) {
      error = 'Too many login attempts. Please try again in 5 minutes.';
      secureAccessibility.form.announceError('Rate limit exceeded. Too many login attempts.');
      return false;
    }

    return true;
  }

  async function handleLogin() {
    // Reset errors
    error = '';
    usernameOrEmailErrors = [];
    passwordErrors = [];
    twoFactorErrors = [];

    // Validate all fields
    const isUsernameOrEmailValid = validateUsernameOrEmailField();
    const isPasswordValid = validatePasswordField();
    const isTwoFactorValid = validateTwoFactor();

    if (!isUsernameOrEmailValid || !isPasswordValid || !isTwoFactorValid) {
      error = 'Please correct the errors above';
      secureAccessibility.form.announceError('Form validation failed. Please correct the errors.');
      return;
    }

    // Check rate limiting
    if (!checkRateLimit()) {
      return;
    }

    // Validate CSRF token
    let isCSRFValid = false;
    try {
      isCSRFValid = csrf.validateToken(csrfToken);
    } catch (error) {
      console.debug('CSRF validation fallback used:', error.message);
      isCSRFValid = csrfToken && csrfToken.length === 32; // Basic fallback validation
    }

    if (!isCSRFValid) {
      error = 'Security token validation failed. Please refresh the page.';
      secureAccessibility.form.announceError('Security validation failed.');
      return;
    }

    loading = true;
    attemptCount++;

    try {
      const loginData = {
        usernameOrEmail: safeSanitizeInput(usernameOrEmail),
        password, // Don't sanitize password as it may contain special chars
        twoFactorCode: requiresTwoFactor ? safeSanitizeInput(twoFactorCode) : undefined,
        rememberMe,
        csrfToken,
        fingerprint: await generateFingerprint(),
      };

      const result = await auth.login(loginData.usernameOrEmail, loginData.password, {
        twoFactorCode: loginData.twoFactorCode,
        rememberMe: loginData.rememberMe,
      });

      if (result.requiresTwoFactor && !requiresTwoFactor) {
        requiresTwoFactor = true;
        showTwoFactorInput = true;
        secureAccessibility.form.announceChange(
          'Two-factor authentication required. Please enter your 6-digit code.'
        );

        // Focus on 2FA input
        setTimeout(() => {
          const twoFactorInput = document.getElementById('twoFactorCode');
          if (twoFactorInput) {
            twoFactorInput.focus();
          }
        }, 100);

        loading = false;
        return;
      }

      // Clear sensitive data
      password = '';
      twoFactorCode = '';

      // Success announcement
      secureAccessibility.form.announceChange('Login successful. Redirecting...');

      // Redirect
      const redirectTo = $page.url.searchParams.get('redirect') || '/';
      goto(redirectTo);
    } catch (err) {
      console.error('Login error:', err);
      console.error('Error details:', {
        message: err.message,
        stack: err.stack,
        status: err.status,
        response: err.response,
      });

      // Sanitize error message to prevent XSS
      const sanitizedError = sanitizeInput(err.message || 'Login failed');
      error = sanitizedError;

      // DEBUG: Show detailed error information (remove in production)
      console.error('=== DETAILED LOGIN ERROR DEBUG ===');
      console.error('Error message:', err.message);
      console.error('Error status:', err.status);
      console.error('Error response:', err.response);
      console.error('Full error object:', err);
      console.error('=== END DEBUG ===');

      // Handle specific error cases
      if (err.message?.includes('2FA')) {
        requiresTwoFactor = true;
        showTwoFactorInput = true;
      } else if (err.message?.includes('rate limit')) {
        rateLimited = true;
      }

      // Announce error to screen readers
      secureAccessibility.form.announceError(`Login failed: ${sanitizedError}`);

      // Clear sensitive fields on error
      password = '';
      twoFactorCode = '';
    } finally {
      loading = false;
    }
  }

  async function generateFingerprint() {
    // Generate browser fingerprint for additional security
    const components = [
      navigator.userAgent,
      navigator.language,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset().toString(),
    ];

    const data = components.join('|');

    // Check if crypto.subtle is available (requires HTTPS or localhost)
    if (typeof crypto !== 'undefined' && crypto.subtle) {
      try {
        const encoder = new TextEncoder();
        const hashBuffer = await crypto.subtle.digest('SHA-256', encoder.encode(data));
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
      } catch (error) {
        console.warn('crypto.subtle.digest failed, using fallback:', error);
      }
    }

    // Fallback: simple hash function (less secure but works everywhere)
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16);
  }

  function handleKeyDown(event) {
    // Enhanced keyboard navigation
    if (event.key === 'Enter') {
      event.preventDefault();
      handleLogin();
    } else if (event.key === 'Escape') {
      // Clear form on escape
      usernameOrEmail = '';
      password = '';
      twoFactorCode = '';
      error = '';
      usernameOrEmailErrors = [];
      passwordErrors = [];
      twoFactorErrors = [];
    }
  }

  function handleInputFocus(fieldName) {
    // Clear errors when user focuses on input
    switch (fieldName) {
      case 'usernameOrEmail':
        usernameOrEmailErrors = [];
        break;
      case 'password':
        passwordErrors = [];
        break;
      case 'twoFactor':
        twoFactorErrors = [];
        break;
    }
    error = '';
  }

  async function handleSubmit(event) {
    event.preventDefault();

    // Create login data
    const loginData = {
      usernameOrEmail: sanitizeInput(usernameOrEmail),
      password: password, // Don't sanitize password as it might change valid chars
      twoFactorCode: twoFactorCode ? sanitizeInput(twoFactorCode) : '',
      rememberMe: rememberMe,
    };

    try {
      loading = true;
      error = '';

      const result = await auth.login(loginData.usernameOrEmail, loginData.password, {
        twoFactorCode: loginData.twoFactorCode,
        rememberMe: loginData.rememberMe,
      });

      // Handle 2FA requirement
      if (result && result.requiresTwoFactor && !requiresTwoFactor) {
        requiresTwoFactor = true;
        showTwoFactorInput = true;
        error = '';
        loading = false;
        return;
      }

      // Show success message if toastStore is available
      try {
        // toastStore?.success(`Welcome ${usernameOrEmail}!`);
      } catch (e) {
        // Toast store not available, continue silently
      }

      // Redirect after successful login
      const redirectTo = $page.url.searchParams.get('redirect') || '/';
      goto(redirectTo);
    } catch (err) {
      console.error('Login submit error:', err);
      console.error('Error details:', {
        message: err.message,
        stack: err.stack,
        status: err.status,
        response: err.response,
      });

      error = err.message || 'Login error';

      // Reset 2FA state on error
      if (requiresTwoFactor) {
        requiresTwoFactor = false;
        showTwoFactorInput = false;
        twoFactorCode = '';
      }

      try {
        // toastStore?.error(error);
      } catch (e) {
        // Toast store not available, continue silently
      }
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Connexion - WakeDock</title>
  <meta name="description" content="Secure login to WakeDock Docker management dashboard" />
</svelte:head>

<!-- Skip link for accessibility -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
  <div class="max-w-md w-full space-y-8">
    <!-- Header section with improved accessibility -->
    <header>
      <div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
        <svg
          class="h-8 w-8 text-blue-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
          />
        </svg>
      </div>
      <h1 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Login to WakeDock</h1>
      <p class="mt-2 text-center text-sm text-gray-600">Manage your Docker containers with ease</p>
    </header>

    <!-- Main login form with enhanced security and accessibility -->
    <main id="main-content">
      <form
        bind:this={formRef}
        class="mt-8 space-y-6"
        on:submit|preventDefault={handleLogin}
        aria-labelledby="login-heading"
        novalidate
        autocomplete="on"
        data-form-type="login"
      >
        <input type="hidden" name="csrf_token" value={csrfToken} />

        <!-- Form heading for screen readers -->
        <h2 id="login-heading" class="sr-only">Login Form</h2>

        <div class="space-y-4" role="group" aria-labelledby="login-fields">
          <h3 id="login-fields" class="sr-only">Login Credentials</h3>

          <!-- Username or Email field with validation -->
          <div>
            <label for="usernameOrEmail" class="block text-sm font-medium text-gray-700 mb-1">
              Username or Email
              <span class="text-red-500" aria-label="required">*</span>
            </label>
            <input
              id="usernameOrEmail"
              name="usernameOrEmail"
              type="text"
              required
              aria-required="true"
              aria-describedby={usernameOrEmailErrors.length > 0 ? 'usernameOrEmail-error' : 'usernameOrEmail-hint'}
              aria-invalid={usernameOrEmailErrors.length > 0}
              bind:value={usernameOrEmail}
              on:blur={validateUsernameOrEmailField}
              on:focus={() => handleInputFocus('usernameOrEmail')}
              on:keydown={handleKeyDown}
              class="relative block w-full appearance-none rounded-md border {usernameOrEmailErrors.length > 0
                ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'} px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none sm:text-sm"
              placeholder="Enter your username or email"
              disabled={loading}
              autocomplete="username"
              spellcheck="false"
              data-lpignore="false"
              data-form-type="username"
            />
            <div id="usernameOrEmail-hint" class="sr-only">Enter your username or email address to log in</div>
            {#if usernameOrEmailErrors.length > 0}
              <div id="usernameOrEmail-error" class="mt-1 text-sm text-red-600" role="alert">
                {#each usernameOrEmailErrors as usernameOrEmailError}
                  <p>{usernameOrEmailError}</p>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Password field with validation -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
              Password
              <span class="text-red-500" aria-label="required">*</span>
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              aria-required="true"
              aria-describedby={passwordErrors.length > 0 ? 'password-error' : 'password-hint'}
              aria-invalid={passwordErrors.length > 0}
              bind:value={password}
              on:blur={validatePasswordField}
              on:focus={() => handleInputFocus('password')}
              on:keydown={handleKeyDown}
              class="relative block w-full appearance-none rounded-md border {passwordErrors.length >
              0
                ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'} px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none sm:text-sm"
              placeholder="Enter your password"
              disabled={loading}
              autocomplete="current-password"
              spellcheck="false"
              data-lpignore="false"
              data-form-type="password"
            />
            <div id="password-hint" class="sr-only">Enter your password to log in</div>
            {#if passwordErrors.length > 0}
              <div id="password-error" class="mt-1 text-sm text-red-600" role="alert">
                {#each passwordErrors as passwordError}
                  <p>{passwordError}</p>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Two-Factor Authentication section -->
          {#if showTwoFactorInput}
            <div class="bg-blue-50 p-4 rounded-md" role="region" aria-labelledby="2fa-heading">
              <div class="flex">
                <div class="flex-shrink-0">
                  <svg
                    class="h-5 w-5 text-blue-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h3 id="2fa-heading" class="text-sm font-medium text-blue-800">
                    Two-Factor Authentication Required
                  </h3>
                  <div class="mt-2">
                    <p class="text-sm text-blue-700">
                      Please enter the 6-digit code from your authenticator app.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label for="twoFactorCode" class="block text-sm font-medium text-gray-700 mb-1">
                Two-Factor Authentication Code
                <span class="text-red-500" aria-label="required">*</span>
              </label>
              <input
                id="twoFactorCode"
                name="twoFactorCode"
                type="text"
                inputmode="numeric"
                pattern="[0-9]*"
                maxlength="6"
                required={requiresTwoFactor}
                aria-required={requiresTwoFactor}
                aria-describedby={twoFactorErrors.length > 0 ? '2fa-error' : '2fa-hint'}
                aria-invalid={twoFactorErrors.length > 0}
                bind:value={twoFactorCode}
                on:blur={validateTwoFactor}
                on:focus={() => handleInputFocus('twoFactor')}
                on:keydown={handleKeyDown}
                class="relative block w-full appearance-none rounded-md border {twoFactorErrors.length >
                0
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'} px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none sm:text-sm text-center tracking-widest"
                placeholder="000000"
                disabled={loading}
                autocomplete="one-time-code"
              />
              <div id="2fa-hint" class="sr-only">
                Enter the 6-digit code from your authenticator app
              </div>
              {#if twoFactorErrors.length > 0}
                <div id="2fa-error" class="mt-1 text-sm text-red-600" role="alert">
                  {#each twoFactorErrors as twoFactorError}
                    <p>{twoFactorError}</p>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}

          <!-- Form controls -->
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                bind:checked={rememberMe}
                aria-describedby="remember-me-description"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded focus:ring-2"
              />
              <label for="remember-me" class="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
              <div id="remember-me-description" class="sr-only">Keep me logged in for 30 days</div>
            </div>

            <div class="text-sm">
              <a
                href="/forgot-password"
                class="font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
              >
                Forgot your password?
              </a>
            </div>
          </div>
        </div>

        <!-- Error display with accessibility -->
        {#if error}
          <div class="rounded-md bg-red-50 p-4" role="alert" aria-live="polite">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg
                  class="h-5 w-5 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-red-800">Login Error</h3>
                <div class="mt-2 text-sm text-red-700">
                  {error}
                </div>
              </div>
            </div>
          </div>
        {/if}

        <!-- Rate limiting notice -->
        {#if rateLimited}
          <div class="rounded-md bg-yellow-50 p-4" role="alert" aria-live="polite">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg
                  class="h-5 w-5 text-yellow-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fill-rule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-yellow-800">Rate Limit Exceeded</h3>
                <div class="mt-2 text-sm text-yellow-700">
                  Too many login attempts. Please wait 15 minutes before trying again.
                </div>
              </div>
            </div>
          </div>
        {/if}

        <!-- Submit button with loading state -->
        <div>
          <button
            type="submit"
            disabled={loading || rateLimited}
            aria-describedby="submit-button-description"
            class="group relative flex w-full justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {#if loading}
              <svg
                class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Signing in...
            {:else}
              Sign in
            {/if}
          </button>
          <div id="submit-button-description" class="sr-only">
            {loading
              ? 'Please wait while we sign you in'
              : rateLimited
                ? 'Button disabled due to rate limiting'
                : 'Click to sign in to your account'}
          </div>
        </div>

        <!-- Register link -->
        <div class="text-center">
          <p class="text-sm text-gray-600">
            Don't have an account?
            <a
              href="/register"
              class="font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
            >
              Create an account
            </a>
          </p>
        </div>
      </form>
    </main>
  </div>
</div>

<style>
  /* Style pour améliorer l'apparence */
  input:focus {
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  /* Prevent autofill extension styling conflicts */
  input:-webkit-autofill,
  input:-webkit-autofill:hover,
  input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px white inset !important;
    -webkit-text-fill-color: #111827 !important;
  }

  /* Hide autofill extension overlays */
  input::-webkit-contacts-auto-fill-button,
  input::-webkit-credentials-auto-fill-button {
    visibility: hidden;
    display: none !important;
    pointer-events: none;
    height: 0;
    width: 0;
    margin: 0;
  }
</style>
