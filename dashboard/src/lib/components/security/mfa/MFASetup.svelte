<!-- MFA Setup Component -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';

  export let userEmail: string = '';
  export let isLoading: boolean = false;

  const dispatch = createEventDispatcher<{
    setup: { secret: string };
    cancel: void;
  }>();

  let currentStep = 1;
  let qrCode = '';
  let secret = '';
  let backupCodes: string[] = [];
  let verificationCode = '';
  let setupError = '';
  let isVerifying = false;
  let setupComplete = false;

  const steps = [
    { number: 1, title: "Installer l'application", icon: '📱' },
    { number: 2, title: 'Scanner le QR code', icon: '📷' },
    { number: 3, title: 'Vérifier le code', icon: '✅' },
    { number: 4, title: 'Sauvegarder les codes', icon: '💾' },
  ];

  async function initializeMFA() {
    try {
      isLoading = true;
      setupError = '';

      const response = await fetch('/api/v1/auth/mfa/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to initialize MFA setup');
      }

      const data = await response.json();
      qrCode = data.qr_code;
      secret = data.secret;
      backupCodes = data.backup_codes;
    } catch (error) {
      setupError = error instanceof Error ? error.message : 'Setup failed';
    } finally {
      isLoading = false;
    }
  }

  async function verifySetup() {
    if (!verificationCode || verificationCode.length !== 6) {
      setupError = 'Please enter a 6-digit code';
      return;
    }

    try {
      isVerifying = true;
      setupError = '';

      const response = await fetch('/api/v1/auth/mfa/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          verification_code: verificationCode,
        }),
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Verification failed');
      }

      setupComplete = true;
      currentStep = 4;
    } catch (error) {
      setupError = error instanceof Error ? error.message : 'Verification failed';
      verificationCode = '';
    } finally {
      isVerifying = false;
    }
  }

  function nextStep() {
    if (currentStep < 4) {
      currentStep++;
    }
  }

  function previousStep() {
    if (currentStep > 1) {
      currentStep--;
    }
  }

  function completeSetup() {
    dispatch('setup', { secret });
  }

  function downloadBackupCodes() {
    const content = [
      'WakeDock - Codes de récupération 2FA',
      '======================================',
      '',
      "Conservez ces codes en lieu sûr. Chaque code ne peut être utilisé qu'une seule fois.",
      '',
      ...backupCodes.map((code, index) => `${index + 1}. ${code}`),
      '',
      `Générés le: ${new Date().toLocaleString()}`,
      `Utilisateur: ${userEmail}`,
    ].join('\\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wakedock-backup-codes-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Initialize on mount
  $: if (userEmail && currentStep === 1) {
    initializeMFA();
  }
</script>

<div class="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
  <!-- Header -->
  <div class="text-center mb-8">
    <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
      <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
    </div>
    <h2 class="text-2xl font-bold text-gray-900 mb-2">
      Configuration de l'authentification à deux facteurs
    </h2>
    <p class="text-gray-600">
      Sécurisez votre compte avec l'authentification à deux facteurs (2FA)
    </p>
  </div>

  <!-- Progress Steps -->
  <div class="flex justify-between mb-8">
    {#each steps as step}
      <div class="flex flex-col items-center">
        <div
          class="w-12 h-12 rounded-full flex items-center justify-center text-sm font-medium transition-colors"
          class:bg-blue-600={currentStep >= step.number}
          class:text-white={currentStep >= step.number}
          class:bg-gray-200={currentStep < step.number}
          class:text-gray-600={currentStep < step.number}
        >
          {#if setupComplete && step.number <= 3}
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
          {:else}
            <span>{step.icon}</span>
          {/if}
        </div>
        <span class="text-xs mt-2 text-center max-w-20">{step.title}</span>
      </div>
    {/each}
  </div>

  <!-- Step Content -->
  <div class="min-h-96">
    {#if currentStep === 1}
      <div in:fade={{ duration: 300 }} class="text-center">
        <h3 class="text-xl font-semibold mb-4">
          Étape 1: Installer une application d'authentification
        </h3>
        <p class="text-gray-600 mb-6">
          Vous devez installer une application d'authentification sur votre téléphone pour générer
          des codes de sécurité.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <!-- Google Authenticator -->
          <div class="border rounded-lg p-4 text-center">
            <div
              class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3"
            >
              <svg class="w-8 h-8 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.017 0L22 6v12l-9.983 6L2 18V6z" />
              </svg>
            </div>
            <h4 class="font-medium mb-2">Google Authenticator</h4>
            <p class="text-sm text-gray-600">Application officielle de Google</p>
          </div>

          <!-- Authy -->
          <div class="border rounded-lg p-4 text-center">
            <div
              class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3"
            >
              <svg class="w-8 h-8 text-red-600" viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z"
                />
              </svg>
            </div>
            <h4 class="font-medium mb-2">Authy</h4>
            <p class="text-sm text-gray-600">Application avec sauvegarde cloud</p>
          </div>

          <!-- Microsoft Authenticator -->
          <div class="border rounded-lg p-4 text-center">
            <div
              class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3"
            >
              <svg class="w-8 h-8 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                <path d="M0 0h11v11H0zm13 0h11v11H13zM0 13h11v11H0zm13 0h11v11H13z" />
              </svg>
            </div>
            <h4 class="font-medium mb-2">Microsoft Authenticator</h4>
            <p class="text-sm text-gray-600">Application Microsoft officielle</p>
          </div>
        </div>

        {#if isLoading}
          <div class="flex justify-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        {:else}
          <button
            on:click={nextStep}
            class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            J'ai installé l'application
          </button>
        {/if}
      </div>
    {:else if currentStep === 2}
      <div in:fade={{ duration: 300 }} class="text-center">
        <h3 class="text-xl font-semibold mb-4">Étape 2: Scanner le QR code</h3>
        <p class="text-gray-600 mb-6">
          Ouvrez votre application d'authentification et scannez ce QR code pour ajouter WakeDock.
        </p>

        {#if qrCode}
          <div class="bg-white p-6 rounded-lg shadow-inner inline-block mb-6">
            <img src={qrCode} alt="QR Code pour configuration 2FA" class="mx-auto" />
          </div>

          <div class="bg-gray-50 p-4 rounded-lg mb-6">
            <p class="text-sm text-gray-600 mb-2">
              Impossible de scanner? Entrez ce code manuellement:
            </p>
            <code class="text-sm font-mono bg-white px-3 py-1 rounded border">{secret}</code>
          </div>
        {/if}

        <div class="flex justify-center space-x-4">
          <button
            on:click={previousStep}
            class="border border-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-50 transition-colors"
          >
            Retour
          </button>
          <button
            on:click={nextStep}
            class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            J'ai scanné le code
          </button>
        </div>
      </div>
    {:else if currentStep === 3}
      <div in:fade={{ duration: 300 }} class="text-center">
        <h3 class="text-xl font-semibold mb-4">Étape 3: Vérifier le code</h3>
        <p class="text-gray-600 mb-6">
          Entrez le code à 6 chiffres affiché dans votre application d'authentification.
        </p>

        <form on:submit|preventDefault={verifySetup} class="max-w-sm mx-auto">
          <div class="mb-6">
            <input
              bind:value={verificationCode}
              type="text"
              placeholder="000000"
              maxlength="6"
              pattern="[0-9]{6}"
              class="w-full text-center text-2xl font-mono px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              class:border-red-500={setupError}
            />
          </div>

          {#if setupError}
            <div class="text-red-600 text-sm mb-4" in:slide>
              {setupError}
            </div>
          {/if}

          <div class="flex justify-center space-x-4">
            <button
              type="button"
              on:click={previousStep}
              class="border border-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-50 transition-colors"
            >
              Retour
            </button>
            <button
              type="submit"
              disabled={isVerifying || verificationCode.length !== 6}
              class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {#if isVerifying}
                <span class="flex items-center">
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Vérification...
                </span>
              {:else}
                Vérifier
              {/if}
            </button>
          </div>
        </form>
      </div>
    {:else if currentStep === 4}
      <div in:fade={{ duration: 300 }} class="text-center">
        <div
          class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>

        <h3 class="text-xl font-semibold mb-4">Configuration terminée!</h3>
        <p class="text-gray-600 mb-6">
          L'authentification à deux facteurs est maintenant activée. Sauvegardez ces codes de
          récupération.
        </p>

        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div class="flex items-start">
            <svg
              class="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <div class="text-left">
              <h4 class="font-medium text-yellow-800 mb-1">Codes de récupération</h4>
              <p class="text-sm text-yellow-700">
                Ces codes vous permettront d'accéder à votre compte si vous perdez votre téléphone.
                Chaque code ne peut être utilisé qu'une seule fois.
              </p>
            </div>
          </div>
        </div>

        <div class="bg-gray-50 p-4 rounded-lg mb-6">
          <div class="grid grid-cols-2 gap-2 font-mono text-sm">
            {#each backupCodes as code}
              <div class="bg-white p-2 rounded border">{code}</div>
            {/each}
          </div>
        </div>

        <div class="flex justify-center space-x-4">
          <button
            on:click={downloadBackupCodes}
            class="border border-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-50 transition-colors"
          >
            📥 Télécharger les codes
          </button>
          <button
            on:click={completeSetup}
            class="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 transition-colors"
          >
            Terminer la configuration
          </button>
        </div>
      </div>
    {/if}
  </div>

  <!-- Cancel Button -->
  <div class="text-center mt-8 pt-6 border-t border-gray-200">
    <button
      on:click={() => dispatch('cancel')}
      class="text-gray-500 hover:text-gray-700 transition-colors"
    >
      Annuler la configuration
    </button>
  </div>
</div>
