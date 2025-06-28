<!-- Page de connexion -->
<script>
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { page } from "$app/stores";
    import { auth, isAuthenticated } from "$lib/stores/auth";
    import { toastStore } from "$lib/stores/toastStore";

    let username = "";
    let password = "";
    let loading = false;
    let error = "";

    // Rediriger si déjà connecté
    onMount(() => {
        const unsubscribe = isAuthenticated.subscribe((authenticated) => {
            if (authenticated) {
                const redirectTo =
                    $page.url.searchParams.get("redirect") || "/";
                goto(redirectTo);
            }
        });

        return unsubscribe;
    });

    async function handleLogin() {
        if (!username || !password) {
            error = "Veuillez remplir tous les champs";
            return;
        }

        loading = true;
        error = "";

        try {
            await auth.login(username, password);

            toastStore.success(`Bienvenue ${username}!`);

            // Redirection après connexion réussie
            const redirectTo = $page.url.searchParams.get("redirect") || "/";
            goto(redirectTo);
        } catch (err) {
            error = err.message || "Erreur de connexion";
            toastStore.error(error);
        } finally {
            loading = false;
        }
    }

    function handleKeyDown(event) {
        if (event.key === "Enter") {
            handleLogin();
        }
    }
</script>

<svelte:head>
    <title>Connexion - WakeDock</title>
</svelte:head>

<div
    class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8"
>
    <div class="max-w-md w-full space-y-8">
        <div>
            <div
                class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100"
            >
                <svg
                    class="h-8 w-8 text-blue-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                </svg>
            </div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Connexion à WakeDock
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600">
                Gérez vos conteneurs Docker en toute simplicité
            </p>
        </div>

        <form class="mt-8 space-y-6" on:submit|preventDefault={handleLogin}>
            <div class="space-y-4">
                <div>
                    <label for="username" class="sr-only"
                        >Nom d'utilisateur</label
                    >
                    <input
                        id="username"
                        name="username"
                        type="text"
                        required
                        bind:value={username}
                        on:keydown={handleKeyDown}
                        class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                        placeholder="Nom d'utilisateur"
                        disabled={loading}
                    />
                </div>
                <div>
                    <label for="password" class="sr-only">Mot de passe</label>
                    <input
                        id="password"
                        name="password"
                        type="password"
                        required
                        bind:value={password}
                        on:keydown={handleKeyDown}
                        class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                        placeholder="Mot de passe"
                        disabled={loading}
                    />
                </div>
            </div>

            {#if error}
                <div class="rounded-md bg-red-50 p-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg
                                class="h-5 w-5 text-red-400"
                                viewBox="0 0 20 20"
                                fill="currentColor"
                            >
                                <path
                                    fill-rule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                    clip-rule="evenodd"
                                />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-sm font-medium text-red-800">
                                Erreur de connexion
                            </h3>
                            <div class="mt-2 text-sm text-red-700">
                                {error}
                            </div>
                        </div>
                    </div>
                </div>
            {/if}

            <div>
                <button
                    type="submit"
                    disabled={loading}
                    class="group relative flex w-full justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
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
                        Connexion...
                    {:else}
                        Se connecter
                    {/if}
                </button>
            </div>

            <div class="text-center">
                <p class="text-sm text-gray-600">
                    Pas encore de compte?
                    <a
                        href="/register"
                        class="font-medium text-blue-600 hover:text-blue-500"
                    >
                        Créer un compte
                    </a>
                </p>
            </div>
        </form>
    </div>
</div>

<style>
    /* Style pour améliorer l'apparence */
    input:focus {
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
</style>
