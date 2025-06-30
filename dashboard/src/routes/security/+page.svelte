<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { api } from "$lib/api";
    import { ui, isAuthenticated } from "$lib/stores";
    import { websocket } from "$lib/websocket";
    import { goto } from "$app/navigation";

    interface SecurityEvent {
        id: string;
        type: "success" | "warning" | "error" | "info";
        message: string;
        timestamp: string;
        ipAddress?: string;
        userAgent?: string;
        userId?: string;
    }

    interface SecurityMetrics {
        totalSessions: number;
        activeSessions: number;
        failedLogins: number;
        lastActivity: string;
        securityEvents: SecurityEvent[];
        blockedIPs: string[];
        recentActivity: Array<{
            action: string;
            timestamp: string;
            ipAddress: string;
            userId?: string;
        }>;
    }

    let securityMetrics: SecurityMetrics = {
        totalSessions: 0,
        activeSessions: 0,
        failedLogins: 0,
        lastActivity: "",
        securityEvents: [],
        blockedIPs: [],
        recentActivity: [],
    };
    
    let loading = true;
    let autoRefresh = true;
    let refreshInterval: NodeJS.Timeout | null = null;
    let selectedEventType = 'all';
    let eventSearch = '';

    $: filteredEvents = securityMetrics.securityEvents.filter(event => {
        const matchesType = selectedEventType === 'all' || event.type === selectedEventType;
        const matchesSearch = !eventSearch || event.message.toLowerCase().includes(eventSearch.toLowerCase());
        return matchesType && matchesSearch;
    });

    onMount(async () => {
        // Redirect if not authenticated
        if (!$isAuthenticated) {
            goto('/login');
            return;
        }

        await loadSecurityMetrics();
        
        // Setup WebSocket for real-time security events
        websocket.connect();
        websocket.subscribe('security_event', (data) => {
            addSecurityEvent(data);
        });

        websocket.subscribe('session_update', (data) => {
            updateSessionMetrics(data);
        });

        // Setup auto-refresh
        if (autoRefresh) {
            startAutoRefresh();
        }
    });

    onDestroy(() => {
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        websocket.disconnect();
    });

    const loadSecurityMetrics = async () => {
        loading = true;
        try {
            const response = await api.get("/security/metrics");
            if (response.ok) {
                securityMetrics = await response.json();
            } else {
                throw new Error("Failed to load security metrics");
            }
        } catch (error) {
            console.error("Failed to load security metrics:", error);
            ui.showError("Failed to load security metrics", (error as Error).message);
            
            // Fallback to mock data
            securityMetrics = {
                totalSessions: 156,
                activeSessions: 23,
                failedLogins: 8,
                lastActivity: new Date().toISOString(),
                securityEvents: [
                    {
                        id: '1',
                        type: 'warning',
                        message: 'Multiple failed login attempts from IP 192.168.1.100',
                        timestamp: new Date(Date.now() - 300000).toISOString(),
                        ipAddress: '192.168.1.100'
                    },
                    {
                        id: '2',
                        type: 'success',
                        message: 'User admin logged in successfully',
                        timestamp: new Date(Date.now() - 600000).toISOString(),
                        userId: 'admin'
                    },
                    {
                        id: '3',
                        type: 'error',
                        message: 'Suspicious activity detected: Rapid API calls',
                        timestamp: new Date(Date.now() - 900000).toISOString(),
                        ipAddress: '10.0.0.50'
                    }
                ],
                blockedIPs: ['192.168.1.100', '10.0.0.50'],
                recentActivity: [
                    {
                        action: 'Login',
                        timestamp: new Date(Date.now() - 300000).toISOString(),
                        ipAddress: '192.168.1.50',
                        userId: 'admin'
                    },
                    {
                        action: 'Service Created',
                        timestamp: new Date(Date.now() - 600000).toISOString(),
                        ipAddress: '192.168.1.50',
                        userId: 'admin'
                    }
                ]
            };
        } finally {
            loading = false;
        }
    };

    const startAutoRefresh = () => {
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        refreshInterval = setInterval(loadSecurityMetrics, 30000); // Refresh every 30 seconds
    };

    const stopAutoRefresh = () => {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    };

    const toggleAutoRefresh = () => {
        autoRefresh = !autoRefresh;
        if (autoRefresh) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    };

    const addSecurityEvent = (event: SecurityEvent) => {
        securityMetrics.securityEvents = [event, ...securityMetrics.securityEvents].slice(0, 100); // Keep only last 100 events
    };

    const updateSessionMetrics = (data: any) => {
        securityMetrics.activeSessions = data.activeSessions;
        securityMetrics.totalSessions = data.totalSessions;
    };

    const clearSecurityLogs = async () => {
        const confirmed = confirm("Are you sure you want to clear all security logs?");
        if (!confirmed) return;

        try {
            const response = await api.post("/security/clear-logs");
            if (response.ok) {
                ui.showSuccess("Security logs cleared", "All security logs have been cleared successfully");
                await loadSecurityMetrics();
            } else {
                throw new Error("Failed to clear logs");
            }
        } catch (error) {
            ui.showError("Failed to clear security logs", (error as Error).message);
        }
    };

    const blockIP = async (ipAddress: string) => {
        try {
            const response = await api.post("/security/block-ip", { ipAddress });
            if (response.ok) {
                ui.showSuccess("IP Blocked", `IP address ${ipAddress} has been blocked`);
                await loadSecurityMetrics();
            } else {
                throw new Error("Failed to block IP");
            }
        } catch (error) {
            ui.showError("Failed to block IP", (error as Error).message);
        }
    };

    const unblockIP = async (ipAddress: string) => {
        try {
            const response = await api.post("/security/unblock-ip", { ipAddress });
            if (response.ok) {
                ui.showSuccess("IP Unblocked", `IP address ${ipAddress} has been unblocked`);
                await loadSecurityMetrics();
            } else {
                throw new Error("Failed to unblock IP");
            }
        } catch (error) {
            ui.showError("Failed to unblock IP", (error as Error).message);
        }
    };

    const getEventIcon = (type: string) => {
        switch (type) {
            case 'success':
                return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z';
            case 'warning':
                return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833-.192 2.5 1.732 2.5z';
            case 'error':
                return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z';
            default:
                return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
        }
    };

    const getEventColor = (type: string) => {
        switch (type) {
            case 'success':
                return 'text-green-600 bg-green-100';
            case 'warning':
                return 'text-yellow-600 bg-yellow-100';
            case 'error':
                return 'text-red-600 bg-red-100';
            default:
                return 'text-blue-600 bg-blue-100';
        }
    };

    const formatTimestamp = (timestamp: string) => {
        return new Date(timestamp).toLocaleString();
    };
            }
        } catch (error) {
            toastStore.add({
                type: "error",
                message: "Failed to clear security logs",
            });
        }
    }
</script>

<svelte:head>
  <title>Security - WakeDock</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Security Dashboard</h1>
    <p class="text-gray-600 dark:text-gray-400">Monitor security events and system access</p>
  </div>

  {#if loading}
    <div class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  {:else}
    <!-- Security Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Total Sessions</h3>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">
          {securityMetrics.totalSessions}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Active Sessions</h3>
        <p class="text-2xl font-bold text-green-600">
          {securityMetrics.activeSessions}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Failed Logins</h3>
        <p class="text-2xl font-bold text-red-600">
          {securityMetrics.failedLogins}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Last Activity</h3>
        <p class="text-sm text-gray-900 dark:text-white">
          {securityMetrics.lastActivity || 'N/A'}
        </p>
      </div>
    </div>

    <!-- Security Events -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div
        class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center"
      >
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Security Events</h2>
        <button
          on:click={clearSecurityLogs}
          class="px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
        >
          Clear Logs
        </button>
      </div>

      <div class="p-6">
        {#if securityMetrics.securityEvents.length === 0}
          <div class="text-center py-8">
            <div class="text-gray-400 dark:text-gray-500 mb-2">
              <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                ></path>
              </svg>
            </div>
            <p class="text-gray-500 dark:text-gray-400">No security events recorded</p>
          </div>
        {:else}
          <div class="space-y-4">
            {#each securityMetrics.securityEvents as event}
              <div class="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex-shrink-0">
                  {#if event.type === 'success'}
                    <div class="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
                  {:else if event.type === 'warning'}
                    <div class="w-2 h-2 bg-yellow-400 rounded-full mt-2"></div>
                  {:else}
                    <div class="w-2 h-2 bg-red-400 rounded-full mt-2"></div>
                  {/if}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-gray-900 dark:text-white font-medium">
                    {event.message}
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {event.timestamp}
                  </p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- Security Settings -->
    <div class="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Security Settings</h2>
      </div>

      <div class="p-6 space-y-6">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">
              Two-Factor Authentication
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Add an extra layer of security to your account
            </p>
          </div>
          <button
            class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
          >
            Enable 2FA
          </button>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">Session Timeout</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Automatically log out inactive sessions
            </p>
          </div>
          <select
            class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="30">30 minutes</option>
            <option value="60" selected>1 hour</option>
            <option value="120">2 hours</option>
            <option value="480">8 hours</option>
          </select>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">Login Notifications</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">Get notified of login attempts</p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" class="sr-only peer" checked />
            <div
              class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"
            ></div>
          </label>
        </div>
      </div>
    </div>
  {/if}
</div>
