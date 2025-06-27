<script lang="ts">
    import {
        Menu,
        X,
        Container,
        BarChart3,
        Settings,
        Users,
        Shield,
    } from "lucide-svelte";
    import type { Writable } from "svelte/store";

    export let open: Writable<boolean>;

    const navItems = [
        { label: "Dashboard", href: "/", icon: BarChart3 },
        { label: "Services", href: "/services", icon: Container },
        { label: "Users", href: "/users", icon: Users },
        { label: "Settings", href: "/settings", icon: Settings },
        { label: "Security", href: "/security", icon: Shield },
    ];
</script>

<aside class="sidebar" class:open={$open}>
    <div class="sidebar-header">
        <div class="logo">
            <Container size={24} />
            <span>WakeDock</span>
        </div>
        <button class="close-btn" on:click={() => open.set(false)}>
            <X size={20} />
        </button>
    </div>

    <nav class="sidebar-nav">
        {#each navItems as item}
            <a href={item.href} class="nav-item" class:active={false}>
                <svelte:component this={item.icon} size={18} />
                <span>{item.label}</span>
            </a>
        {/each}
    </nav>

    <div class="sidebar-footer">
        <div class="version">
            <p class="text-sm text-muted">WakeDock v1.0.0</p>
        </div>
    </div>
</aside>

{#if $open}
    <div class="overlay" on:click={() => open.set(false)}></div>
{/if}

<style>
    .sidebar {
        position: fixed;
        top: 0;
        left: -280px;
        width: 280px;
        height: 100vh;
        background-color: var(--color-surface);
        border-right: 1px solid var(--color-border);
        z-index: 50;
        transition: left 0.3s ease;
        display: flex;
        flex-direction: column;
    }

    .sidebar.open {
        left: 0;
    }

    .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--spacing-lg);
        border-bottom: 1px solid var(--color-border);
    }

    .logo {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        font-weight: 600;
        font-size: 1.25rem;
        color: var(--color-primary);
    }

    .close-btn {
        background: none;
        border: none;
        color: var(--color-text-secondary);
        cursor: pointer;
        padding: var(--spacing-xs);
        border-radius: var(--radius);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .close-btn:hover {
        background-color: var(--color-surface-hover);
    }

    .sidebar-nav {
        flex: 1;
        padding: var(--spacing-lg);
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--radius);
        color: var(--color-text-secondary);
        text-decoration: none;
        margin-bottom: var(--spacing-xs);
        transition: all 0.2s ease;
    }

    .nav-item:hover {
        background-color: var(--color-surface-hover);
        color: var(--color-text);
    }

    .nav-item.active {
        background-color: var(--color-primary);
        color: white;
    }

    .sidebar-footer {
        padding: var(--spacing-lg);
        border-top: 1px solid var(--color-border);
    }

    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 40;
    }

    @media (min-width: 769px) {
        .sidebar {
            position: static;
            left: 0;
        }

        .overlay {
            display: none;
        }

        .close-btn {
            display: none;
        }
    }
</style>
