import { writable, derived } from 'svelte/store';
import type { User } from '$lib/types/user';

interface UserState {
  users: User[];
  loading: boolean;
  error: string | null;
  selectedUser: User | null;
}

const initialState: UserState = {
  users: [],
  loading: false,
  error: null,
  selectedUser: null,
};

function createUserStore() {
  const { subscribe, set, update } = writable<UserState>(initialState);

  return {
    subscribe,
    setLoading: (loading: boolean) => update((state) => ({ ...state, loading })),
    setError: (error: string | null) => update((state) => ({ ...state, error })),
    setUsers: (users: User[]) => update((state) => ({ ...state, users, error: null })),
    addUser: (user: User) =>
      update((state) => ({
        ...state,
        users: [...state.users, user],
      })),
    updateUser: (updatedUser: User) =>
      update((state) => ({
        ...state,
        users: state.users.map((user) => (user.id === updatedUser.id ? updatedUser : user)),
      })),
    removeUser: (userId: number) =>
      update((state) => ({
        ...state,
        users: state.users.filter((user) => user.id !== userId),
      })),
    selectUser: (user: User | null) => update((state) => ({ ...state, selectedUser: user })),
    reset: () => set(initialState),
  };
}

export const userStore = createUserStore();

// Derived stores
export const activeUsers = derived(userStore, ($userStore) =>
  $userStore.users.filter((user) => user.active)
);

export const adminUsers = derived(userStore, ($userStore) =>
  $userStore.users.filter((user) => user.role === 'admin')
);

export const userCount = derived(userStore, ($userStore) => $userStore.users.length);

export const activeUserCount = derived(activeUsers, ($activeUsers) => $activeUsers.length);
