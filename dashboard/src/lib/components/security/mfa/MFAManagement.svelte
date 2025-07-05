<!-- MFA Management Component for Settings -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import MFASetup from './MFASetup.svelte';

  export let userEmail: string = '';
  export let mfaEnabled: boolean = false;
  export let isLoading: boolean = false;

  const dispatch = createEventDispatcher<{
    mfaEnabled: { enabled: boolean };
    mfaDisabled: void;
    codesRegenerated: { codes: string[] };
  }>();

  let showSetup = false;
  let showDisableConfirm = false;
  let showRegenerateConfirm = false;
  let newBackupCodes: string[] = [];
  let showNewCodes = false;
  let actionError = '';
  let isProcessing = false;

  async function enableMFA() {
    showSetup = true;
    actionError = '';
  }

  async function disableMFA() {
    try {
      isProcessing = true;
      actionError = '';

      const response = await fetch('/api/v1/auth/mfa/disable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to disable MFA');
      }

      mfaEnabled = false;
      showDisableConfirm = false;
      dispatch('mfaDisabled');
    } catch (error) {
      actionError = error instanceof Error ? error.message : 'Failed to disable MFA';
    } finally {
      isProcessing = false;
    }
  }

  async function regenerateBackupCodes() {
    try {
      isProcessing = true;
      actionError = '';

      const response = await fetch('/api/v1/auth/mfa/regenerate-codes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to regenerate codes');
      }

      const data = await response.json();
      newBackupCodes = data.backup_codes;
      showNewCodes = true;
      showRegenerateConfirm = false;

      dispatch('codesRegenerated', { codes: newBackupCodes });
    } catch (error) {
      actionError = error instanceof Error ? error.message : 'Failed to regenerate codes';
    } finally {
      isProcessing = false;
    }
  }

  function handleMFASetupComplete(event: CustomEvent) {
    mfaEnabled = true;
    showSetup = false;
    dispatch('mfaEnabled', { enabled: true });
  }

  function handleMFASetupCancel() {
    showSetup = false;
    actionError = '';
  }

  function downloadNewCodes() {
    const content = [
      'WakeDock - Nouveaux codes de récupération 2FA',
      '============================================',
      '',
      "Conservez ces codes en lieu sûr. Chaque code ne peut être utilisé qu'une seule fois.",
      'Ces codes remplacent vos anciens codes de récupération.',
      '',
      ...newBackupCodes.map((code, index) => `${index + 1}. ${code}`),
      '',
      `Générés le: ${new Date().toLocaleString()}`,
      `Utilisateur: ${userEmail}`,
    ].join('\\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wakedock-new-backup-codes-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

{#if showSetup}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" in:fade>
    <div class="max-w-4xl w-full mx-4">
      <MFASetup {userEmail} on:setup={handleMFASetupComplete} on:cancel={handleMFASetupCancel} />
    </div>
  </div>
{/if}

{#if showNewCodes}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" in:fade>
    <div class="bg-white rounded-lg shadow-lg p-6 max-w-lg w-full mx-4">
      <div class="text-center mb-6">
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
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Nouveaux codes générés</h3>
        <p class="text-gray-600">Vos nouveaux codes de récupération ont été générés avec succès.</p>
      </div>

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
            <h4 class="font-medium text-yellow-800 mb-1">Important</h4>
            <p class="text-sm text-yellow-700">
              Ces nouveaux codes remplacent vos anciens codes. Assurez-vous de les sauvegarder avant
              de fermer cette fenêtre.
            </p>
          </div>
        </div>
      </div>

      <div class="bg-gray-50 p-4 rounded-lg mb-6">
        <div class="grid grid-cols-2 gap-2 font-mono text-sm">
          {#each newBackupCodes as code}
            <div class="bg-white p-2 rounded border text-center">{code}</div>
          {/each}
        </div>
      </div>

      <div class="flex justify-center space-x-4">
        <button
          on:click={downloadNewCodes}
          class="border border-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-50 transition-colors"
        >
          📥 Télécharger
        </button>
        <button
          on:click={() => (showNewCodes = false)}
          class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          J'ai sauvegardé les codes
        </button>
      </div>
    </div>
  </div>
{/if}

<div class="bg-white rounded-lg shadow p-6">
  <div class="flex items-center justify-between mb-6">
    <div>
      <h3 class="text-lg font-medium text-gray-900">Authentification à deux facteurs</h3>
      <p class="text-sm text-gray-600 mt-1">
        Ajoutez une couche de sécurité supplémentaire à votre compte
      </p>
    </div>
    <div class="flex items-center">
      <span class="text-sm text-gray-500 mr-3">
        {mfaEnabled ? 'Activé' : 'Désactivé'}
      </span>
      <div
        class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
        class:bg-blue-600={mfaEnabled}
        class:bg-gray-200={!mfaEnabled}
      >
        <span
          class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
          class:translate-x-6={mfaEnabled}
          class:translate-x-1={!mfaEnabled}
        ></span>
      </div>
    </div>
  </div>

  {#if actionError}
    <div class="bg-red-50 border border-red-200 rounded-md p-3 mb-6" in:slide>
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
        <p class="text-sm text-red-700">{actionError}</p>
      </div>
    </div>
  {/if}

  {#if !mfaEnabled}
    <!-- MFA Not Enabled -->
    <div class="border border-gray-200 rounded-lg p-6">
      <div class="text-center">
        <div
          class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>
        <h4 class="text-lg font-medium text-gray-900 mb-2">2FA non configuré</h4>
        <p class="text-gray-600 mb-6">
          Protégez votre compte avec l'authentification à deux facteurs. Cette fonctionnalité ajoute
          une couche de sécurité supplémentaire à votre connexion.
        </p>

        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h5 class="font-medium text-blue-900 mb-2">Avantages de la 2FA :</h5>
          <ul class="text-sm text-blue-800 space-y-1 text-left">
            <li>✓ Protection contre les accès non autorisés</li>
            <li>✓ Sécurité renforcée même si votre mot de passe est compromis</li>
            <li>✓ Codes de récupération en cas de perte de téléphone</li>
            <li>✓ Compatible avec les applications d'authentification populaires</li>
          </ul>
        </div>

        <button
          on:click={enableMFA}
          disabled={isLoading || isProcessing}
          class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {#if isProcessing}
            <span class="flex items-center">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Configuration...
            </span>
          {:else}
            Configurer la 2FA
          {/if}
        </button>
      </div>
    </div>
  {:else}
    <!-- MFA Enabled -->
    <div class="space-y-6">
      <!-- Status -->
      <div class="flex items-center p-4 bg-green-50 border border-green-200 rounded-lg">
        <svg
          class="w-5 h-5 text-green-600 mr-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div>
          <p class="font-medium text-green-900">2FA activé</p>
          <p class="text-sm text-green-700">
            Votre compte est protégé par l'authentification à deux facteurs
          </p>
        </div>
      </div>

      <!-- Actions -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Regenerate Backup Codes -->
        <div class="border border-gray-200 rounded-lg p-4">
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
                d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
              />
            </svg>
            <div class="flex-1">
              <h4 class="font-medium text-gray-900 mb-1">Codes de récupération</h4>
              <p class="text-sm text-gray-600 mb-3">
                Générez de nouveaux codes de récupération si vous avez perdu les anciens
              </p>
              <button
                on:click={() => (showRegenerateConfirm = true)}
                disabled={isProcessing}
                class="text-sm bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 disabled:bg-gray-400 transition-colors"
              >
                Régénérer les codes
              </button>
            </div>
          </div>
        </div>

        <!-- Disable MFA -->
        <div class="border border-gray-200 rounded-lg p-4">
          <div class="flex items-start">
            <svg
              class="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0"
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
            <div class="flex-1">
              <h4 class="font-medium text-gray-900 mb-1">Désactiver la 2FA</h4>
              <p class="text-sm text-gray-600 mb-3">
                Supprime la protection 2FA de votre compte (non recommandé)
              </p>
              <button
                on:click={() => (showDisableConfirm = true)}
                disabled={isProcessing}
                class="text-sm bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:bg-gray-400 transition-colors"
              >
                Désactiver la 2FA
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Confirmation Modals -->
  {#if showDisableConfirm}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" in:fade>
      <div class="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <div class="text-center mb-6">
          <div
            class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4"
          >
            <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">Désactiver la 2FA ?</h3>
          <p class="text-gray-600">
            Cette action va supprimer la protection 2FA de votre compte. Votre compte sera moins
            sécurisé.
          </p>
        </div>

        <div class="flex justify-center space-x-4">
          <button
            on:click={() => (showDisableConfirm = false)}
            disabled={isProcessing}
            class="border border-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-50 transition-colors"
          >
            Annuler
          </button>
          <button
            on:click={disableMFA}
            disabled={isProcessing}
            class="bg-red-600 text-white px-6 py-2 rounded-md hover:bg-red-700 disabled:bg-gray-400 transition-colors"
          >
            {#if isProcessing}
              <span class="flex items-center">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Désactivation...
              </span>
            {:else}
              Oui, désactiver
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if showRegenerateConfirm}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" in:fade>
      <div class="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        <div class="text-center mb-6">
          <div
            class="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4"
          >
            <svg
              class="w-8 h-8 text-yellow-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
              />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">Régénérer les codes ?</h3>
          <p class="text-gray-600">
            Cette action va créer de nouveaux codes de récupération et invalider tous vos anciens
            codes.
          </p>
        </div>

        <div class="flex justify-center space-x-4">
          <button
            on:click={() => (showRegenerateConfirm = false)}
            disabled={isProcessing}
            class="border border-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-50 transition-colors"
          >
            Annuler
          </button>
          <button
            on:click={regenerateBackupCodes}
            disabled={isProcessing}
            class="bg-yellow-600 text-white px-6 py-2 rounded-md hover:bg-yellow-700 disabled:bg-gray-400 transition-colors"
          >
            {#if isProcessing}
              <span class="flex items-center">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Génération...
              </span>
            {:else}
              Oui, régénérer
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
