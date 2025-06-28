<!-- Base Modal Component -->
<script lang="ts">
    import { createEventDispatcher, onMount } from "svelte";

    export let open: boolean = false;
    export let size: "sm" | "md" | "lg" | "xl" | "full" = "md";
    export let persistent: boolean = false; // Prevent closing on backdrop click
    export let showCloseButton: boolean = true;
    export let title: string = "";
    export let closeOnEscape: boolean = true;

    const dispatch = createEventDispatcher<{
        close: void;
        open: void;
    }>();

    // Size classes
    const sizeClasses = {
        sm: "max-w-sm",
        md: "max-w-md",
        lg: "max-w-lg",
        xl: "max-w-4xl",
        full: "max-w-full mx-4",
    };

    let modalElement: HTMLDivElement;

    onMount(() => {
        // Only run in browser (not during SSR)
        if (typeof window !== "undefined" && typeof document !== "undefined") {
            // Focus trap and escape key handling
            const handleKeydown = (event: KeyboardEvent) => {
                if (open && closeOnEscape && event.key === "Escape") {
                    handleClose();
                }
            };

            document.addEventListener("keydown", handleKeydown);

            return () => {
                document.removeEventListener("keydown", handleKeydown);
            };
        }
    });

    const handleBackdropClick = (event: MouseEvent) => {
        if (!persistent && event.target === event.currentTarget) {
            handleClose();
        }
    };

    const handleClose = () => {
        if (open) {
            open = false;
            dispatch("close");
        }
    };

    const handleOpen = () => {
        if (!open) {
            open = true;
            dispatch("open");
        }
    };

    // Reactive statement to handle open/close
    $: if (open) {
        // Prevent body scroll when modal is open
        document.body.style.overflow = "hidden";
    } else {
        // Restore body scroll
        document.body.style.overflow = "";
    }

    // Cleanup on destroy
    import { onDestroy } from "svelte";
    onDestroy(() => {
        document.body.style.overflow = "";
    });
</script>

{#if open}
    <!-- Backdrop -->
    <div
        class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4"
        on:click={handleBackdropClick}
        bind:this={modalElement}
        role="dialog"
        aria-modal="true"
    >
        <!-- Modal Content -->
        <div
            class="relative bg-white rounded-lg shadow-xl {sizeClasses[
                size
            ]} w-full max-h-full overflow-hidden"
            on:click|stopPropagation
        >
            <!-- Header -->
            {#if title || showCloseButton || $$slots.header}
                <div
                    class="flex items-center justify-between p-6 border-b border-gray-200"
                >
                    <div class="flex items-center">
                        {#if $$slots.header}
                            <slot name="header" />
                        {:else if title}
                            <h3 class="text-lg font-medium text-gray-900">
                                {title}
                            </h3>
                        {/if}
                    </div>

                    {#if showCloseButton}
                        <button
                            type="button"
                            class="text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition ease-in-out duration-150"
                            on:click={handleClose}
                            aria-label="Close modal"
                        >
                            <svg
                                class="h-6 w-6"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        </button>
                    {/if}
                </div>
            {/if}

            <!-- Body -->
            <div class="p-6 overflow-y-auto max-h-96">
                <slot />
            </div>

            <!-- Footer -->
            {#if $$slots.footer}
                <div
                    class="flex items-center justify-end px-6 py-4 bg-gray-50 border-t border-gray-200"
                >
                    <slot name="footer" />
                </div>
            {/if}
        </div>
    </div>
{/if}
