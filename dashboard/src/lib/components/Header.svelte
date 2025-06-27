<script lang="ts">
    import { Menu, Bell, User, Sun, Moon } from "lucide-svelte";
    import { writable } from "svelte/store";

    export let sidebarOpen: any;

    const darkMode = writable(false);

    function toggleDarkMode() {
        darkMode.update((dark) => {
            const newMode = !dark;
            document.documentElement.setAttribute(
                "data-theme",
                newMode ? "dark" : "light",
            );
            return newMode;
        });
    }
</script>

<header class="header">
    <div class="header-left">
        <button
            class="menu-btn"
            on:click={() => sidebarOpen.set(!$sidebarOpen)}
        >
            <Menu size={20} />
        </button>
    </div>

    <div class="header-right">
        <button class="icon-btn" on:click={toggleDarkMode} title="Toggle theme">
            {#if $darkMode}
                <Sun size={18} />
            {:else}
                <Moon size={18} />
            {/if}
        </button>

        <button class="icon-btn" title="Notifications">
            <Bell size={18} />
        </button>

        <div class="user-menu">
            <button class="user-btn">
                <User size={18} />
                <span>Admin</span>
            </button>
        </div>
    </div>
</header>

<style>
    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--spacing-md) var(--spacing-lg);
        background-color: var(--color-surface);
        border-bottom: 1px solid var(--color-border);
        position: sticky;
        top: 0;
        z-index: 30;
    }

    .header-left {
        display: flex;
        align-items: center;
    }

    .menu-btn {
        background: none;
        border: none;
        color: var(--color-text-secondary);
        cursor: pointer;
        padding: var(--spacing-sm);
        border-radius: var(--radius);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .menu-btn:hover {
        background-color: var(--color-surface-hover);
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }

    .icon-btn {
        background: none;
        border: none;
        color: var(--color-text-secondary);
        cursor: pointer;
        padding: var(--spacing-sm);
        border-radius: var(--radius);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }

    .icon-btn:hover {
        background-color: var(--color-surface-hover);
        color: var(--color-text);
    }

    .user-btn {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        background: none;
        border: none;
        color: var(--color-text-secondary);
        cursor: pointer;
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--radius);
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }

    .user-btn:hover {
        background-color: var(--color-surface-hover);
        color: var(--color-text);
    }

    @media (min-width: 769px) {
        .menu-btn {
            display: none;
        }
    }
</style>
