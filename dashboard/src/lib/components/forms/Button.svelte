<!-- Button Component -->
<script lang="ts">
    import { manageFocus, announceToScreenReader } from '$lib/utils/accessibility';

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
    export let ariaLabel: string = "";
    export let ariaDescribedBy: string = "";
    export let loadingText: string = "Loading...";
    export let autoFocus: boolean = false;

    // Variant classes with improved focus states
    const variantClasses = {
        primary:
            "text-white bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 border-transparent focus:ring-2 focus:ring-offset-2",
        secondary:
            "text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500 border-gray-300 focus:ring-2 focus:ring-offset-2",
        danger: "text-white bg-red-600 hover:bg-red-700 focus:ring-red-500 border-transparent focus:ring-2 focus:ring-offset-2",
        success:
            "text-white bg-green-600 hover:bg-green-700 focus:ring-green-500 border-transparent focus:ring-2 focus:ring-offset-2",
        warning:
            "text-white bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500 border-transparent focus:ring-2 focus:ring-offset-2",
        ghost: "text-gray-500 bg-transparent hover:text-gray-700 hover:bg-gray-100 focus:ring-gray-500 border-transparent focus:ring-2 focus:ring-offset-2",
    };

    // Size classes
    const sizeClasses = {
        xs: "px-2.5 py-1.5 text-xs",
        sm: "px-3 py-2 text-sm leading-4",
        md: "px-4 py-2 text-sm",
        lg: "px-4 py-2 text-base",
        xl: "px-6 py-3 text-base",
    };

    // Base classes with improved accessibility
    const baseClasses =
        "inline-flex items-center justify-center border font-medium rounded-md shadow-sm focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 relative";

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

    // Handle click with accessibility enhancements
    const handleClick = (event: MouseEvent) => {
        if (disabled || loading) {
            event.preventDefault();
            announceToScreenReader(disabled ? 'Button is disabled' : 'Button is loading, please wait');
            return;
        }
        
        // Announce action to screen readers for important actions
        if (variant === 'danger') {
            announceToScreenReader('Confirming destructive action');
        } else if (type === 'submit') {
            announceToScreenReader('Submitting form');
        }
    };

    // Focus management
    export const focus = () => {
        const button = document.querySelector(`button[aria-label="${ariaLabel}"]`) as HTMLButtonElement;
        if (button) {
            manageFocus(button);
        }
    };

    // Auto-focus if requested
    import { onMount } from 'svelte';
    onMount(() => {
        if (autoFocus) {
            focus();
        }
    });
</script>

{#if href}
    <a
        {href}
        {target}
        {download}
        class={classes}
        class:pointer-events-none={disabled || loading}
        role="button"
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy || undefined}
        aria-disabled={disabled || loading ? 'true' : 'false'}
        tabindex={disabled || loading ? -1 : 0}
        on:click={handleClick}
        on:keydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleClick(e);
            }
        }}
    >
        {#if loading}
            <svg
                class="animate-spin -ml-1 mr-2 h-4 w-4"
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
            <span class="sr-only">{loadingText}</span>
        {/if}
        <slot />
    </a>
{:else}
    <button
        {type}
        disabled={disabled || loading}
        class={classes}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy || undefined}
        aria-disabled={disabled || loading ? 'true' : 'false'}
        on:click={handleClick}
        on:submit
        on:focus
        on:blur
    >
        {#if loading}
            <div class="flex items-center">
                <svg
                    class="animate-spin -ml-1 mr-2 h-4 w-4"
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
                <span class="sr-only">{loadingText}</span>
            </div>
        {/if}
        <slot />
    </button>
{/if}
