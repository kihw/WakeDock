<script lang="ts">
    import { onMount } from "svelte";
    import { writable } from "svelte/store";
    import Sidebar from "$lib/components/Sidebar.svelte";
    import Header from "$lib/components/Header.svelte";

    export let data: any = {};

    let sidebarOpen = writable(false);
</script>

<div class="app">
    <Sidebar open={sidebarOpen} />

    <div class="main" class:shifted={$sidebarOpen}>
        <Header {sidebarOpen} />

        <main class="content">
            <slot />
        </main>
    </div>
</div>

<style>
    .app {
        display: flex;
        height: 100vh;
        background-color: var(--color-background);
    }

    .main {
        flex: 1;
        display: flex;
        flex-direction: column;
        transition: margin-left 0.3s ease;
        min-width: 0;
    }

    .main.shifted {
        margin-left: 0;
    }

    .content {
        flex: 1;
        padding: var(--spacing-lg);
        overflow-y: auto;
    }

    @media (max-width: 768px) {
        .main {
            margin-left: 0;
        }
    }
</style>
