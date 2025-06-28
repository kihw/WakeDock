<script lang="ts">
    import {
        Menu,
        X,
        Container,
        BarChart3,
        Settings,
        Users,
        Shield,
        Home,
        Activity,
        Layers,
        Zap
    } from "lucide-svelte";
    import type { Writable } from "svelte/store";
    import { page } from '$app/stores';

    export let open: Writable<boolean>;

    const navItems = [
        { 
            label: "Dashboard", 
            href: "/", 
            icon: Home,
            description: "Overview and metrics"
        },
        { 
            label: "Services", 
            href: "/services", 
            icon: Container,
            description: "Manage containers"
        },
        { 
            label: "Monitoring", 
            href: "/monitoring", 
            icon: Activity,
            description: "System health"
        },
        { 
            label: "Analytics", 
            href: "/analytics", 
            icon: BarChart3,
            description: "Usage insights"
        },
        { 
            label: "Users", 
            href: "/users", 
            icon: Users,
            description: "User management"
        },
        { 
            label: "Security", 
            href: "/security", 
            icon: Shield,
            description: "Access control"
        },
        { 
            label: "Settings", 
            href: "/settings", 
            icon: Settings,
            description: "System configuration"
        }
    ];

    $: currentPath = $page.url.pathname;

    function isActive(href: string): boolean {
        if (href === '/') {
            return currentPath === '/';
        }
        return currentPath.startsWith(href);
    }

    // System stats for sidebar footer
    let systemStats = {
        cpu: 24,
        memory: 68,
        uptime: "14h 32m"
    };
</script>

<aside class="sidebar" class:open={$open}>
    <!-- Logo Section -->
    <div class="sidebar-header">
        <div class="logo">
            <div class="logo-icon">
                <Container size={28} />
            </div>
            <div class="logo-text">
                <span class="logo-name">WakeDock</span>
                <span class="logo-tagline">Docker Manager</span>
            </div>
        </div>
        <button class="close-btn" on:click={() => open.set(false)} aria-label="Close sidebar">
            <X size={20} />
        </button>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
        <button class="quick-action primary" title="Deploy new service">
            <Zap size={16} />
            <span>Quick Deploy</span>
        </button>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
        <div class="nav-section">
            <div class="nav-section-title">Main</div>
            {#each navItems.slice(0, 4) as item}
                <a 
                    href={item.href} 
                    class="nav-item" 
                    class:active={isActive(item.href)}
                    on:click={() => {
                        if (window.innerWidth <= 768) {
                            open.set(false);
                        }
                    }}
                >
                    <div class="nav-item-icon">
                        <svelte:component this={item.icon} size={20} />
                    </div>
                    <div class="nav-item-content">
                        <span class="nav-item-label">{item.label}</span>
                        <span class="nav-item-description">{item.description}</span>
                    </div>
                    {#if isActive(item.href)}
                        <div class="nav-item-indicator"></div>
                    {/if}
                </a>
            {/each}
        </div>

        <div class="nav-section">
            <div class="nav-section-title">Administration</div>
            {#each navItems.slice(4) as item}
                <a 
                    href={item.href} 
                    class="nav-item" 
                    class:active={isActive(item.href)}
                    on:click={() => {
                        if (window.innerWidth <= 768) {
                            open.set(false);
                        }
                    }}
                >
                    <div class="nav-item-icon">
                        <svelte:component this={item.icon} size={20} />
                    </div>
                    <div class="nav-item-content">
                        <span class="nav-item-label">{item.label}</span>
                        <span class="nav-item-description">{item.description}</span>
                    </div>
                    {#if isActive(item.href)}
                        <div class="nav-item-indicator"></div>
                    {/if}
                </a>
            {/each}
        </div>
    </nav>

    <!-- System Status -->
    <div class="sidebar-status">
        <div class="status-header">
            <h4>System Status</h4>
            <div class="status-indicator online">
                <span class="status-dot"></span>
                Online
            </div>
        </div>
        
        <div class="status-metrics">
            <div class="metric">
                <div class="metric-header">
                    <span>CPU</span>
                    <span>{systemStats.cpu}%</span>
                </div>
                <div class="metric-bar">
                    <div class="metric-fill" style="width: {systemStats.cpu}%"></div>
                </div>
            </div>
            
            <div class="metric">
                <div class="metric-header">
                    <span>Memory</span>
                    <span>{systemStats.memory}%</span>
                </div>
                <div class="metric-bar">
                    <div class="metric-fill high" style="width: {systemStats.memory}%"></div>
                </div>
            </div>
            
            <div class="uptime">
                <span class="uptime-label">Uptime</span>
                <span class="uptime-value">{systemStats.uptime}</span>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
        <div class="version">
            <p class="version-text">WakeDock v1.0.0</p>
            <p class="build-info">Build 2024.1.1</p>
        </div>
    </div>
</aside>

{#if $open}
    <div class="overlay" on:click={() => open.set(false)} on:keydown={(e) => e.key === 'Escape' && open.set(false)}></div>
{/if}

<style>
    .sidebar {
        position: fixed;
        top: 0;
        left: -320px;
        width: 320px;
        height: 100vh;
        background: var(--gradient-surface);
        border-right: 1px solid var(--color-border);
        z-index: 50;
        transition: left var(--transition-normal);
        display: flex;
        flex-direction: column;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: var(--shadow-xl);
    }

    .sidebar.open {
        left: 0;
    }

    /* Header Section */
    .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--spacing-lg);
        border-bottom: 1px solid var(--color-border-light);
        background: rgba(255, 255, 255, 0.05);
    }

    .logo {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
    }

    .logo-icon {
        width: 48px;
        height: 48px;
        border-radius: var(--radius-lg);
        background: var(--gradient-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: var(--shadow-md);
    }

    .logo-text {
        display: flex;
        flex-direction: column;
    }

    .logo-name {
        font-weight: 700;
        font-size: 1.25rem;
        color: var(--color-text);
        line-height: 1.2;
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .logo-tagline {
        font-size: 0.75rem;
        color: var(--color-text-muted);
        line-height: 1.2;
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
        transition: all var(--transition-normal);
    }

    .close-btn:hover {
        background: var(--color-surface-hover);
        color: var(--color-text);
        transform: scale(1.1);
    }

    /* Quick Actions */
    .quick-actions {
        padding: var(--spacing-md) var(--spacing-lg);
        border-bottom: 1px solid var(--color-border-light);
    }

    .quick-action {
        width: 100%;
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm) var(--spacing-md);
        border: none;
        border-radius: var(--radius);
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all var(--transition-normal);
        background: var(--gradient-primary);
        color: white;
        box-shadow: var(--shadow-sm);
    }

    .quick-action:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }

    /* Navigation */
    .sidebar-nav {
        flex: 1;
        padding: var(--spacing-lg);
        overflow-y: auto;
    }

    .nav-section {
        margin-bottom: var(--spacing-xl);
    }

    .nav-section:last-child {
        margin-bottom: 0;
    }

    .nav-section-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--color-text-muted);
        margin-bottom: var(--spacing-md);
        padding: 0 var(--spacing-sm);
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        padding: var(--spacing-md) var(--spacing-sm);
        border-radius: var(--radius-lg);
        color: var(--color-text-secondary);
        text-decoration: none;
        margin-bottom: var(--spacing-xs);
        transition: all var(--transition-normal);
        position: relative;
        overflow: hidden;
    }

    .nav-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: var(--gradient-primary);
        opacity: 0;
        transition: opacity var(--transition-normal);
        z-index: -1;
    }

    .nav-item:hover {
        color: var(--color-text);
        transform: translateX(4px);
        background: rgba(255, 255, 255, 0.05);
    }

    .nav-item.active {
        color: white;
        background: var(--gradient-primary);
        box-shadow: var(--shadow-md);
    }

    .nav-item.active::before {
        opacity: 1;
    }

    .nav-item-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: var(--radius);
        background: rgba(255, 255, 255, 0.1);
        transition: all var(--transition-normal);
        flex-shrink: 0;
    }

    .nav-item:hover .nav-item-icon {
        background: rgba(255, 255, 255, 0.15);
        transform: scale(1.05);
    }

    .nav-item.active .nav-item-icon {
        background: rgba(255, 255, 255, 0.2);
    }

    .nav-item-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);
        min-width: 0;
    }

    .nav-item-label {
        font-weight: 500;
        font-size: 0.9rem;
        line-height: 1.2;
    }

    .nav-item-description {
        font-size: 0.75rem;
        opacity: 0.8;
        line-height: 1.2;
    }

    .nav-item-indicator {
        position: absolute;
        right: var(--spacing-sm);
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: white;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        animation: pulse 2s infinite;
    }

    /* System Status */
    .sidebar-status {
        padding: var(--spacing-lg);
        border-top: 1px solid var(--color-border-light);
        background: rgba(0, 0, 0, 0.02);
    }

    .status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-md);
    }

    .status-header h4 {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--color-text);
        margin: 0;
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        font-size: 0.75rem;
        font-weight: 500;
    }

    .status-indicator.online {
        color: var(--color-success);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--color-success);
        animation: pulse 2s infinite;
    }

    .status-metrics {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-md);
    }

    .metric {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);
    }

    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: var(--color-text-secondary);
    }

    .metric-bar {
        height: 4px;
        background: rgba(0, 0, 0, 0.1);
        border-radius: var(--radius-full);
        overflow: hidden;
    }

    .metric-fill {
        height: 100%;
        background: var(--gradient-success);
        border-radius: var(--radius-full);
        transition: width var(--transition-normal);
    }

    .metric-fill.high {
        background: var(--gradient-secondary);
    }

    .uptime {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        padding-top: var(--spacing-sm);
        border-top: 1px solid var(--color-border-light);
    }

    .uptime-label {
        color: var(--color-text-secondary);
    }

    .uptime-value {
        font-weight: 600;
        color: var(--color-text);
        font-family: monospace;
    }

    /* Footer */
    .sidebar-footer {
        padding: var(--spacing-md) var(--spacing-lg);
        border-top: 1px solid var(--color-border-light);
        background: rgba(0, 0, 0, 0.02);
    }

    .version {
        text-align: center;
    }

    .version-text {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--color-text-secondary);
        margin: 0;
        margin-bottom: var(--spacing-xs);
    }

    .build-info {
        font-size: 0.7rem;
        color: var(--color-text-muted);
        margin: 0;
        font-family: monospace;
    }

    /* Overlay */
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 40;
        backdrop-filter: blur(2px);
        -webkit-backdrop-filter: blur(2px);
        animation: fadeIn 0.2s ease-out;
    }

    /* Responsive Design */
    @media (min-width: 769px) {
        .sidebar {
            position: static;
            left: 0;
            width: 280px;
        }

        .overlay {
            display: none;
        }

        .close-btn {
            display: none;
        }
    }

    @media (max-width: 480px) {
        .sidebar {
            width: 100vw;
            left: -100vw;
        }

        .sidebar.open {
            left: 0;
        }

        .nav-item-description {
            display: none;
        }

        .sidebar-status {
            display: none;
        }
    }

    /* Scrollbar for navigation */
    .sidebar-nav::-webkit-scrollbar {
        width: 4px;
    }

    .sidebar-nav::-webkit-scrollbar-track {
        background: transparent;
    }

    .sidebar-nav::-webkit-scrollbar-thumb {
        background: var(--color-border);
        border-radius: var(--radius-full);
    }

    .sidebar-nav::-webkit-scrollbar-thumb:hover {
        background: var(--color-text-muted);
    }
</style>