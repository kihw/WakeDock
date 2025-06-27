<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import {
        Play,
        Square,
        ExternalLink,
        Settings,
        Cpu,
        HardDrive,
    } from "lucide-svelte";

    export let service: {
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
    };

    const dispatch = createEventDispatcher();

    function formatBytes(bytes: number): string {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return (
            Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
        );
    }

    function formatLastAccessed(dateString?: string): string {
        if (!dateString) return "Never";
        const date = new Date(dateString);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const minutes = Math.floor(diff / (1000 * 60));

        if (minutes < 1) return "Just now";
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    }

    function getStatusClass(status: string): string {
        switch (status) {
            case "running":
                return "status-running";
            case "stopped":
                return "status-stopped";
            case "starting":
                return "status-starting";
            case "error":
                return "status-error";
            default:
                return "status-stopped";
        }
    }
</script>

<div class="service-card">
    <div class="card-header">
        <div class="service-info">
            <h3 class="service-name">{service.name}</h3>
            <p class="service-subdomain">{service.subdomain}.yourdomain.com</p>
        </div>

        <div class="service-status">
            <span class="status {getStatusClass(service.status)}">
                <span class="status-dot"></span>
                {service.status}
            </span>
        </div>
    </div>

    <div class="card-body">
        <div class="service-details">
            <div class="detail-item">
                <span class="detail-label">Type:</span>
                <span class="detail-value">
                    {service.docker_compose ? "Compose" : "Image"}
                </span>
            </div>

            <div class="detail-item">
                <span class="detail-label">Source:</span>
                <span class="detail-value">
                    {service.docker_compose || service.docker_image || "N/A"}
                </span>
            </div>

            {#if service.ports.length > 0}
                <div class="detail-item">
                    <span class="detail-label">Ports:</span>
                    <span class="detail-value">{service.ports.join(", ")}</span>
                </div>
            {/if}

            <div class="detail-item">
                <span class="detail-label">Last accessed:</span>
                <span class="detail-value"
                    >{formatLastAccessed(service.last_accessed)}</span
                >
            </div>
        </div>

        {#if service.resource_usage && service.status === "running"}
            <div class="resource-usage">
                <h4>Resource Usage</h4>
                <div class="resource-stats">
                    <div class="resource-item">
                        <Cpu size={16} />
                        <span
                            >{service.resource_usage.cpu_percent.toFixed(
                                1,
                            )}%</span
                        >
                    </div>
                    <div class="resource-item">
                        <HardDrive size={16} />
                        <span
                            >{formatBytes(
                                service.resource_usage.memory_usage,
                            )}</span
                        >
                    </div>
                </div>
            </div>
        {/if}
    </div>

    <div class="card-footer">
        <div class="action-buttons">
            {#if service.status === "running"}
                <button
                    class="btn btn-warning btn-sm"
                    on:click={() => dispatch("sleep")}
                >
                    <Square size={14} />
                    Sleep
                </button>
            {:else}
                <button
                    class="btn btn-success btn-sm"
                    on:click={() => dispatch("wake")}
                >
                    <Play size={14} />
                    Wake
                </button>
            {/if}

            <a
                href={`/services/${service.id}`}
                class="btn btn-secondary btn-sm"
            >
                <Settings size={14} />
                Configure
            </a>

            {#if service.status === "running"}
                <a
                    href={`https://${service.subdomain}.yourdomain.com`}
                    target="_blank"
                    class="btn btn-primary btn-sm"
                >
                    <ExternalLink size={14} />
                    Visit
                </a>
            {/if}
        </div>
    </div>
</div>

<style>
    .service-card {
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        overflow: hidden;
        transition: all 0.2s ease;
    }

    .service-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: var(--spacing-lg);
        border-bottom: 1px solid var(--color-border);
    }

    .service-name {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: var(--spacing-xs);
        color: var(--color-text);
    }

    .service-subdomain {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        font-family: monospace;
        margin: 0;
    }

    .card-body {
        padding: var(--spacing-lg);
    }

    .service-details {
        margin-bottom: var(--spacing-lg);
    }

    .detail-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-sm);
        font-size: 0.875rem;
    }

    .detail-item:last-child {
        margin-bottom: 0;
    }

    .detail-label {
        font-weight: 500;
        color: var(--color-text-secondary);
    }

    .detail-value {
        color: var(--color-text);
        text-align: right;
        max-width: 60%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .resource-usage {
        border-top: 1px solid var(--color-border);
        padding-top: var(--spacing-lg);
    }

    .resource-usage h4 {
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: var(--spacing-sm);
        color: var(--color-text);
    }

    .resource-stats {
        display: flex;
        gap: var(--spacing-lg);
    }

    .resource-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        font-size: 0.875rem;
        color: var(--color-text-secondary);
    }

    .card-footer {
        padding: var(--spacing-lg);
        border-top: 1px solid var(--color-border);
        background-color: var(--color-background);
    }

    .action-buttons {
        display: flex;
        gap: var(--spacing-sm);
        flex-wrap: wrap;
    }

    .action-buttons .btn {
        flex: 1;
        min-width: auto;
    }

    @media (max-width: 480px) {
        .action-buttons {
            flex-direction: column;
        }

        .action-buttons .btn {
            flex: none;
        }
    }
</style>
