<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import type { User } from '$lib/types/user';
  import { userStore } from '$lib/stores/userStore';
  import { auth } from '$lib/stores/auth';
  import { api } from '$lib/api';
  import Button from '$lib/components/ui/atoms/Button.svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/ui/organisms/Modal.svelte';
  import ConfirmModal from '$lib/components/ui/organisms/ConfirmModal.svelte';
  import { toast } from '$lib/stores/toastStore';

  let users: User[] = [];
  let loading = true;
  let error = '';
  let selectedUser: User | null = null;
  let showDeleteModal = false;
  let showEditModal = false;
  let editingUser: Partial<User> = {};

  // Check if current user is admin
  $: isAdmin = $auth.user?.role === 'admin';

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'username', label: 'Username', sortable: true },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'role', label: 'Role', sortable: true },
    { key: 'active', label: 'Status', sortable: true },
    { key: 'created_at', label: 'Created', sortable: true },
    { key: 'actions', label: 'Actions', sortable: false },
  ];

  onMount(async () => {
    if (!isAdmin) {
      goto('/');
      return;
    }
    await loadUsers();
  });

  async function loadUsers() {
    try {
      loading = true;
      error = '';
      users = await api.users.getAll();
      userStore.setUsers(users);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load users';
      toast.error(error);
    } finally {
      loading = false;
    }
  }

  async function handleDelete(user: User) {
    if (user.id === $auth.user?.id) {
      toast.error('Cannot delete your own account');
      return;
    }
    selectedUser = user;
    showDeleteModal = true;
  }

  async function confirmDelete() {
    if (!selectedUser) return;

    try {
      await api.users.delete(
        typeof selectedUser.id === 'string' ? parseInt(selectedUser.id) : selectedUser.id
      );
      toast.success('User deleted successfully');
      await loadUsers();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete user';
      toast.error(message);
    } finally {
      showDeleteModal = false;
      selectedUser = null;
    }
  }

  function handleEdit(user: User) {
    editingUser = { ...user };
    showEditModal = true;
  }

  async function handleSave() {
    if (!editingUser.id) return;

    try {
      const updatedUser = await api.users.update(
        typeof editingUser.id === 'string' ? parseInt(editingUser.id) : editingUser.id,
        editingUser
      );
      toast.success('User updated successfully');
      await loadUsers();
      showEditModal = false;
      editingUser = {};
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update user';
      toast.error(message);
    }
  }

  async function toggleUserStatus(user: User) {
    try {
      await api.users.update(typeof user.id === 'string' ? parseInt(user.id) : user.id, {
        active: !user.active,
      });
      toast.success(`User ${user.active ? 'deactivated' : 'activated'} successfully`);
      await loadUsers();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update user status';
      toast.error(message);
    }
  }

  function renderCell(item: User, column: any): string {
    switch (column.key) {
      case 'active':
        return item.active ? 'Active' : 'Inactive';
      case 'created_at':
        return new Date(item.created_at).toLocaleDateString();
      case 'actions':
        return ''; // Will be handled by slot
      default:
        const value = item[column.key as keyof User];
        return String(value || '');
    }
  }
</script>

<svelte:head>
  <title>User Management - WakeDock</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold text-gray-900">User Management</h1>
    <Button href="/users/new" class="bg-blue-600 hover:bg-blue-700 text-white">Add User</Button>
  </div>

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error loading users</h3>
          <p class="text-sm text-red-700 mt-1">{error}</p>
        </div>
      </div>
    </div>
    <Button on:click={loadUsers} class="bg-blue-600 hover:bg-blue-700 text-white">Retry</Button>
  {:else}
    <div class="bg-white shadow rounded-lg">
      <DataTable data={users} {columns} {renderCell} className="min-w-full">
        <svelte:fragment slot="cell" let:item let:column>
          {#if column.key === 'actions'}
            <div class="flex space-x-2">
              <Button
                on:click={() => handleEdit(item)}
                size="sm"
                class="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Edit
              </Button>
              <Button
                on:click={() => toggleUserStatus(item)}
                size="sm"
                class={item.active
                  ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'}
              >
                {item.active ? 'Deactivate' : 'Activate'}
              </Button>
              <Button
                on:click={() => handleDelete(item)}
                size="sm"
                class="bg-red-600 hover:bg-red-700 text-white"
                disabled={item.id === $auth.user?.id}
              >
                Delete
              </Button>
            </div>
          {/if}
        </svelte:fragment>
      </DataTable>
    </div>

    {#if users.length === 0}
      <div class="text-center py-12">
        <div class="text-gray-500 text-lg">No users found</div>
        <p class="text-gray-400 mt-2">Get started by creating your first user</p>
      </div>
    {/if}
  {/if}
</div>

<!-- Delete Confirmation Modal -->
<ConfirmModal
  bind:open={showDeleteModal}
  title="Delete User"
  message="Are you sure you want to delete user '{selectedUser?.username}'? This action cannot be undone."
  confirmText="Delete"
  confirmVariant="danger"
  on:confirm={confirmDelete}
  on:cancel={() => {
    showDeleteModal = false;
    selectedUser = null;
  }}
/>

<!-- Edit User Modal -->
<Modal bind:open={showEditModal} title="Edit User">
  <form on:submit|preventDefault={handleSave} class="space-y-4">
    <div>
      <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
      <input
        type="text"
        id="username"
        bind:value={editingUser.username}
        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        required
      />
    </div>

    <div>
      <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
      <input
        type="email"
        id="email"
        bind:value={editingUser.email}
        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        required
      />
    </div>

    <div>
      <label for="role" class="block text-sm font-medium text-gray-700">Role</label>
      <select
        id="role"
        bind:value={editingUser.role}
        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        required
      >
        <option value="user">User</option>
        <option value="admin">Admin</option>
      </select>
    </div>

    <div class="flex items-center">
      <input
        type="checkbox"
        id="active"
        bind:checked={editingUser.active}
        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
      />
      <label for="active" class="ml-2 block text-sm text-gray-900">Active</label>
    </div>

    <div class="flex justify-end space-x-3 pt-4">
      <Button
        type="button"
        on:click={() => {
          showEditModal = false;
          editingUser = {};
        }}
        class="bg-gray-300 hover:bg-gray-400 text-gray-700"
      >
        Cancel
      </Button>
      <Button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white">Save Changes</Button>
    </div>
  </form>
</Modal>

<style>
  :global(.container) {
    max-width: 1200px;
  }
</style>
