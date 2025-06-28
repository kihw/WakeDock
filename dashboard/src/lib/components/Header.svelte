<script lang="ts">
    import { Menu, Bell, User, Sun, Moon, Settings } from "lucide-svelte";
    import { writable } from "svelte/store";
    import type { Writable } from "svelte/store";

    export let sidebarOpen: Writable<boolean>;

    const darkMode = writable(false);

    function toggleDarkMode() {
        darkMode.update((dark) => {
            const newMode = !dark;
            document.documentElement.setAttribute(
                "data-theme",
                newMode ? "dark" : "light",
            );
            localStorage.setItem('wakedock_theme', newMode ? 'dark' : 'light');
            return newMode;
        });
    }

    // Initialize theme from localStorage
    if (typeof window !== 'undefined') {
        const savedTheme = localStorage.getItem('wakedock_theme');
        if (savedTheme) {
            darkMode.set(savedTheme === 'dark');
            document.documentElement.setAttribute("data-theme", savedTheme);
        }
    }

    let showNotifications = false;
    let showUserMenu = false;

    // Mock notifications
    const notifications = [
        { id: 1, title: "Service Started", message: "nginx-proxy is now running", time: "2 min ago", type: "success" },
        { id: 2, title: "Memory Alert", message: "High memory usage detected", time: "5 min ago", type: "warning" },
        { id: 3, title: "Backup Complete", message: "Database backup finished", time: "1 hour ago", type: "info" }
    ];

    function getNotificationIcon(type: string) {
        switch (type) {
            case 'success': return '✅';
            case 'warning': return '⚠️';
            case 'error': return '❌';
            default: return 'ℹ️';
        }
    }
</script>

<header class="header">
    <div class="header-left">
        <button
            class="menu-btn"
            on:click={() => sidebarOpen.set(!$sidebarOpen)}
            aria-label="Toggle sidebar"
        >
            <Menu size={20} />
        </button>
        
        <div class="breadcrumb">
            <h2 class="page-title">Dashboard</h2>
            <span class="page-subtitle">Welcome back, Admin</span>
        </div>
    </div>

    <div class="header-right">
        <!-- Search Bar -->
        <div class="search-container">
            <div class="search-input-wrapper">
                <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="m21 21-4.35-4.35"/>
                </svg>
                <input 
                    type="text" 
                    placeholder="Search services..." 
                    class="search-input"
                />
                <kbd class="search-kbd">⌘K</kbd>
            </div>
        </div>

        <!-- Theme Toggle -->
        <button class="icon-btn theme-toggle" on:click={toggleDarkMode} title="Toggle theme">
            {#if $darkMode}
                <Sun size={18} />
            {:else}
                <Moon size={18} />
            {/if}
        </button>

        <!-- Notifications -->
        <div class="dropdown">
            <button 
                class="icon-btn notification-btn" 
                title="Notifications"
                on:click={() => showNotifications = !showNotifications}
            >
                <Bell size={18} />
                <span class="notification-badge">{notifications.length}</span>
            </button>

            {#if showNotifications}
                <div class="dropdown-menu notifications-menu">
                    <div class="dropdown-header">
                        <h3>Notifications</h3>
                        <button class="text-btn">Mark all read</button>
                    </div>
                    <div class="notifications-list">
                        {#each notifications as notification}
                            <div class="notification-item">
                                <div class="notification-icon">
                                    {getNotificationIcon(notification.type)}
                                </div>
                                <div class="notification-content">
                                    <div class="notification-title">{notification.title}</div>
                                    <div class="notification-message">{notification.message}</div>
                                    <div class="notification-time">{notification.time}</div>
                                </div>
                            </div>
                        {/each}
                    </div>
                    <div class="dropdown-footer">
                        <a href="/notifications" class="text-btn">View all notifications</a>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Settings -->
        <button class="icon-btn" title="Settings">
            <Settings size={18} />
        </button>

        <!-- User Menu -->
        <div class="dropdown">
            <button 
                class="user-btn"
                on:click={() => showUserMenu = !showUserMenu}
            >
                <div class="user-avatar">
                    <User size={18} />
                </div>
                <div class="user-info">
                    <span class="user-name">Admin</span>
                    <span class="user-role">Administrator</span>
                </div>
                <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6,9 12,15 18,9"/>
                </svg>
            </button>

            {#if showUserMenu}
                <div class="dropdown-menu user-menu">
                    <div class="user-menu-header">
                        <div class="user-avatar large">
                            <User size={24} />
                        </div>
                        <div class="user-details">
                            <div class="user-name">Administrator</div>
                            <div class="user-email">admin@wakedock.com</div>
                        </div>
                    </div>
                    <div class="menu-divider"></div>
                    <a href="/profile" class="menu-item">
                        <User size={16} />
                        Profile Settings
                    </a>
                    <a href="/preferences" class="menu-item">
                        <Settings size={16} />
                        Preferences
                    </a>
                    <div class="menu-divider"></div>
                    <button class="menu-item logout-btn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                            <polyline points="16,17 21,12 16,7"/>
                            <line x1="21" y1="12" x2="9" y2="12"/>
                        </svg>
                        Sign Out
                    </button>
                </div>
            {/if}
        </div>
    </div>
</header>

<!-- Click outside to close dropdowns -->
<svelte:window 
    on:click={(e) => {
        if (!e.target.closest('.dropdown')) {
            showNotifications = false;
            showUserMenu = false;
        }
    }}
/>

<style>
    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--spacing-md) var(--spacing-lg);
        background: var(--gradient-surface);
        border-bottom: 1px solid var(--color-border-light);
        position: sticky;
        top: 0;
        z-index: 30;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: var(--shadow-sm);
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: var(--spacing-lg);
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
        transition: all var(--transition-normal);
    }

    .menu-btn:hover {
        background: var(--color-surface-hover);
        color: var(--color-text);
        transform: scale(1.05);
    }

    .breadcrumb {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);
    }

    .page-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--color-text);
        margin: 0;
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .page-subtitle {
        font-size: 0.75rem;
        color: var(--color-text-muted);
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }

    /* Search Container */
    .search-container {
        position: relative;
        margin-right: var(--spacing-md);
    }

    .search-input-wrapper {
        position: relative;
        display: flex;
        align-items: center;
    }

    .search-input {
        width: 300px;
        padding: var(--spacing-sm) var(--spacing-md);
        padding-left: 2.5rem;
        padding-right: 3rem;
        border: 1px solid var(--color-border);
        border-radius: var(--radius-full);
        background: var(--color-surface-glass);
        color: var(--color-text);
        font-size: 0.875rem;
        transition: all var(--transition-normal);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .search-input:focus {
        outline: none;
        border-color: var(--color-primary);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        width: 350px;
    }

    .search-icon {
        position: absolute;
        left: var(--spacing-sm);
        color: var(--color-text-muted);
        pointer-events: none;
    }

    .search-kbd {
        position: absolute;
        right: var(--spacing-sm);
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--spacing-xs);
        padding: 2px 6px;
        font-size: 0.7rem;
        color: var(--color-text-muted);
        font-family: monospace;
    }

    /* Icon Buttons */
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
        transition: all var(--transition-normal);
        position: relative;
    }

    .icon-btn:hover {
        background: var(--color-surface-hover);
        color: var(--color-text);
        transform: scale(1.05);
    }

    .theme-toggle:hover {
        color: var(--color-primary);
    }

    /* Notification Badge */
    .notification-btn {
        position: relative;
    }

    .notification-badge {
        position: absolute;
        top: 2px;
        right: 2px;
        background: var(--gradient-secondary);
        color: white;
        border-radius: 50%;
        width: 18px;
        height: 18px;
        font-size: 0.7rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse 2s infinite;
    }

    /* User Button */
    .user-btn {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        background: var(--color-surface-glass);
        border: 1px solid var(--color-border);
        color: var(--color-text);
        cursor: pointer;
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--radius-full);
        font-size: 0.875rem;
        transition: all var(--transition-normal);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .user-btn:hover {
        background: var(--color-surface-hover);
        border-color: var(--color-primary-light);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }

    .user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--gradient-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }

    .user-avatar.large {
        width: 48px;
        height: 48px;
    }

    .user-info {
        display: flex;
        flex-direction: column;
        text-align: left;
    }

    .user-name {
        font-weight: 500;
        line-height: 1.2;
    }

    .user-role {
        font-size: 0.75rem;
        color: var(--color-text-muted);
        line-height: 1.2;
    }

    .chevron {
        color: var(--color-text-muted);
        transition: transform var(--transition-normal);
    }

    .user-btn:hover .chevron {
        transform: rotate(180deg);
    }

    /* Dropdown Menus */
    .dropdown {
        position: relative;
    }

    .dropdown-menu {
        position: absolute;
        top: calc(100% + var(--spacing-sm));
        right: 0;
        min-width: 280px;
        background: var(--gradient-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-xl);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        z-index: 1000;
        animation: slideIn 0.2s ease-out;
        overflow: hidden;
    }

    .dropdown-header {
        padding: var(--spacing-md) var(--spacing-lg);
        border-bottom: 1px solid var(--color-border-light);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
    }

    .dropdown-header h3 {
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
        color: var(--color-text);
    }

    .dropdown-footer {
        padding: var(--spacing-md) var(--spacing-lg);
        border-top: 1px solid var(--color-border-light);
        background: rgba(0, 0, 0, 0.02);
        text-align: center;
    }

    .text-btn {
        background: none;
        border: none;
        color: var(--color-primary);
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        transition: color var(--transition-normal);
    }

    .text-btn:hover {
        color: var(--color-primary-dark);
    }

    /* Notifications Menu */
    .notifications-list {
        max-height: 300px;
        overflow-y: auto;
    }

    .notification-item {
        display: flex;
        gap: var(--spacing-sm);
        padding: var(--spacing-md) var(--spacing-lg);
        border-bottom: 1px solid var(--color-border-light);
        transition: background-color var(--transition-normal);
    }

    .notification-item:hover {
        background: rgba(255, 255, 255, 0.05);
    }

    .notification-item:last-child {
        border-bottom: none;
    }

    .notification-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
    }

    .notification-content {
        flex: 1;
        min-width: 0;
    }

    .notification-title {
        font-weight: 500;
        font-size: 0.875rem;
        color: var(--color-text);
        margin-bottom: var(--spacing-xs);
    }

    .notification-message {
        font-size: 0.8rem;
        color: var(--color-text-secondary);
        margin-bottom: var(--spacing-xs);
    }

    .notification-time {
        font-size: 0.75rem;
        color: var(--color-text-muted);
    }

    /* User Menu */
    .user-menu-header {
        padding: var(--spacing-lg);
        display: flex;
        gap: var(--spacing-md);
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
    }

    .user-details .user-name {
        font-weight: 600;
        color: var(--color-text);
        margin-bottom: var(--spacing-xs);
    }

    .user-email {
        font-size: 0.8rem;
        color: var(--color-text-muted);
    }

    .menu-divider {
        height: 1px;
        background: var(--color-border-light);
        margin: var(--spacing-sm) 0;
    }

    .menu-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm) var(--spacing-lg);
        color: var(--color-text-secondary);
        text-decoration: none;
        font-size: 0.875rem;
        transition: all var(--transition-normal);
        background: none;
        border: none;
        width: 100%;
        text-align: left;
        cursor: pointer;
    }

    .menu-item:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--color-text);
    }

    .logout-btn {
        color: var(--color-error);
    }

    .logout-btn:hover {
        background: rgba(239, 68, 68, 0.1);
        color: var(--color-error);
    }

    @media (max-width: 768px) {
        .menu-btn {
            display: flex;
        }

        .search-container {
            display: none;
        }

        .breadcrumb {
            display: none;
        }

        .user-info {
            display: none;
        }

        .dropdown-menu {
            min-width: 250px;
        }
    }

    @media (max-width: 480px) {
        .header {
            padding: var(--spacing-sm) var(--spacing-md);
        }

        .header-right {
            gap: var(--spacing-xs);
        }

        .dropdown-menu {
            right: -50px;
            min-width: 200px;
        }
    }
</style>