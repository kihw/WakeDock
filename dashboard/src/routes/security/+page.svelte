<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { toastStore } from '$lib/stores/toastStore';

	interface SecurityEvent {
		type: 'success' | 'warning' | 'error';
		message: string;
		timestamp: string;
	}

	let securityMetrics = {
		totalSessions: 0,
		activeSessions: 0,
		failedLogins: 0,
		lastActivity: '',
		securityEvents: [] as SecurityEvent[]
	};
	let loading = true;

	onMount(async () => {
		try {
			// Load security metrics from API
			const response = await api.get('/security/metrics');
			if (response.ok) {
				securityMetrics = await response.json();
			}
		} catch (error) {
			console.error('Failed to load security metrics:', error);
			toastStore.add({
				type: 'error',
				message: 'Failed to load security metrics'
			});
		} finally {
			loading = false;
		}
	});

	async function clearSecurityLogs() {
		try {
			const response = await api.post('/security/clear-logs');
			if (response.ok) {
				toastStore.add({
					type: 'success',
					message: 'Security logs cleared successfully'
				});
				// Refresh metrics
				location.reload();
			} else {
				throw new Error('Failed to clear logs');
			}
		} catch (error) {
			toastStore.add({
				type: 'error',
				message: 'Failed to clear security logs'
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
				<p class="text-2xl font-bold text-gray-900 dark:text-white">{securityMetrics.totalSessions}</p>
			</div>
			
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
				<h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Active Sessions</h3>
				<p class="text-2xl font-bold text-green-600">{securityMetrics.activeSessions}</p>
			</div>
			
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
				<h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Failed Logins</h3>
				<p class="text-2xl font-bold text-red-600">{securityMetrics.failedLogins}</p>
			</div>
			
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
				<h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Last Activity</h3>
				<p class="text-sm text-gray-900 dark:text-white">{securityMetrics.lastActivity || 'N/A'}</p>
			</div>
		</div>

		<!-- Security Events -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow">
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
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
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
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
									<p class="text-sm text-gray-900 dark:text-white font-medium">{event.message}</p>
									<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{event.timestamp}</p>
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
						<h3 class="text-sm font-medium text-gray-900 dark:text-white">Two-Factor Authentication</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400">Add an extra layer of security to your account</p>
					</div>
					<button class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors">
						Enable 2FA
					</button>
				</div>
				
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-sm font-medium text-gray-900 dark:text-white">Session Timeout</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400">Automatically log out inactive sessions</p>
					</div>
					<select class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
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
						<input type="checkbox" class="sr-only peer" checked>
						<div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
					</label>
				</div>
			</div>
		</div>
	{/if}
</div>
