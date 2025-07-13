<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Bell, User, Settings, LogOut, Shield, Moon, Sun } from 'lucide-svelte';
  import { writable } from 'svelte/store';
  import { manageFocus, announceToScreenReader, trapFocus } from '$lib/utils/accessibility';
  
  interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
    avatar?: string;
    role: string;
  }

  interface Notification {
    id: number;
    title: string;
    message: string;
    time: string;
    type: 'success' | 'warning' | 'error' | 'info';
    read: boolean;
  }

  export let user: User | null = null;
  export let unreadNotifications: number = 0;

  const dispatch = createEventDispatcher<{
    logout: void;
    themeToggle: void;
  }>();

  const darkMode = writable(false);
  
  let showNotifications = false;
  let showUserMenu = false;
  let notificationDropdown: HTMLElement;
  let userDropdown: HTMLElement;
  let previousFocus: HTMLElement;

  // Mock notifications
  const notifications: Notification[] = [
    {
      id: 1,
      title: 'Service Started',
      message: 'nginx-proxy is now running',
      time: '2 min ago',
      type: 'success',
      read: false
    },
    {
      id: 2,
      title: 'Memory Alert',
      message: 'High memory usage detected',
      time: '5 min ago',
      type: 'warning',
      read: false
    },
    {
      id: 3,
      title: 'Backup Complete',
      message: 'Database backup finished',
      time: '1 hour ago',
      type: 'info',
      read: true
    }
  ];

  function toggleNotifications(e: MouseEvent) {
    e.stopPropagation();
    
    if (showNotifications) {
      closeNotifications();
    } else {
      openNotifications();
    }
  }

  function openNotifications() {
    previousFocus = document.activeElement as HTMLElement;
    showUserMenu = false;
    showNotifications = true;

    setTimeout(() => {
      if (notificationDropdown) {
        trapFocus(notificationDropdown);
        const firstItem = notificationDropdown.querySelector('[role="menuitem"]') as HTMLElement;
        if (firstItem) {
          manageFocus(firstItem);
        }
      }
    }, 100);

    announceToScreenReader(`Notifications menu opened. ${notifications.length} notifications available.`);
  }

  function closeNotifications() {
    showNotifications = false;
    if (previousFocus) {
      manageFocus(previousFocus);
    }
    announceToScreenReader('Notifications menu closed');
  }

  function toggleUserMenu(e: MouseEvent) {
    e.stopPropagation();
    
    if (showUserMenu) {
      closeUserMenu();
    } else {
      openUserMenu();
    }
  }

  function openUserMenu() {
    previousFocus = document.activeElement as HTMLElement;
    showNotifications = false;
    showUserMenu = true;

    setTimeout(() => {
      if (userDropdown) {
        trapFocus(userDropdown);
        const firstItem = userDropdown.querySelector('[role="menuitem"]') as HTMLElement;
        if (firstItem) {
          manageFocus(firstItem);
        }
      }
    }, 100);

    announceToScreenReader('User menu opened. Navigate with arrow keys.');
  }

  function closeUserMenu() {
    showUserMenu = false;
    if (previousFocus) {
      manageFocus(previousFocus);
    }
    announceToScreenReader('User menu closed');
  }

  function handleThemeToggle() {
    dispatch('themeToggle');
    darkMode.update(mode => !mode);
    closeUserMenu();
  }

  function handleLogout() {
    dispatch('logout');
    closeUserMenu();
  }

  function getNotificationIcon(type: string) {
    switch (type) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return 'ℹ️';
    }
  }

  // Close dropdowns when clicking outside
  function handleClickOutside() {
    if (showNotifications) closeNotifications();
    if (showUserMenu) closeUserMenu();
  }
</script>

<svelte:window on:click={handleClickOutside} />

<div class="flex items-center space-x-3">
  <!-- Theme Toggle -->
  <button
    type="button"
    class="p-2 rounded-md text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors duration-200"
    on:click={handleThemeToggle}
    aria-label={$darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
  >
    {#if $darkMode}
      <Sun class="h-5 w-5" />
    {:else}
      <Moon class="h-5 w-5" />
    {/if}
  </button>

  <!-- Notifications -->
  <div class="relative">
    <button
      type="button"
      class="p-2 rounded-md text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors duration-200"
      on:click={toggleNotifications}
      aria-label="Notifications"
      aria-expanded={showNotifications}
      aria-haspopup="true"
    >
      <Bell class="h-5 w-5" />
      {#if unreadNotifications > 0}
        <span class="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          {unreadNotifications > 9 ? '9+' : unreadNotifications}
        </span>
      {/if}
    </button>

    <!-- Notifications Dropdown -->
    {#if showNotifications}
      <div
        bind:this={notificationDropdown}
        class="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50"
        role="menu"
        tabindex="-1"
        aria-orientation="vertical"
        on:click|stopPropagation
      >
        <div class="py-1">
          <div class="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">Notifications</h3>
          </div>
          
          <div class="max-h-64 overflow-y-auto">
            {#each notifications as notification}
              <button
                type="button"
                class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                role="menuitem"
              >
                <div class="flex items-start space-x-3">
                  <span class="text-lg mt-0.5">{getNotificationIcon(notification.type)}</span>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {notification.title}
                    </p>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {notification.message}
                    </p>
                    <p class="text-xs text-gray-400 mt-1">
                      {notification.time}
                    </p>
                  </div>
                  {#if !notification.read}
                    <div class="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  {/if}
                </div>
              </button>
            {/each}
          </div>
          
          <div class="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
            <a
              href="/notifications"
              class="text-sm text-green-600 hover:text-green-500 font-medium"
              role="menuitem"
            >
              View all notifications
            </a>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- User Menu -->
  {#if user}
    <div class="relative">
      <button
        type="button"
        class="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
        on:click={toggleUserMenu}
        aria-label="User menu"
        aria-expanded={showUserMenu}
        aria-haspopup="true"
      >
        {#if user.avatar}
          <img
            class="h-8 w-8 rounded-full"
            src={user.avatar}
            alt={user.full_name}
          />
        {:else}
          <div class="h-8 w-8 rounded-full bg-green-500 flex items-center justify-center">
            <User class="h-5 w-5 text-white" />
          </div>
        {/if}
      </button>

      <!-- User Dropdown -->
      {#if showUserMenu}
        <div
          bind:this={userDropdown}
          class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50"
          role="menu"
          tabindex="-1"
          aria-orientation="vertical"
          on:click|stopPropagation
        >
          <div class="py-1">
            <!-- User Info -->
            <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <p class="text-sm font-medium text-gray-900 dark:text-white">{user.full_name}</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">{user.email}</p>
              <p class="text-xs text-gray-400 mt-1 capitalize">{user.role}</p>
            </div>

            <!-- Menu Items -->
            <a
              href="/profile"
              class="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
              role="menuitem"
            >
              <User class="h-4 w-4 mr-3" />
              Profile
            </a>

            <a
              href="/settings"
              class="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
              role="menuitem"
            >
              <Settings class="h-4 w-4 mr-3" />
              Settings
            </a>

            <a
              href="/security"
              class="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
              role="menuitem"
            >
              <Shield class="h-4 w-4 mr-3" />
              Security
            </a>

            <div class="border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                class="flex items-center w-full px-4 py-2 text-sm text-red-700 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                role="menuitem"
                on:click={handleLogout}
              >
                <LogOut class="h-4 w-4 mr-3" />
                Sign out
              </button>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <!-- Login Button -->
    <a
      href="/login"
      class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
    >
      Sign in
    </a>
  {/if}
</div>