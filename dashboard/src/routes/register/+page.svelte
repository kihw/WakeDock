<!-- Page d'inscription -->
<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import { goto } from '$app/navigation';
  import { isAuthenticated } from '$lib/stores/auth';
  import { toastStore } from '$lib/stores/toastStore';
  import { 
    validateEmail, 
    validatePassword, 
    validateUsername,
    sanitizeInput,
    validatePasswordStrength,
    generateCSRFToken,
    verifyCSRFToken,
    checkRateLimit
  } from '$lib/utils/validation';
  import { api } from '$lib/api.js';
  import { 
    manageFocus, 
    announceToScreenReader, 
    validateFormAccessibility,
    getAccessibleErrorMessage,
    enhanceFormAccessibility
  } from '$lib/utils/accessibility';

  let formData = {
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    acceptTerms: false,
    subscribeNewsletter: false,
  };
  let loading = false;
  let errors = {};
  let passwordStrength = {
    score: 0,
    feedback: [],
    isValid: false,
  };

  // Security and accessibility state
  let csrfToken = '';
  let attemptCount = 0;
  let isRateLimited = false;
  let formElement;
  let firstErrorElement;
  let skipLinkFocused = false;

  // Password strength indicators
  let showPasswordStrength = false;
  let showPassword = false;
  let showConfirmPassword = false;

  // Accessibility announcements
  let announceMessage = '';
  let liveRegion;

  // Rediriger si déjà connecté et initialisation sécurisée
  onMount(async () => {
    const unsubscribe = isAuthenticated.subscribe((authenticated) => {
      if (authenticated) {
        goto('/');
      }
    });

    // Initialize security features
    csrfToken = generateCSRFToken();
    
    // Setup accessibility enhancements
    if (formElement) {
      enhanceFormAccessibility(formElement);
    }

    // Announce page load to screen readers
    announceToScreenReader('Registration form loaded. Fill out all required fields to create your account.');

    return unsubscribe;
  });

  onDestroy(() => {
    // Clear sensitive data from memory
    formData.password = '';
    formData.confirmPassword = '';
    csrfToken = '';
  });

  // Handle skip link focus
  function handleSkipLink() {
    skipLinkFocused = true;
    if (formElement) {
      manageFocus(formElement.querySelector('input[name="username"]'));
    }
  }

  // Real-time password strength validation with security features
  function checkPasswordStrength(password) {
    if (!password) {
      passwordStrength = { score: 0, feedback: [], isValid: false };
      showPasswordStrength = false;
      return;
    }

    showPasswordStrength = true;
    
    // Use enhanced password validation
    const strengthResult = validatePasswordStrength(password, {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      preventCommonPatterns: true,
      checkBreachedPasswords: false // Disable for offline use
    });

    passwordStrength = {
      score: strengthResult.score,
      feedback: strengthResult.feedback.slice(0, 3), // Show max 3 suggestions
      isValid: strengthResult.isValid && strengthResult.score >= 4,
    };

    // Clear password confirmation error if passwords now match
    if (formData.confirmPassword && password === formData.confirmPassword) {
      errors = { ...errors };
      delete errors.confirmPassword;
    }

    // Announce strength changes to screen readers
    if (strengthResult.score > 0) {
      const strengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'][strengthResult.score];
      announceToScreenReader(`Password strength: ${strengthText}`);
    }
  }
      feedback: feedback.slice(0, 3), // Show max 3 suggestions
      isValid: result.isValid && score >= 4,
    };

    // Clear password confirmation error if passwords now match
    if (formData.confirmPassword && password === formData.confirmPassword) {
      errors = { ...errors };
      delete errors.confirmPassword;
    }
  }

  // Real-time field validation with security and accessibility
  function validateField(field, value) {
    const newErrors = { ...errors };
    
    // Sanitize input to prevent XSS
    const sanitizedValue = sanitizeInput(value);
    
    switch (field) {
      case 'username':
        const usernameValidation = validateUsername(sanitizedValue);
        if (!usernameValidation.isValid) {
          newErrors.username = usernameValidation.errors[0];
        } else {
          delete newErrors.username;
        }
        break;
        
      case 'email':
        const emailValidation = validateEmail(sanitizedValue);
        if (!emailValidation.isValid) {
          newErrors.email = emailValidation.errors[0];
        } else {
          delete newErrors.email;
        }
        break;
        
      case 'full_name':
        if (!sanitizedValue || sanitizedValue.trim().length < 2) {
          newErrors.full_name = 'Full name must be at least 2 characters';
        } else if (sanitizedValue.trim().length > 100) {
          newErrors.full_name = 'Full name must be less than 100 characters';
        } else {
          delete newErrors.full_name;
        }
        break;
        
      case 'confirmPassword':
        if (value && value !== formData.password) {
          newErrors.confirmPassword = 'Passwords do not match';
        } else {
          delete newErrors.confirmPassword;
        }
        break;
        
      case 'acceptTerms':
        if (!value) {
          newErrors.acceptTerms = 'You must accept the terms and conditions';
        } else {
          delete newErrors.acceptTerms;
        }
        break;
    }
    
    errors = newErrors;

    // Announce validation errors to screen readers
    if (newErrors[field]) {
      announceToScreenReader(getAccessibleErrorMessage(field, newErrors[field]));
    }
  }

  // Debounced validation for performance
  let validationTimer;
  function debouncedValidation(field, value, delay = 300) {
    clearTimeout(validationTimer);
    validationTimer = setTimeout(() => {
      validateField(field, value);
    }, delay);
  }
  // Comprehensive form validation with security checks
  function validateForm() {
    errors = {};

    // Check rate limiting
    if (isRateLimited) {
      errors.general = 'Too many registration attempts. Please wait before trying again.';
      return false;
    }

    // Sanitize all inputs
    formData.username = sanitizeInput(formData.username);
    formData.email = sanitizeInput(formData.email);
    formData.full_name = sanitizeInput(formData.full_name);

    // Username validation
    const usernameResult = validateUsername(formData.username);
    if (!usernameResult.isValid) {
      errors.username = usernameResult.errors[0];
    }

    // Email validation
    const emailResult = validateEmail(formData.email);
    if (!emailResult.isValid) {
      errors.email = emailResult.errors[0];
    }

    // Password validation
    checkPasswordStrength(formData.password);
    if (!passwordStrength.isValid) {
      errors.password = passwordStrength.feedback[0] || 'Password does not meet requirements';
    }

    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    // Full name validation
    if (!formData.full_name || formData.full_name.trim().length < 2) {
      errors.full_name = 'Full name must be at least 2 characters';
    } else if (formData.full_name.trim().length > 100) {
      errors.full_name = 'Full name must be less than 100 characters';
    }

    // Terms acceptance validation
    if (!formData.acceptTerms) {
      errors.acceptTerms = 'You must accept the terms and conditions';
    }

    // CSRF token validation
    if (!verifyCSRFToken(csrfToken)) {
      errors.general = 'Security token expired. Please refresh the page.';
      return false;
    }

    const isValid = Object.keys(errors).length === 0;
    
    // Focus first error for accessibility
    if (!isValid) {
      tick().then(() => {
        const firstErrorField = Object.keys(errors)[0];
        const errorElement = formElement?.querySelector(`[name="${firstErrorField}"]`);
        if (errorElement) {
          manageFocus(errorElement);
          announceToScreenReader(`Form validation failed. ${Object.keys(errors).length} errors found. Please review and correct.`);
        }
      });
    }

    return isValid;
  }

  async function handleRegister() {
    // Check rate limiting
    attemptCount++;
    const rateLimitResult = checkRateLimit('register', attemptCount, 5, 15 * 60 * 1000); // 5 attempts per 15 minutes
    if (!rateLimitResult.allowed) {
      isRateLimited = true;
      errors.general = `Too many registration attempts. Please wait ${Math.ceil(rateLimitResult.resetTime / 60000)} minutes before trying again.`;
      announceToScreenReader('Registration temporarily blocked due to too many attempts.');
      return;
    }

    if (!validateForm()) {
      return;
    }

    loading = true;
    announceToScreenReader('Creating account, please wait...');

    try {
      // Use the API client for registration with CSRF protection
      const userData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        role: 'user', // Default role
        is_active: true,
        subscribe_newsletter: formData.subscribeNewsletter,
        _csrf: csrfToken, // Include CSRF token
      };

      const newUser = await api.users.create(userData);

      // Clear sensitive data immediately
      formData.password = '';
      formData.confirmPassword = '';

      toastStore.addToast({
        type: 'success',
        message: 'Compte créé avec succès! Un email de vérification a été envoyé à votre adresse.',
      });

      // Show email verification notice
      toastStore.addToast({
        type: 'info',
        message: 'Veuillez vérifier votre email avant de vous connecter.',
        persistent: true,
      });

      // Announce success to screen readers
      announceToScreenReader('Account created successfully! Please check your email for verification instructions.');

      // Redirect to login page
      goto('/login?registered=true');
    } catch (error) {
      console.error('Registration error:', error);

      // Clear sensitive data on error
      formData.password = '';
      formData.confirmPassword = '';

      if (error.code === 'VALIDATION_ERROR') {
        // Handle specific validation errors
        if (error.details?.username) {
          errors.username = "Ce nom d'utilisateur est déjà pris";
        }
        if (error.details?.email) {
          errors.email = 'Cet email est déjà utilisé';
        }
        if (error.details?.password) {
          errors.password = error.details.password;
        }
      } else if (error.code === 'USER_EXISTS') {
        if (error.message.includes('username')) {
          errors.username = "Ce nom d'utilisateur est déjà pris";
        } else if (error.message.includes('email')) {
          errors.email = 'Cet email est déjà utilisé';
        } else {
          errors.general = error.message;
        }
      } else if (error.code === 'RATE_LIMITED') {
        isRateLimited = true;
        errors.general = 'Too many requests. Please wait before trying again.';
      } else {
        errors.general = error.message || "Erreur lors de l'inscription. Veuillez réessayer.";
      }

      // Announce error to screen readers
      announceToScreenReader(`Registration failed: ${errors.general || 'Please check the form for errors.'}`);
      
      // Focus first error field
      tick().then(() => {
        const firstErrorField = Object.keys(errors)[0];
        if (firstErrorField !== 'general') {
          const errorElement = formElement?.querySelector(`[name="${firstErrorField}"]`);
          if (errorElement) {
            manageFocus(errorElement);
          }
        }
      });
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Inscription - WakeDock</title>
  <meta name="description" content="Créez votre compte WakeDock pour gérer vos containers Docker">
</svelte:head>

<!-- Skip link for accessibility -->
<a 
  href="#main-content" 
  class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
  on:click={handleSkipLink}
>
  Aller au contenu principal
</a>

<!-- Live region for screen reader announcements -->
<div 
  bind:this={liveRegion}
  class="sr-only" 
  aria-live="polite" 
  aria-atomic="true"
>
  {announceMessage}
</div>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
  <div class="max-w-md w-full space-y-8">
    <div>
      <div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-green-100">
        <svg 
          class="h-8 w-8 text-green-600" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
          />
        </svg>
      </div>
      <h1 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Créer un compte WakeDock
      </h1>
      <p class="mt-2 text-center text-sm text-gray-600">
        Rejoignez la plateforme de gestion Docker
      </p>
    </div>

    <main id="main-content">
      <form 
        bind:this={formElement}
        class="mt-8 space-y-6" 
        on:submit|preventDefault={handleRegister}
        novalidate
        aria-label="Registration form"
      >
        <!-- CSRF Token (hidden) -->
        <input type="hidden" name="_csrf" value={csrfToken} />

        {#if errors.general}
          <div 
            class="rounded-md bg-red-50 p-4" 
            role="alert"
            aria-labelledby="error-title"
          >
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
                <h3 id="error-title" class="text-sm font-medium text-red-800">Erreur</h3>
                <div class="mt-2 text-sm text-red-700">
                  {errors.general}
                </div>
              </div>
            </div>
          </div>
        {/if}

        <fieldset class="space-y-4">
          <legend class="sr-only">Account Information</legend>
          
          <!-- Full Name Field -->
          <div>
            <label for="full_name" class="block text-sm font-medium text-gray-700 mb-1">
              Nom complet <span class="text-red-500" aria-label="required">*</span>
            </label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              required
              bind:value={formData.full_name}
              on:input={() => debouncedValidation('full_name', formData.full_name)}
              on:blur={() => validateField('full_name', formData.full_name)}
              class="relative block w-full appearance-none rounded-md border px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none focus:ring-2 sm:text-sm
                {errors.full_name
                  ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                  : formData.full_name && !errors.full_name
                  ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                  : 'border-gray-300 focus:border-green-500 focus:ring-green-500'}"
              placeholder="Entrez votre nom complet"
              disabled={loading}
              autocomplete="name"
              aria-describedby={errors.full_name ? 'full_name-error' : 'full_name-help'}
              aria-invalid={errors.full_name ? 'true' : 'false'}
            />
            {#if !errors.full_name}
              <p id="full_name-help" class="mt-1 text-sm text-gray-500">
                Votre nom complet sera visible sur votre profil
              </p>
            {/if}
            {#if errors.full_name}
              <p id="full_name-error" class="mt-1 text-sm text-red-600" role="alert">
                <span class="sr-only">Erreur:</span> {errors.full_name}
              </p>
            {/if}
          </div>

          <!-- Username Field -->
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
              Nom d'utilisateur <span class="text-red-500" aria-label="required">*</span>
            </label>
            <div class="relative">
              <input
                id="username"
                name="username"
                type="text"
                required
                bind:value={formData.username}
                on:input={() => debouncedValidation('username', formData.username)}
                on:blur={() => validateField('username', formData.username)}
                class="relative block w-full appearance-none rounded-md border px-3 py-2 pr-10 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none focus:ring-2 sm:text-sm
                  {errors.username
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : formData.username && !errors.username
                    ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                    : 'border-gray-300 focus:border-green-500 focus:ring-green-500'}"
                placeholder="Choisissez un nom d'utilisateur"
                disabled={loading}
                autocomplete="username"
                aria-describedby={errors.username ? 'username-error' : 'username-help'}
                aria-invalid={errors.username ? 'true' : 'false'}
                minlength="3"
                maxlength="20"
              />
              <!-- Validation icon -->
              {#if formData.username}
                <div class="absolute inset-y-0 right-0 flex items-center pr-3">
                  {#if errors.username}
                    <svg class="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                  {:else}
                    <svg class="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                  {/if}
                </div>
              {/if}
            </div>
            {#if !errors.username}
              <p id="username-help" class="mt-1 text-sm text-gray-500">
                3-20 caractères, lettres, chiffres et tirets uniquement
              </p>
            {/if}
            {#if errors.username}
              <p id="username-error" class="mt-1 text-sm text-red-600" role="alert">
                <span class="sr-only">Erreur:</span> {errors.username}
              </p>
            {/if}
          </div>

          <!-- Email Field -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
              Adresse email <span class="text-red-500" aria-label="required">*</span>
            </label>
            <div class="relative">
              <input
                id="email"
                name="email"
                type="email"
                required
                bind:value={formData.email}
                on:input={() => debouncedValidation('email', formData.email)}
                on:blur={() => validateField('email', formData.email)}
                class="relative block w-full appearance-none rounded-md border px-3 py-2 pr-10 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none focus:ring-2 sm:text-sm
                  {errors.email
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : formData.email && !errors.email
                    ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                    : 'border-gray-300 focus:border-green-500 focus:ring-green-500'}"
                placeholder="Entrez votre adresse email"
                disabled={loading}
                autocomplete="email"
                aria-describedby={errors.email ? 'email-error' : 'email-help'}
                aria-invalid={errors.email ? 'true' : 'false'}
              />
              <!-- Validation icon -->
              {#if formData.email}
                <div class="absolute inset-y-0 right-0 flex items-center pr-3">
                  {#if errors.email}
                    <svg class="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                  {:else}
                    <svg class="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                  {/if}
                </div>
              {/if}
            </div>
            {#if !errors.email}
              <p id="email-help" class="mt-1 text-sm text-gray-500">
                Utilisée pour les notifications et la récupération de compte
              </p>
            {/if}
            {#if errors.email}
              <p id="email-error" class="mt-1 text-sm text-red-600" role="alert">
                <span class="sr-only">Erreur:</span> {errors.email}
              </p>
            {/if}
          </div>

          <!-- Password Field -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
              Mot de passe <span class="text-red-500" aria-label="required">*</span>
            </label>
            <div class="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                required
                bind:value={formData.password}
                on:input={() => {
                  checkPasswordStrength(formData.password);
                  showPasswordStrength = formData.password.length > 0;
                }}
                on:focus={() => (showPasswordStrength = true)}
                class="relative block w-full appearance-none rounded-md border px-3 py-2 pr-10 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none focus:ring-2 sm:text-sm
                  {errors.password
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : formData.password && passwordStrength.isValid
                    ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                    : 'border-gray-300 focus:border-green-500 focus:ring-green-500'}"
                placeholder="Créez un mot de passe sécurisé"
                disabled={loading}
                autocomplete="new-password"
                aria-describedby={errors.password ? 'password-error' : showPasswordStrength ? 'password-strength password-help' : 'password-help'}
                aria-invalid={errors.password ? 'true' : 'false'}
                minlength="8"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 flex items-center pr-3 hover:text-gray-600 focus:outline-none focus:text-gray-600"
                on:click={() => (showPassword = !showPassword)}
                aria-label={showPassword ? 'Masquer le mot de passe' : 'Montrer le mot de passe'}
                tabindex="0"
              >
                <svg
                  class="h-5 w-5 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  {#if showPassword}
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"
                    />
                  {:else}
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  {/if}
                </svg>
              </button>
            </div>
          </div>

          <!-- Password Strength Indicator -->
          {#if showPasswordStrength && formData.password}
            <div class="mt-2">
              <div class="flex items-center space-x-2">
                <div class="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    class="h-2 rounded-full transition-all duration-300 {passwordStrength.score <= 1
                      ? 'bg-red-500'
                      : passwordStrength.score <= 2
                        ? 'bg-yellow-500'
                        : passwordStrength.score <= 3
                          ? 'bg-blue-500'
                          : 'bg-green-500'}"
                    style="width: {(passwordStrength.score / 4) * 100}%"
                  ></div>
                </div>
                <span
                  class="text-xs font-medium {passwordStrength.score <= 1
                    ? 'text-red-600'
                    : passwordStrength.score <= 2
                      ? 'text-yellow-600'
                      : passwordStrength.score <= 3
                        ? 'text-blue-600'
                        : 'text-green-600'}"
                >
                  {passwordStrength.score <= 1
                    ? 'Faible'
                    : passwordStrength.score <= 2
                      ? 'Moyen'
                      : passwordStrength.score <= 3
                        ? 'Bon'
                        : 'Excellent'}
                </span>
              </div>
              {#if passwordStrength.feedback.length > 0}
                <ul class="mt-1 text-xs text-gray-600 space-y-1">
                  {#each passwordStrength.feedback as feedback}
                    <li class="flex items-center">
                      <svg
                        class="h-3 w-3 mr-1 text-red-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clip-rule="evenodd"
                        />
                      </svg>
                      {feedback}
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          {/if}

          {#if errors.password}
            <p class="mt-1 text-sm text-red-600">
              {errors.password}
            </p>
          {/if}
        </div>

        <div>
          <label for="confirmPassword" class="sr-only">Confirmer le mot de passe</label>
          <div class="relative">
            <input
              id="confirmPassword"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              required
              bind:value={formData.confirmPassword}
              on:input={() => validateField('confirmPassword')}
              class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 pr-10 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-green-500 focus:outline-none focus:ring-green-500 sm:text-sm {errors.confirmPassword
                ? 'border-red-500'
                : ''}"
              placeholder="Confirmer le mot de passe"
              disabled={loading}
            />
            <button
              type="button"
              class="absolute inset-y-0 right-0 flex items-center pr-3"
              on:click={() => (showConfirmPassword = !showConfirmPassword)}
            >
              <svg
                class="h-5 w-5 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {#if showConfirmPassword}
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"
                  />
                {:else}
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                {/if}
              </svg>
            </button>
          </div>

          <!-- Password Match Indicator -->
          {#if formData.confirmPassword && formData.password}
            <div class="mt-1 flex items-center">
              {#if formData.password === formData.confirmPassword}
                <svg class="h-4 w-4 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clip-rule="evenodd"
                  />
                </svg>
                <span class="text-sm text-green-600">Les mots de passe correspondent</span>
              {:else}
                <svg class="h-4 w-4 text-red-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clip-rule="evenodd"
                  />
                </svg>
                <span class="text-sm text-red-600">Les mots de passe ne correspondent pas</span>
              {/if}
            </div>
          {/if}

          {#if errors.confirmPassword}
            <p class="mt-1 text-sm text-red-600">
              {errors.confirmPassword}
            </p>
          {/if}
        </div>
      </div>

      <!-- Terms and Conditions -->
      <div class="space-y-3">
        <div class="flex items-start">
          <input
            id="acceptTerms"
            name="acceptTerms"
            type="checkbox"
            bind:checked={formData.acceptTerms}
            on:change={() => validateField('acceptTerms')}
            class="mt-1 h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500 {errors.acceptTerms
              ? 'border-red-500'
              : ''}"
            disabled={loading}
          />
          <label for="acceptTerms" class="ml-2 block text-sm text-gray-900">
            J'accepte les
            <a href="/terms" target="_blank" class="text-green-600 hover:text-green-500 underline">
              conditions d'utilisation
            </a>
            et la
            <a
              href="/privacy"
              target="_blank"
              class="text-green-600 hover:text-green-500 underline"
            >
              politique de confidentialité
            </a>
            <span class="text-red-500">*</span>
          </label>
        </div>
        {#if errors.acceptTerms}
          <p class="text-sm text-red-600 ml-6">
            {errors.acceptTerms}
          </p>
        {/if}

        <div class="flex items-start">
          <input
            id="subscribeNewsletter"
            name="subscribeNewsletter"
            type="checkbox"
            bind:checked={formData.subscribeNewsletter}
            class="mt-1 h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
            disabled={loading}
          />
          <label for="subscribeNewsletter" class="ml-2 block text-sm text-gray-700">
            Je souhaite recevoir la newsletter avec les dernières nouvelles et mises à jour de
            WakeDock
          </label>
        </div>
      </div>

      <div>
        <button
          type="submit"
          disabled={loading}
          class="group relative flex w-full justify-center rounded-md border border-transparent bg-green-600 py-2 px-4 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {#if loading}
            <svg
              class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
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
            Création du compte...
          {:else}
            Créer le compte
          {/if}
        </button>
      </div>

      <div class="text-center">
        <p class="text-sm text-gray-600">
          Déjà un compte?
          <a href="/login" class="font-medium text-green-600 hover:text-green-500">
            Se connecter
          </a>
        </p>
      </div>
    </form>
  </div>
</div>

<style>
  /* Style pour améliorer l'apparence */
  input:focus {
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.1);
  }
</style>
