<script lang="ts">
    import { Cpu, HardDrive, Activity, Container } from "lucide-svelte";
    import type { Writable } from "svelte/store";

    export let stats: Writable<{
        services: {
            total: number;
            running: number;
            stopped: number;
            error: number;
        };
        system: {
            cpu_usage: number;
            memory_usage: number;
            disk_usage: number;
            uptime: number;
        };
        docker: {
            version: string;
            api_version: string;
            status: string;
        };
        caddy: {
            version: string;
            status: string;
            active_routes: number;
        };
    }>;

    function formatBytes(bytes: number): string {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return (
            Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
        );
    }
</script>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-icon">
            <Container size={24} />
        </div>
        <div class="stat-content">
            <div class="stat-value">{$stats.services.total}</div>
            <div class="stat-label">Total Services</div>
        </div>
    </div>

    <div class="stat-card success">
        <div class="stat-icon">
            <Activity size={24} />
        </div>
        <div class="stat-content">
            <div class="stat-value">{$stats.services.running}</div>
            <div class="stat-label">Running</div>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">
            <Cpu size={24} />
        </div>
        <div class="stat-content">
            <div class="stat-value">{$stats.system.cpu_usage.toFixed(1)}%</div>
            <div class="stat-label">CPU Usage</div>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">
            <HardDrive size={24} />
        </div>
        <div class="stat-content">
            <div class="stat-value">
                {$stats.system.memory_usage.toFixed(1)}%
            </div>
            <div class="stat-label">Memory Usage</div>
        </div>
    </div>
</div>

<style>
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--spacing-lg);
        margin-bottom: var(--spacing-xl);
    }

    .stat-card {
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        transition: all 0.2s ease;
    }

    .stat-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .stat-card.success {
        border-color: var(--color-success);
        background-color: rgb(34 197 94 / 0.05);
    }

    .stat-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: var(--radius);
        background-color: var(--color-primary);
        color: white;
    }

    .success .stat-icon {
        background-color: var(--color-success);
    }

    .stat-content {
        flex: 1;
    }

    .stat-value {
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--color-text);
        line-height: 1;
        margin-bottom: var(--spacing-xs);
    }

    .stat-label {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        font-weight: 500;
    }

    @media (max-width: 640px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
</style>
