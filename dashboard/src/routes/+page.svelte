<script lang="ts">
    import { onMount } from "svelte";
    import { writable } from "svelte/store";
    import ServiceCard from "$lib/components/ServiceCard.svelte";
    import StatsCards from "$lib/components/StatsCards.svelte";
    import { Container, Play, Square, Plus } from "lucide-svelte";

    interface Service {
        id: string;
        name: string;
        subdomain: string;
        status: string;
        docker_image?: string;
        docker_compose?: string;
        ports: string[];
        last_accessed?: string;
        resource_usage?: {
            cpu_percent: number;
            memory_usage: number;
            memory_percent: number;
        };
    }

    let services: Service[] = [];
    let loading = true;
    let error = "";

    const stats = writable({
        services: {
            total: 0,
            running: 0,
            stopped: 0,
            error: 0,
        },
        system: {
            cpu_usage: 0,
            memory_usage: 0,
            disk_usage: 0,
            uptime: 0,
        },
        docker: {
            version: "unknown",
            api_version: "unknown",
            status: "unknown",
        },
        caddy: {
            version: "unknown",
            status: "unknown",
            active_routes: 0,
        },
    });

    onMount(async () => {
        await loadServices();
        await loadStats();

        // Refresh data every 30 seconds
        const interval = setInterval(async () => {
            await loadServices();
            await loadStats();
        }, 30000);

        return () => clearInterval(interval);
    });

    async function loadServices() {
        try {
            const response = await fetch("/api/v1/services");
            if (response.ok) {
                services = await response.json();
            } else {
                error = "Failed to load services";
            }
        } catch (e) {
            error = "Network error loading services";
        } finally {
            loading = false;
        }
    }

    async function loadStats() {
        try {
            const response = await fetch("/api/v1/system/overview");
            if (response.ok) {
                const data = await response.json();
                stats.set(data);
            }
        } catch (e) {
            console.error("Failed to load stats:", e);
        }
    }

    async function wakeService(serviceId: string) {
        try {
            const response = await fetch(`/api/v1/services/${serviceId}/wake`, {
                method: "POST",
            });
            if (response.ok) {
                await loadServices();
            }
        } catch (e) {
            console.error("Failed to wake service:", e);
        }
    }

    async function sleepService(serviceId: string) {
        try {
            const response = await fetch(
                `/api/v1/services/${serviceId}/sleep`,
                {
                    method: "POST",
                },
            );
            if (response.ok) {
                await loadServices();
            }
        } catch (e) {
            console.error("Failed to sleep service:", e);
        }
    }
</script>

<svelte:head>
    <title>Dashboard - WakeDock</title>
</svelte:head>

<div class="dashboard">
    <div class="dashboard-header">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="flex items-center gap-md">
                    <Container size={32} />
                    WakeDock Dashboard
                </h1>
                <p class="text-secondary">
                    Manage your Docker services with intelligent orchestration
                </p>
            </div>

            <a href="/services/new" class="btn btn-primary">
                <Plus size={16} />
                Add Service
            </a>
        </div>
    </div>

    <StatsCards {stats} />

    <div class="services-section">
        <div class="section-header">
            <h2>Services</h2>
            <p class="text-secondary">
                {services.length} service{services.length !== 1 ? "s" : ""} configured
            </p>
        </div>

        {#if loading}
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Loading services...</p>
            </div>
        {:else if error}
            <div class="error-state">
                <p class="text-error">{error}</p>
                <button class="btn btn-secondary" on:click={loadServices}>
                    Retry
                </button>
            </div>
        {:else if services.length === 0}
            <div class="empty-state">
                <Container size={48} class="text-muted" />
                <h3>No services configured</h3>
                <p class="text-secondary">
                    Get started by adding your first service
                </p>
                <a href="/services/new" class="btn btn-primary">
                    <Plus size={16} />
                    Add Your First Service
                </a>
            </div>
        {:else}
            <div class="services-grid">
                {#each services as service (service.id)}
                    <ServiceCard
                        {service}
                        on:wake={() => wakeService(service.id)}
                        on:sleep={() => sleepService(service.id)}
                    />
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    .dashboard {
        max-width: 1200px;
        margin: 0 auto;
    }

    .dashboard-header {
        margin-bottom: var(--spacing-xl);
    }

    .section-header {
        margin-bottom: var(--spacing-lg);
    }

    .section-header h2 {
        margin-bottom: var(--spacing-xs);
    }

    .services-grid {
        display: grid;
        gap: var(--spacing-lg);
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    }

    .loading-state,
    .error-state,
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--spacing-2xl);
        text-align: center;
        min-height: 300px;
    }

    .spinner {
        width: 32px;
        height: 32px;
        border: 3px solid var(--color-border);
        border-top: 3px solid var(--color-primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: var(--spacing-md);
    }

    .empty-state h3 {
        margin: var(--spacing-md) 0;
    }

    .empty-state p {
        margin-bottom: var(--spacing-lg);
    }

    @keyframes spin {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }

    @media (max-width: 768px) {
        .services-grid {
            grid-template-columns: 1fr;
        }

        .dashboard-header .flex {
            flex-direction: column;
            gap: var(--spacing-md);
            align-items: flex-start;
        }
    }
</style>
