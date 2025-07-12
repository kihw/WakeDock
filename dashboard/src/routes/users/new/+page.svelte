<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import type { CreateUserRequest } from '$lib/types/user';
  import { auth } from '$lib/stores/auth';
  import { api } from '$lib/api';
  import Button from '$lib/components/ui/atoms/Button.svelte';
  import { toast } from '$lib/stores/toastStore';

  let formData: CreateUserRequest = {
    username: '',
    email: '',
    password: '',
    role: 'user',
    active: true,
  };

  let confirmPassword = '';
  let loading = false;
  let errors: Record<string, string> = {};

  // Check if current user is admin
  $: isAdmin = $auth.user?.role === 'admin';

  onMount(() => {
    if (!isAdmin) {
      goto('/');
      return;
    }
  });

  async function handleSubmit() {
    // Reset errors
    errors = {};

    // Validate form
    if (!formData.username) {
      errors.username = 'Username is required';
    }

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters long';
    }

    if (formData.password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(errors).length > 0) {
      return;
    }

    try {
      loading = true;
      await api.users.create(formData);
      toast.success('User created successfully');
      goto('/users');
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('username')) {
          errors.username = 'Username already exists';
        } else if (err.message.includes('email')) {
          errors.email = 'Email already exists';
        } else {
          toast.error(err.message);
        }
      } else {
        toast.error('Failed to create user');
      }
    } finally {
      loading = false;
    }
  }

  function handleCancel() {
    goto('/users');
  }
</script>

<svelte:head>
  <title>Create User - WakeDock</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <div class="max-w-md mx-auto">
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Create New User</h1>
      <p class="text-gray-600 mt-2">Add a new user to the WakeDock system</p>
    </div>

    <div class="bg-white shadow rounded-lg p-6">
      <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700"> Username * </label>
          <input
            type="text"
            id="username"
            bind:value={formData.username}
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 {errors.username
              ? 'border-red-300'
              : ''}"
            placeholder="Enter username"
            required
          />
          {#if errors.username}
            <p class="mt-1 text-sm text-red-600">
              {errors.username}
            </p>
          {/if}
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">
            Email Address *
          </label>
          <input
            type="email"
            id="email"
            bind:value={formData.email}
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 {errors.email
              ? 'border-red-300'
              : ''}"
            placeholder="Enter email address"
            required
          />
          {#if errors.email}
            <p class="mt-1 text-sm text-red-600">{errors.email}</p>
          {/if}
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700"> Password * </label>
          <input
            type="password"
            id="password"
            bind:value={formData.password}
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 {errors.password
              ? 'border-red-300'
              : ''}"
            placeholder="Enter password"
            required
          />
          {#if errors.password}
            <p class="mt-1 text-sm text-red-600">
              {errors.password}
            </p>
          {/if}
          <p class="mt-1 text-sm text-gray-500">Password must be at least 8 characters long</p>
        </div>

        <div>
          <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
            Confirm Password *
          </label>
          <input
            type="password"
            id="confirmPassword"
            bind:value={confirmPassword}
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 {errors.confirmPassword
              ? 'border-red-300'
              : ''}"
            placeholder="Confirm password"
            required
          />
          {#if errors.confirmPassword}
            <p class="mt-1 text-sm text-red-600">
              {errors.confirmPassword}
            </p>
          {/if}
        </div>

        <div>
          <label for="role" class="block text-sm font-medium text-gray-700"> Role * </label>
          <select
            id="role"
            bind:value={formData.role}
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
          <p class="mt-1 text-sm text-gray-500">
            {formData.role === 'admin'
              ? 'Admin users can manage all system settings and users'
              : 'Regular users can manage their own services'}
          </p>
        </div>

        <div class="flex items-center">
          <input
            type="checkbox"
            id="active"
            bind:checked={formData.active}
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label for="active" class="ml-2 block text-sm text-gray-900"> Active </label>
          <p class="ml-2 text-sm text-gray-500">(Inactive users cannot log in)</p>
        </div>

        <div class="flex justify-end space-x-3 pt-6">
          <Button
            type="button"
            on:click={handleCancel}
            class="bg-gray-300 hover:bg-gray-400 text-gray-700"
            disabled={loading}
          >
            Cancel
          </Button>
          <Button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white" disabled={loading}>
            {#if loading}
              <svg
                class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Creating...
            {:else}
              Create User
            {/if}
          </Button>
        </div>
      </form>
    </div>
  </div>
</div>

<style>
  :global(.container) {
    max-width: 1200px;
  }
</style>
