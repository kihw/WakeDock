<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import { 
    validateEmail,
    validatePassword,
    validateUsername,
    sanitizeInput,
    validatePasswordStrength,
    generateCSRFToken,
    verifyCSRFToken,
    checkRateLimit,
  } from '$lib/utils/validation';
  import { 
    manageFocus,
    announceToScreenReader,
    getAccessibleErrorMessage,
    enhanceFormAccessibility,
  } from '$lib/utils/accessibility';
  import { uiLogger } from '$lib/utils/logger';
  
  import TextInput from '../FormFields/TextInput.svelte';
  import EmailInput from '../FormFields/EmailInput.svelte';
  import PasswordInput from '../FormFields/PasswordInput.svelte';
  import PasswordConfirmInput from '../FormFields/PasswordConfirmInput.svelte';
  import CheckboxField from '../FormFields/CheckboxField.svelte';
  import ErrorAlert from '../../ui/ErrorAlert.svelte';

  export let loading: boolean = false;

  const dispatch = createEventDispatcher<{
    submit: {
      formData: {
        username: string;
        email: string;
        password: string;
        full_name: string;
        acceptTerms: boolean;
        subscribeNewsletter: boolean;
        _csrf: string;
      };
    };
  }>();

  // Form data
  let formData = {
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    acceptTerms: false,
    subscribeNewsletter: false,
  };

  // State
  let errors: Record<string, string> = {};
  let passwordStrength = {
    score: 0,
    feedback: [],
    isValid: false,
  };

  // Security and accessibility state
  let csrfToken = '';
  let attemptCount = 0;
  let isRateLimited = false;
  let formElement: HTMLFormElement;

  // Initialize security features
  onMount(() => {
    csrfToken = generateCSRFToken();
    
    if (formElement) {
      enhanceFormAccessibility(formElement);
    }
    
    announceToScreenReader(
      'Registration form loaded. Fill out all required fields to create your account.'
    );
  });

  onDestroy(() => {
    // Clear sensitive data from memory
    formData.password = '';
    formData.confirmPassword = '';
    csrfToken = '';
  });

  // Password strength validation
  function checkPasswordStrength(password: string) {
    if (!password) {
      passwordStrength = { score: 0, feedback: [], isValid: false };
      return;
    }

    const strengthResult = validatePasswordStrength(password, {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      preventCommonPatterns: true,
      checkBreachedPasswords: false,
    });

    passwordStrength = {
      score: strengthResult.score,
      feedback: strengthResult.feedback.slice(0, 3),
      isValid: strengthResult.isValid && strengthResult.score >= 4,
    };

    // Clear password confirmation error if passwords now match
    if (formData.confirmPassword && password === formData.confirmPassword) {
      errors = { ...errors };
      delete errors.confirmPassword;
    }

    // Announce strength changes to screen readers
    if (strengthResult.score > 0) {
      const strengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'][
        strengthResult.score
      ];
      announceToScreenReader(`Password strength: ${strengthText}`);
    }
  }

  // Field validation functions
  function validateField(field: string, value: any) {
    try {
      const newErrors = { ...errors };

      if (value === null || value === undefined) {
        return;
      }

      const stringValue = String(value);

      if (stringValue === '') {
        if (newErrors[field]) {
          delete newErrors[field];
          errors = newErrors;
        }
        return;
      }

      let sanitizedValue;
      try {
        sanitizedValue = sanitizeInput(stringValue);
      } catch (sanitizeError) {
        uiLogger.error('Register', sanitizeError, {
          context: 'sanitizeInput',
          field,
          value: stringValue,
        });
        sanitizedValue = stringValue;
      }

      switch (field) {
        case 'username':
          const usernameValidation = validateUsername(sanitizedValue);
          if (!usernameValidation || !usernameValidation.isValid) {
            newErrors.username =
              (usernameValidation && usernameValidation.errors && usernameValidation.errors[0]) ||
              'Invalid username';
          } else {
            delete newErrors.username;
          }
          break;

        case 'email':
          const emailValidation = validateEmail(sanitizedValue);
          if (!emailValidation || !emailValidation.isValid) {
            newErrors.email =
              (emailValidation && emailValidation.message) || 'Invalid email address';
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
          if (stringValue && formData && formData.password && stringValue !== formData.password) {
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

      if (newErrors[field]) {
        announceToScreenReader(getAccessibleErrorMessage(field, newErrors[field]));
      }
    } catch (error) {
      uiLogger.error('Register', error, { context: 'validateField', field, value });
    }
  }

  // Debounced validation
  let validationTimer: number;
  function debouncedValidation(field: string, value: any, delay = 300) {
    try {
      clearTimeout(validationTimer);
      validationTimer = setTimeout(() => {
        validateField(field, value);
      }, delay);
    } catch (err) {
      uiLogger.error('Register', err, { context: 'debouncedValidation', field, value });
    }
  }

  // Form validation
  function validateForm() {
    errors = {};

    if (isRateLimited) {
      errors.general = 'Too many registration attempts. Please wait before trying again.';
      return false;
    }

    if (!formData || typeof formData !== 'object') {
      errors.general = 'Form data is invalid. Please refresh the page and try again.';
      return false;
    }

    // Sanitize all inputs
    formData.username = sanitizeInput(formData.username || '');
    formData.email = sanitizeInput(formData.email || '');
    formData.full_name = sanitizeInput(formData.full_name || '');

    // Validate all fields
    const usernameResult = validateUsername(formData.username);
    if (!usernameResult.isValid) {
      errors.username = usernameResult.errors[0];
    }

    const emailResult = validateEmail(formData.email);
    if (!emailResult.isValid) {
      errors.email = emailResult.errors[0];
    }

    checkPasswordStrength(formData.password);
    if (!passwordStrength.isValid) {
      errors.password = passwordStrength.feedback[0] || 'Password does not meet requirements';
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.full_name || formData.full_name.trim().length < 2) {
      errors.full_name = 'Full name must be at least 2 characters';
    } else if (formData.full_name.trim().length > 100) {
      errors.full_name = 'Full name must be less than 100 characters';
    }

    if (!formData.acceptTerms) {
      errors.acceptTerms = 'You must accept the terms and conditions';
    }

    if (!verifyCSRFToken(csrfToken)) {
      errors.general = 'Security token expired. Please refresh the page.';
      return false;
    }

    const isValid = Object.keys(errors).length === 0;

    if (!isValid) {
      tick().then(() => {
        const firstErrorField = Object.keys(errors)[0];
        const errorElement = formElement?.querySelector(`[name="${firstErrorField}"]`);
        if (errorElement) {
          manageFocus(errorElement);
          announceToScreenReader(
            `Form validation failed. ${Object.keys(errors).length} errors found. Please review and correct.`
          );
        }
      });
    }

    return isValid;
  }

  // Handle form submission
  function handleSubmit() {
    attemptCount++;
    const rateLimitResult = checkRateLimit('register', attemptCount, 5, 15 * 60 * 1000);
    if (!rateLimitResult.allowed) {
      isRateLimited = true;
      errors.general = `Too many registration attempts. Please wait ${Math.ceil(rateLimitResult.resetTime / 60000)} minutes before trying again.`;
      announceToScreenReader('Registration temporarily blocked due to too many attempts.');
      return;
    }

    if (!validateForm()) {
      return;
    }

    announceToScreenReader('Creating account, please wait...');

    const userData = {
      username: formData.username || '',
      email: formData.email || '',
      password: formData.password || '',
      full_name: formData.full_name || '',
      acceptTerms: formData.acceptTerms,
      subscribeNewsletter: formData.subscribeNewsletter,
      _csrf: csrfToken,
    };

    dispatch('submit', { formData: userData });
  }

  // Event handlers for form fields
  function handlePasswordInput(event: CustomEvent<{ value: string }>) {
    formData.password = event.detail.value;
    checkPasswordStrength(formData.password);
  }

  function handleConfirmPasswordInput(event: CustomEvent<{ value: string }>) {
    formData.confirmPassword = event.detail.value;
    debouncedValidation('confirmPassword', formData.confirmPassword);
  }
</script>

<form
  bind:this={formElement}
  class="mt-8 space-y-6"
  on:submit|preventDefault={handleSubmit}
  novalidate
  aria-label="Registration form"
  data-form-type="register"
  autocomplete="on"
>
  <!-- CSRF Token (hidden) -->
  <input type="hidden" name="_csrf" value={csrfToken} />

  {#if errors.general}
    <ErrorAlert error={errors.general} />
  {/if}

  <!-- Account Information Section -->
  <div class="space-y-4">
    <!-- Full Name Field -->
    <TextInput
      id="full_name"
      name="full_name"
      label="Nom complet"
      placeholder="Entrez votre nom complet"
      required={true}
      disabled={loading}
      autocomplete="name"
      minlength={2}
      maxlength={100}
      bind:value={formData.full_name}
      error={errors.full_name}
      helpText="Votre nom complet sera visible sur votre profil"
      on:input={(e) => debouncedValidation('full_name', e.detail.value)}
      on:blur={(e) => validateField('full_name', e.detail.value)}
    />

    <!-- Username Field -->
    <TextInput
      id="username"
      name="username"
      label="Nom d'utilisateur"
      placeholder="Choisissez un nom d'utilisateur"
      required={true}
      disabled={loading}
      autocomplete="username"
      minlength={3}
      maxlength={20}
      bind:value={formData.username}
      error={errors.username}
      helpText="3-20 caractères, lettres, chiffres et tirets uniquement"
      on:input={(e) => debouncedValidation('username', e.detail.value)}
      on:blur={(e) => validateField('username', e.detail.value)}
    />

    <!-- Email Field -->
    <EmailInput
      id="email"
      name="email"
      label="Adresse email"
      placeholder="Entrez votre adresse email"
      required={true}
      disabled={loading}
      bind:value={formData.email}
      error={errors.email}
      helpText="Utilisée pour les notifications et la récupération de compte"
      on:input={(e) => debouncedValidation('email', e.detail.value)}
      on:blur={(e) => validateField('email', e.detail.value)}
    />

    <!-- Password Field -->
    <PasswordInput
      id="password"
      name="password"
      label="Mot de passe"
      placeholder="Créez un mot de passe sécurisé"
      required={true}
      disabled={loading}
      minlength={8}
      bind:value={formData.password}
      error={errors.password}
      helpText="Minimum 8 caractères avec majuscules, minuscules, chiffres et caractères spéciaux"
      showStrengthIndicator={true}
      strengthData={passwordStrength}
      on:input={handlePasswordInput}
    />

    <!-- Confirm Password Field -->
    <PasswordConfirmInput
      id="confirmPassword"
      name="confirmPassword"
      label="Confirmer le mot de passe"
      placeholder="Confirmer le mot de passe"
      required={true}
      disabled={loading}
      bind:value={formData.confirmPassword}
      originalPassword={formData.password}
      error={errors.confirmPassword}
      helpText="Retapez votre mot de passe pour confirmation"
      on:input={handleConfirmPasswordInput}
      on:blur={(e) => validateField('confirmPassword', e.detail.value)}
    />
  </div>

  <!-- Terms and Conditions -->
  <fieldset class="space-y-3">
    <legend class="text-sm font-medium text-gray-700">Conditions et préférences</legend>

    <CheckboxField
      id="acceptTerms"
      name="acceptTerms"
      required={true}
      disabled={loading}
      bind:checked={formData.acceptTerms}
      error={errors.acceptTerms}
      helpText="Vous devez accepter les conditions pour créer un compte"
      on:change={(e) => validateField('acceptTerms', e.detail.checked)}
    >
      <span slot="label">
        J'accepte les <a href="/terms" target="_blank" class="text-success-600 hover:text-success-500 underline">conditions d'utilisation</a> et la <a href="/privacy" target="_blank" class="text-success-600 hover:text-success-500 underline">politique de confidentialité</a>
      </span>
    </CheckboxField>

    <CheckboxField
      id="subscribeNewsletter"
      name="subscribeNewsletter"
      label="Je souhaite recevoir la newsletter avec les dernières nouvelles et mises à jour de WakeDock"
      disabled={loading}
      bind:checked={formData.subscribeNewsletter}
      helpText="Optionnel - Vous pouvez vous désinscrire à tout moment"
    />
  </fieldset>

  <!-- Submit Button -->
  <div>
    <button
      type="submit"
      disabled={loading || isRateLimited}
      class="group relative flex w-full justify-center rounded-md border border-transparent bg-green-600 py-2 px-4 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      aria-describedby="submit-help"
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
        Création du compte...
      {:else}
        Créer le compte
      {/if}
    </button>
    <p id="submit-help" class="mt-2 text-sm text-gray-500 text-center">
      En créant un compte, vous acceptez nos conditions d'utilisation
    </p>
  </div>
</form>