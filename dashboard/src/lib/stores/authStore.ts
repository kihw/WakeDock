import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type { User, UserSession } from '$lib/types/user';

interface AuthState {
    user: User | null;
    token: string | null;
    expiresAt: Date | null;
    loading: boolean;
    error: string | null;
}

const initialState: AuthState = {
    user: null,
    token: null,
    expiresAt: null,
    loading: false,
    error: null
};

function createAuthStore() {
    const { subscribe, set, update } = writable<AuthState>(initialState);

    // Load session from localStorage on initialization
    if (browser) {
        const stored = localStorage.getItem('wakedock-session');
        if (stored) {
            try {
                const session: UserSession = JSON.parse(stored);
                const expiresAt = new Date(session.expiresAt);

                // Check if session is still valid
                if (expiresAt > new Date()) {
                    set({
                        user: session.user,
                        token: session.token,
                        expiresAt,
                        loading: false,
                        error: null
                    });
                } else {
                    // Session expired, clear it
                    localStorage.removeItem('wakedock-session');
                }
            } catch (err) {
                // Invalid session data, clear it
                localStorage.removeItem('wakedock-session');
            }
        }
    }

    return {
        subscribe,
        login: (user: User, token: string, expiresIn: number) => {
            const expiresAt = new Date(Date.now() + expiresIn * 1000);
            const session: UserSession = { user, token, expiresAt };

            if (browser) {
                localStorage.setItem('wakedock-session', JSON.stringify(session));
            }

            set({
                user,
                token,
                expiresAt,
                loading: false,
                error: null
            });
        },
        logout: () => {
            if (browser) {
                localStorage.removeItem('wakedock-session');
            }
            set(initialState);
        },
        setLoading: (loading: boolean) => update(state => ({ ...state, loading })),
        setError: (error: string | null) => update(state => ({ ...state, error })),
        updateUser: (user: User) => update(state => {
            if (state.user && state.token && state.expiresAt) {
                const session: UserSession = { user, token: state.token, expiresAt: state.expiresAt };
                if (browser) {
                    localStorage.setItem('wakedock-session', JSON.stringify(session));
                }
            }
            return { ...state, user };
        }),
        checkSession: (): boolean => {
            const state = get(authStore);
            if (!state.token || !state.expiresAt) {
                return false;
            }

            const now = new Date();
            if (state.expiresAt <= now) {
                // Session expired
                if (browser) {
                    localStorage.removeItem('wakedock-session');
                }
                set(initialState);
                return false;
            }

            return true;
        },
        refreshToken: async (newToken: string, expiresIn: number) => {
            update(state => {
                if (state.user) {
                    const expiresAt = new Date(Date.now() + expiresIn * 1000);
                    const session: UserSession = { user: state.user, token: newToken, expiresAt };

                    if (browser) {
                        localStorage.setItem('wakedock-session', JSON.stringify(session));
                    }

                    return {
                        ...state,
                        token: newToken,
                        expiresAt
                    };
                }
                return state;
            });
        }
    };
}

function get<T>(store: { subscribe: (fn: (value: T) => void) => () => void }): T {
    let value: T;
    const unsubscribe = store.subscribe(v => value = v);
    unsubscribe();
    return value!;
}

export const authStore = createAuthStore();

// Derived stores
export const isAuthenticated = derived(
    authStore,
    $authStore => $authStore.user !== null && $authStore.token !== null
);

export const isAdmin = derived(
    authStore,
    $authStore => $authStore.user?.role === 'admin'
);

export const currentUser = derived(
    authStore,
    $authStore => $authStore.user
);

export const authToken = derived(
    authStore,
    $authStore => $authStore.token
);
