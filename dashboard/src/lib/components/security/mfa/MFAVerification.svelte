<!-- MFA Verification Component for Login -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';

  export let username: string = '';
  export let isLoading: boolean = false;

  const dispatch = createEventDispatcher<{
    verified: { token: string; method: string };
    cancel: void;
    useBackupCode: void;
  }>();

  let mfaToken = '';
  let useBackupCode = false;
  let backupCode = '';
  let verificationError = '';
  let remainingAttempts = 3;
  let isVerifying = false;

  async function verifyMFA() {
    const token = useBackupCode ? backupCode : mfaToken;

    if (!token || token.trim().length === 0) {
      verificationError = useBackupCode
        ? 'Veuillez entrer un code de récupération'
        : "Veuillez entrer le code d'authentification";
      return;
    }

    if (!useBackupCode && token.length !== 6) {
      verificationError = 'Le code doit contenir 6 chiffres';
      return;
    }

    if (useBackupCode && token.replace(/[-\s]/g, '').length !== 8) {
      verificationError = 'Le code de récupération doit contenir 8 caractères';
      return;
    }

    try {
      isVerifying = true;
      verificationError = '';

      const response = await fetch('/api/v1/auth/verify-mfa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          token: token.replace(/[-\s]/g, ''),
          method: useBackupCode ? 'backup_code' : 'totp',
        }),
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Verification failed');
      }

      dispatch('verified', {
        token: token.replace(/[-\s]/g, ''),
        method: useBackupCode ? 'backup_code' : 'totp',
      });
    } catch (error) {
      verificationError = error instanceof Error ? error.message : 'Vérification échouée';
      remainingAttempts--;

      // Clear the input
      if (useBackupCode) {
        backupCode = '';
      } else {
        mfaToken = '';
      }

      // If no attempts left, force logout
      if (remainingAttempts <= 0) {
        setTimeout(() => {
          dispatch('cancel');
        }, 2000);
      }
    } finally {
      isVerifying = false;
    }
  }

  function toggleBackupCode() {
    useBackupCode = !useBackupCode;
    verificationError = '';
    mfaToken = '';
    backupCode = '';
  }

  function formatBackupCode(value: string): string {
    // Remove all non-alphanumeric characters
    const clean = value.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();

    // Add hyphen after 4 characters
    if (clean.length > 4) {
      return clean.slice(0, 4) + '-' + clean.slice(4, 8);
    }
    return clean;
  }

  function handleBackupCodeInput(event: Event) {
    const target = event.target as HTMLInputElement;
    const formatted = formatBackupCode(target.value);
    backupCode = formatted;
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      verifyMFA();
    }
  }
</script>

<div
  class="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8"
  in:scale={{ duration: 300, easing: quintOut }}
>
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
    <h2 class="text-2xl font-bold text-gray-900 mb-2">Authentification à deux facteurs</h2>
    <p class="text-gray-600">
      {#if useBackupCode}
        Entrez un code de récupération
      {:else}
        Entrez le code depuis votre application
      {/if}
    </p>
    <p class="text-sm text-gray-500 mt-1">Connecté en tant que: <strong>{username}</strong></p>
  </div>

  <!-- Verification Form -->
  <form on:submit|preventDefault={verifyMFA} class="space-y-6">
    {#if !useBackupCode}
      <!-- TOTP Code Input -->
      <div>
        <label for="mfa-token" class="block text-sm font-medium text-gray-700 mb-2">
          Code d'authentification
        </label>
        <input
          id="mfa-token"
          bind:value={mfaToken}
          type="text"
          placeholder="000000"
          maxlength="6"
          pattern="[0-9]{6}"
          autocomplete="one-time-code"
          class="w-full text-center text-2xl font-mono px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          class:border-red-500={verificationError}
          on:keydown={handleKeyDown}
        />
        <p class="text-xs text-gray-500 mt-1">Entrez le code à 6 chiffres de votre application</p>
      </div>
    {:else}
      <!-- Backup Code Input -->
      <div>
        <label for="backup-code" class="block text-sm font-medium text-gray-700 mb-2">
          Code de récupération
        </label>
        <input
          id="backup-code"
          bind:value={backupCode}
          type="text"
          placeholder="XXXX-XXXX"
          maxlength="9"
          class="w-full text-center text-xl font-mono px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          class:border-red-500={verificationError}
          on:input={handleBackupCodeInput}
          on:keydown={handleKeyDown}
        />
        <p class="text-xs text-gray-500 mt-1">Format: XXXX-XXXX</p>
      </div>
    {/if}

    <!-- Error Message -->
    {#if verificationError}
      <div class="bg-red-50 border border-red-200 rounded-md p-3" in:fade>
        <div class="flex">
          <svg
            class="w-5 h-5 text-red-600 mr-2 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <p class="text-sm text-red-700">{verificationError}</p>
            {#if remainingAttempts > 0}
              <p class="text-xs text-red-600 mt-1">Tentatives restantes: {remainingAttempts}</p>
            {:else}
              <p class="text-xs text-red-600 mt-1">Redirection en cours...</p>
            {/if}
          </div>
        </div>
      </div>
    {/if}

    <!-- Submit Button -->
    <button
      type="submit"
      disabled={isVerifying ||
        remainingAttempts <= 0 ||
        (!useBackupCode && mfaToken.length !== 6) ||
        (useBackupCode && backupCode.replace(/[-\s]/g, '').length !== 8)}
      class="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200"
    >
      {#if isVerifying}
        <span class="flex items-center justify-center">
          <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
          Vérification...
        </span>
      {:else}
        Vérifier
      {/if}
    </button>
  </form>

  <!-- Alternative Options -->
  <div class="mt-6 pt-6 border-t border-gray-200 space-y-3">
    <!-- Toggle Backup Code -->
    <button
      type="button"
      on:click={toggleBackupCode}
      class="w-full text-center text-sm text-blue-600 hover:text-blue-700 transition-colors"
    >
      {#if useBackupCode}
        🔢 Utiliser le code de l'application
      {:else}
        🔑 Utiliser un code de récupération
      {/if}
    </button>

    <!-- Cancel -->
    <button
      type="button"
      on:click={() => dispatch('cancel')}
      class="w-full text-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
    >
      Annuler et se déconnecter
    </button>
  </div>

  <!-- Help Info -->
  <div class="mt-6 p-4 bg-gray-50 rounded-lg">
    <h4 class="text-sm font-medium text-gray-900 mb-2">💡 Besoin d'aide ?</h4>
    <ul class="text-xs text-gray-600 space-y-1">
      <li>• Vérifiez que l'heure de votre téléphone est correcte</li>
      <li>• Assurez-vous d'avoir la dernière version de l'application</li>
      <li>• Les codes de récupération ne peuvent être utilisés qu'une seule fois</li>
    </ul>
  </div>
</div>
