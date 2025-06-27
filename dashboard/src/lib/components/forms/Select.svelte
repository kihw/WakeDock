<!-- Select Field Component -->
<script lang="ts">
    export let label: string;
    export let id: string = "";
    export let value: string | number = "";
    export let options: Array<{
        value: string | number;
        label: string;
        disabled?: boolean;
    }> = [];
    export let required: boolean = false;
    export let disabled: boolean = false;
    export let error: string = "";
    export let help: string = "";
    export let placeholder: string = "";
    export let size: "sm" | "md" | "lg" = "md";
    export let multiple: boolean = false;

    // Select sizing classes
    const sizeClasses = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-3 py-2 text-sm",
        lg: "px-4 py-3 text-base",
    };

    // Generate unique ID if not provided
    const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;

    // Handle change event
    const handleChange = (event: Event) => {
        const target = event.target as HTMLSelectElement;
        if (multiple) {
            const selectedValues: string[] = [];
            for (const option of target.selectedOptions) {
                selectedValues.push(option.value);
            }
            value = selectedValues;
        } else {
            value = target.value;
        }
    };
</script>

<div class="form-field">
    <label for={selectId} class="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {#if required}
            <span class="text-red-500 ml-1">*</span>
        {/if}
    </label>

    <div class="relative">
        <select
            id={selectId}
            {required}
            {disabled}
            {multiple}
            class="block w-full {sizeClasses[
                size
            ]} border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            class:border-red-300={error}
            class:focus:border-red-500={error}
            class:focus:ring-red-500={error}
            class:pr-10={error && !multiple}
            {value}
            on:change={handleChange}
            on:blur
            on:focus
        >
            {#if placeholder && !multiple}
                <option value="" disabled={required}>
                    {placeholder}
                </option>
            {/if}

            {#each options as option}
                <option value={option.value} disabled={option.disabled}>
                    {option.label}
                </option>
            {/each}
        </select>

        {#if error && !multiple}
            <div
                class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none"
            >
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
