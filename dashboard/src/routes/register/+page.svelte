<!-- Page d'inscription -->
<script>
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { isAuthenticated } from "$lib/stores/auth";
    import { toastStore } from "$lib/stores/toastStore";

    let formData = {
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
        full_name: "",
    };
    let loading = false;
    let errors = {};

    // Rediriger si déjà connecté
    onMount(() => {
        const unsubscribe = isAuthenticated.subscribe((authenticated) => {
            if (authenticated) {
                goto("/");
            }
        });

        return unsubscribe;
    });

    function validateForm() {
        errors = {};

        if (!formData.username) {
            errors.username = "Le nom d'utilisateur est requis";
        } else if (formData.username.length < 3) {
            errors.username =
                "Le nom d'utilisateur doit contenir au moins 3 caractères";
        }

        if (!formData.email) {
            errors.email = "L'email est requis";
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            errors.email = "Format d'email invalide";
        }

        if (!formData.password) {
            errors.password = "Le mot de passe est requis";
        } else if (formData.password.length < 8) {
            errors.password =
                "Le mot de passe doit contenir au moins 8 caractères";
        }

        if (formData.password !== formData.confirmPassword) {
            errors.confirmPassword = "Les mots de passe ne correspondent pas";
        }

        if (!formData.full_name) {
            errors.full_name = "Le nom complet est requis";
        }

        return Object.keys(errors).length === 0;
    }

    async function handleRegister() {
        if (!validateForm()) {
            return;
        }

        loading = true;

        try {
            const response = await fetch("/api/v1/auth/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username: formData.username,
                    email: formData.email,
                    password: formData.password,
                    full_name: formData.full_name,
                    role: "user", // Par défaut
                    is_active: true,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 400) {
                    // Gérer les erreurs spécifiques du backend
                    if (data.detail.includes("username")) {
                        errors.username = "Ce nom d'utilisateur est déjà pris";
                    } else if (data.detail.includes("email")) {
                        errors.email = "Cet email est déjà utilisé";
                    } else {
                        errors.general = data.detail;
                    }
                } else {
                    errors.general =
                        data.detail || "Erreur lors de l'inscription";
                }
                return;
            }

            toastStore.addToast({
                type: "success",
                message:
                    "Compte créé avec succès! Vous pouvez maintenant vous connecter.",
            });

            // Rediriger vers la page de connexion
            goto("/login");
        } catch (err) {
            errors.general = "Erreur de connexion au serveur";
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Inscription - WakeDock</title>
</svelte:head>

<div
    class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8"
>
    <div class="max-w-md w-full space-y-8">
        <div>
            <div
                class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-green-100"
            >
                <svg
                    class="h-8 w-8 text-green-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                    />
                </svg>
            </div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Créer un compte WakeDock
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600">
                Rejoignez la plateforme de gestion Docker
            </p>
        </div>

        <form class="mt-8 space-y-6" on:submit|preventDefault={handleRegister}>
            {#if errors.general}
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
                                Erreur
                            </h3>
                            <div class="mt-2 text-sm text-red-700">
                                {errors.general}
                            </div>
                        </div>
                    </div>
                </div>
            {/if}

            <div class="space-y-4">
                <div>
                    <label for="full_name" class="sr-only">Nom complet</label>
                    <input
                        id="full_name"
                        name="full_name"
                        type="text"
                        required
                        bind:value={formData.full_name}
                        class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-green-500 focus:outline-none focus:ring-green-500 sm:text-sm {errors.full_name
                            ? 'border-red-500'
                            : ''}"
                        placeholder="Nom complet"
                        disabled={loading}
                    />
                    {#if errors.full_name}
                        <p class="mt-1 text-sm text-red-600">
                            {errors.full_name}
                        </p>
                    {/if}
                </div>

                <div>
                    <label for="username" class="sr-only"
                        >Nom d'utilisateur</label
                    >
                    <input
                        id="username"
                        name="username"
                        type="text"
                        required
                        bind:value={formData.username}
                        class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-green-500 focus:outline-none focus:ring-green-500 sm:text-sm {errors.username
                            ? 'border-red-500'
                            : ''}"
                        placeholder="Nom d'utilisateur"
                        disabled={loading}
                    />
                    {#if errors.username}
                        <p class="mt-1 text-sm text-red-600">
                            {errors.username}
                        </p>
                    {/if}
                </div>

                <div>
                    <label for="email" class="sr-only">Email</label>
                    <input
                        id="email"
                        name="email"
                        type="email"
                        required
                        bind:value={formData.email}
                        class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-green-500 focus:outline-none focus:ring-green-500 sm:text-sm {errors.email
                            ? 'border-red-500'
                            : ''}"
                        placeholder="Adresse email"
                        disabled={loading}
                    />
                    {#if errors.email}
                        <p class="mt-1 text-sm text-red-600">{errors.email}</p>
                    {/if}
                </div>

                <div>
                    <label for="password" class="sr-only">Mot de passe</label>
                    <input
                        id="password"
                        name="password"
                        type="password"
                        required
                        bind:value={formData.password}
                        class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-green-500 focus:outline-none focus:ring-green-500 sm:text-sm {errors.password
                            ? 'border-red-500'
                            : ''}"
                        placeholder="Mot de passe (min. 8 caractères)"
                        disabled={loading}
                    />
                    {#if errors.password}
                        <p class="mt-1 text-sm text-red-600">
                            {errors.password}
                        </p>
                    {/if}
                </div>

                <div>
                    <label for="confirmPassword" class="sr-only"
                        >Confirmer le mot de passe</label
                    >
                    <input
                        id="confirmPassword"
                        name="confirmPassword"
                        type="password"
                        required
                        bind:value={formData.confirmPassword}
                        class="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-green-500 focus:outline-none focus:ring-green-500 sm:text-sm {errors.confirmPassword
                            ? 'border-red-500'
                            : ''}"
                        placeholder="Confirmer le mot de passe"
                        disabled={loading}
                    />
                    {#if errors.confirmPassword}
                        <p class="mt-1 text-sm text-red-600">
                            {errors.confirmPassword}
                        </p>
                    {/if}
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
                    <a
                        href="/login"
                        class="font-medium text-green-600 hover:text-green-500"
                    >
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
