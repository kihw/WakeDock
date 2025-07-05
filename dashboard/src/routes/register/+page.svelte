<!-- Page d'inscription refactorisée -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { isAuthenticated } from '$lib/stores/auth';
  import { toastStore } from '$lib/stores/toastStore';
  import { api } from '$lib/api';
  import { uiLogger } from '$lib/utils/logger';
  import { announceToScreenReader } from '$lib/utils/accessibility';
  
  import RegisterForm from '$lib/components/auth/RegisterForm/RegisterForm.svelte';

  let loading = false;

  // Rediriger si déjà connecté
  onMount(() => {
    const unsubscribe = isAuthenticated.subscribe((authenticated) => {
      if (authenticated) {
        goto('/');
      }
    });

    // Ajouter gestionnaire d'erreur global pour les extensions d'autofill
    const handleGlobalError = (event: ErrorEvent) => {
      if (event.error && event.error.message) {
        const errorMessage = event.error.message.toLowerCase();
        if (
          errorMessage.includes('autofill') ||
          errorMessage.includes('bootstrap-autofill') ||
          errorMessage.includes('extension context invalidated') ||
          errorMessage.includes('cannot read properties of null')
        ) {
          event.preventDefault();
          console.debug('Autofill extension error ignored:', event.error.message);
          return false;
        }
      }
    };

    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', (event) => {
      const reason = event.reason;
      if (reason && typeof reason === 'object' && reason.message) {
        const errorMessage = reason.message.toLowerCase();
        if (
          errorMessage.includes('autofill') ||
          errorMessage.includes('bootstrap-autofill') ||
          errorMessage.includes('extension context invalidated')
        ) {
          event.preventDefault();
          console.debug('Autofill promise rejection ignored:', reason.message);
          return false;
        }
      }
    });

    return () => {
      unsubscribe();
      window.removeEventListener('error', handleGlobalError);
    };
  });

  // Gestionnaire de soumission du formulaire
  async function handleRegisterSubmit(event: CustomEvent<{ formData: any }>) {
    const { formData } = event.detail;
    loading = true;

    try {
      const userData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        role: 'user',
        is_active: true,
        subscribe_newsletter: Boolean(formData.subscribeNewsletter),
        _csrf: formData._csrf,
      };

      const newUser = await api.users.create(userData);

      // Effacer les données sensibles immédiatement
      formData.password = '';

      toastStore.addToast({
        type: 'success',
        message: 'Compte créé avec succès! Un email de vérification a été envoyé à votre adresse.',
      });

      toastStore.addToast({
        type: 'info',
        message: 'Veuillez vérifier votre email avant de vous connecter.',
        persistent: true,
      });

      announceToScreenReader(
        'Account created successfully! Please check your email for verification instructions.'
      );

      goto('/login?registered=true');
    } catch (error: any) {
      uiLogger.error('Register', error, {
        context: 'registration',
        formData: { ...formData, password: '[REDACTED]' },
      });

      // Gérer les erreurs spécifiques
      let errorMessage = error.message || "Erreur lors de l'inscription. Veuillez réessayer.";
      
      if (error.code === 'VALIDATION_ERROR') {
        if (error.details?.username) {
          errorMessage = "Ce nom d'utilisateur est déjà pris";
        } else if (error.details?.email) {
          errorMessage = 'Cet email est déjà utilisé';
        }
      } else if (error.code === 'USER_EXISTS') {
        if (error.message.includes('username')) {
          errorMessage = "Ce nom d'utilisateur est déjà pris";
        } else if (error.message.includes('email')) {
          errorMessage = 'Cet email est déjà utilisé';
        }
      } else if (error.code === 'RATE_LIMITED') {
        errorMessage = 'Too many requests. Please wait before trying again.';
      }

      toastStore.addToast({
        type: 'error',
        message: errorMessage,
      });

      announceToScreenReader(`Registration failed: ${errorMessage}`);
    } finally {
      loading = false;
    }
  }

  // Gestionnaire du lien de navigation
  function handleSkipLink() {
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      mainContent.focus();
    }
  }
</script>

<svelte:head>
  <title>Inscription - WakeDock</title>
  <meta name="description" content="Créez votre compte WakeDock pour gérer vos containers Docker" />
  <meta name="robots" content="noindex, nofollow" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <meta http-equiv="X-Content-Type-Options" content="nosniff" />
  <meta http-equiv="X-XSS-Protection" content="1; mode=block" />
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
<div class="sr-only" aria-live="polite" aria-atomic="true"></div>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
  <div class="max-w-md w-full space-y-8">
    <!-- Header -->
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

    <!-- Main Content -->
    <main id="main-content">
      <RegisterForm {loading} on:submit={handleRegisterSubmit} />
    </main>

    <!-- Footer -->
    <div class="text-center">
      <p class="text-sm text-gray-600">
        Vous avez déjà un compte?
        <a href="/login" class="font-medium text-green-600 hover:text-green-500">
          Se connecter
        </a>
      </p>
    </div>
  </div>
</div>