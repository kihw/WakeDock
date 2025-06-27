<!-- Confirmation Modal Component -->
<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import Modal from "./Modal.svelte";
    import { Button } from "../forms";

    export let open: boolean = false;
    export let title: string = "Confirm Action";
    export let message: string =
        "Are you sure you want to perform this action?";
    export let confirmText: string = "Confirm";
    export let cancelText: string = "Cancel";
    export let confirmVariant: "primary" | "danger" | "success" | "warning" =
        "primary";
    export let loading: boolean = false;
    export let persistent: boolean = false;

    const dispatch = createEventDispatcher<{
        confirm: void;
        cancel: void;
        close: void;
    }>();

    const handleConfirm = () => {
        dispatch("confirm");
    };

    const handleCancel = () => {
        open = false;
        dispatch("cancel");
    };

    const handleClose = () => {
        if (!loading) {
            open = false;
            dispatch("close");
        }
    };
</script>

<Modal
    bind:open
    size="sm"
    {persistent}
    showCloseButton={!loading}
    closeOnEscape={!loading}
    on:close={handleClose}
>
    <div slot="header" class="flex items-center">
        {#if confirmVariant === "danger"}
            <div
                class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-red-100 mr-3"
            >
                <svg
                    class="h-6 w-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
            </div>
        {:else if confirmVariant === "warning"}
            <div
                class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-yellow-100 mr-3"
            >
                <svg
                    class="h-6 w-6 text-yellow-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
            </div>
        {:else if confirmVariant === "success"}
            <div
                class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-green-100 mr-3"
            >
                <svg
                    class="h-6 w-6 text-green-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M5 13l4 4L19 7"
                    />
                </svg>
            </div>
        {:else}
            <div
                class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-blue-100 mr-3"
            >
                <svg
                    class="h-6 w-6 text-blue-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
            </div>
        {/if}
        <h3 class="text-lg font-medium text-gray-900">
            {title}
        </h3>
    </div>

    <div class="text-sm text-gray-500">
        {message}
    </div>

    <div slot="footer" class="flex space-x-3">
        <Button variant="secondary" on:click={handleCancel} disabled={loading}>
            {cancelText}
        </Button>

        <Button
            variant={confirmVariant}
            on:click={handleConfirm}
            {loading}
            disabled={loading}
        >
            {confirmText}
        </Button>
    </div>
</Modal>
