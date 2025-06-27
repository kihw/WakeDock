<!-- Textarea Field Component -->
<script lang="ts">
    export let label: string;
    export let id: string = "";
    export let value: string = "";
    export let placeholder: string = "";
    export let required: boolean = false;
    export let disabled: boolean = false;
    export let readonly: boolean = false;
    export let error: string = "";
    export let help: string = "";
    export let rows: number = 4;
    export let maxlength: number | undefined = undefined;
    export let minlength: number | undefined = undefined;
    export let resize: "none" | "vertical" | "horizontal" | "both" = "vertical";
    export let size: "sm" | "md" | "lg" = "md";

    // Textarea sizing classes
    const sizeClasses = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-3 py-2 text-sm",
        lg: "px-4 py-3 text-base",
    };

    // Resize classes
    const resizeClasses = {
        none: "resize-none",
        vertical: "resize-y",
        horizontal: "resize-x",
        both: "resize",
    };

    // Generate unique ID if not provided
    const textareaId =
        id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

    // Handle input event
    const handleInput = (event: Event) => {
        const target = event.target as HTMLTextAreaElement;
        value = target.value;
    };
</script>

<div class="form-field">
    <label
        for={textareaId}
        class="block text-sm font-medium text-gray-700 mb-1"
    >
        {label}
        {#if required}
            <span class="text-red-500 ml-1">*</span>
        {/if}
    </label>

    <div class="relative">
        <textarea
            id={textareaId}
            {placeholder}
            {required}
            {disabled}
            {readonly}
            {rows}
            {maxlength}
            {minlength}
            class="block w-full {sizeClasses[size]} {resizeClasses[
                resize
            ]} border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            class:border-red-300={error}
            class:focus:border-red-500={error}
            class:focus:ring-red-500={error}
            {value}
            on:input={handleInput}
            on:blur
            on:focus
            on:change
            on:keydown
            on:keyup
            on:keypress
        ></textarea>

        {#if error}
            <div class="absolute top-2 right-2 pointer-events-none">
                <svg
                    class="h-5 w-5 text-red-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                >
                    <path
                        fill-rule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                        clip-rule="evenodd"
                    />
                </svg>
            </div>
        {/if}
    </div>

    {#if error}
        <p class="mt-1 text-sm text-red-600">
            {error}
        </p>
    {:else if help}
        <p class="mt-1 text-sm text-gray-500">
            {help}
        </p>
    {/if}
</div>

<style>
    .form-field {
        margin-bottom: 1rem;
    }
</style>
