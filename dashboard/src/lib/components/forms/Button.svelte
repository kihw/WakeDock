<!-- Button Component -->
<script lang="ts">
    export let type: "button" | "submit" | "reset" = "button";
    export let variant:
        | "primary"
        | "secondary"
        | "danger"
        | "success"
        | "warning"
        | "ghost" = "primary";
    export let size: "xs" | "sm" | "md" | "lg" | "xl" = "md";
    export let disabled: boolean = false;
    export let loading: boolean = false;
    export let fullWidth: boolean = false;
    export let href: string = "";
    export let target: string = "";
    export let download: string = "";

    // Variant classes
    const variantClasses = {
        primary:
            "text-white bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 border-transparent",
        secondary:
            "text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500 border-gray-300",
        danger: "text-white bg-red-600 hover:bg-red-700 focus:ring-red-500 border-transparent",
        success:
            "text-white bg-green-600 hover:bg-green-700 focus:ring-green-500 border-transparent",
        warning:
            "text-white bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500 border-transparent",
        ghost: "text-gray-500 bg-transparent hover:text-gray-700 hover:bg-gray-100 focus:ring-gray-500 border-transparent",
    };

    // Size classes
    const sizeClasses = {
        xs: "px-2.5 py-1.5 text-xs",
        sm: "px-3 py-2 text-sm leading-4",
        md: "px-4 py-2 text-sm",
        lg: "px-4 py-2 text-base",
        xl: "px-6 py-3 text-base",
    };

    // Base classes
    const baseClasses =
        "inline-flex items-center justify-center border font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200";

    // Compute classes
    $: classes = [
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        fullWidth ? "w-full" : "",
        loading ? "cursor-wait" : "",
    ]
        .filter(Boolean)
        .join(" ");

    // Handle click for non-form buttons
    const handleClick = (event: MouseEvent) => {
        if (disabled || loading) {
            event.preventDefault();
            return;
        }
        // Dispatch custom click event
    };
</script>

{#if href}
    <a
        {href}
        {target}
        {download}
        class={classes}
        class:pointer-events-none={disabled || loading}
        on:click={handleClick}
    >
        {#if loading}
            <svg
                class="animate-spin -ml-1 mr-2 h-4 w-4"
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
        {/if}
        <slot />
    </a>
{:else}
    <button
        {type}
        {disabled}
        class={classes}
        on:click={handleClick}
        on:submit
        on:focus
        on:blur
    >
        {#if loading}
            <svg
                class="animate-spin -ml-1 mr-2 h-4 w-4"
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
        {/if}
        <slot />
    </button>
{/if}
