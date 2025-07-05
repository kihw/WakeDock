/**
 * Dark Mode Theme Provider - WakeDock Design System
 * Provides theme context and utilities for dark mode support
 */

import { writable, derived, type Readable } from 'svelte/store';
import { browser } from '$app/environment';

// Theme types
export type Theme = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

// Theme store
function createThemeStore() {
    const { subscribe, set, update } = writable<Theme>('system');

    return {
        subscribe,
        set,
        update,
        setTheme: (theme: Theme) => {
            set(theme);
            if (browser) {
                localStorage.setItem('theme', theme);
                applyTheme(theme);
            }
        },
        toggle: () => {
            update(current => {
                const newTheme = current === 'light' ? 'dark' : 'light';
                if (browser) {
                    localStorage.setItem('theme', newTheme);
                    applyTheme(newTheme);
                }
                return newTheme;
            });
        },
        init: () => {
            if (browser) {
                const stored = localStorage.getItem('theme') as Theme;
                const theme = stored || 'system';
                set(theme);
                applyTheme(theme);
            }
        }
    };
}

export const theme = createThemeStore();

// System theme detection
function createSystemThemeStore() {
    const { subscribe, set } = writable<ResolvedTheme>('light');

    if (browser) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        const updateSystemTheme = () => {
            set(mediaQuery.matches ? 'dark' : 'light');
        };

        // Set initial value
        updateSystemTheme();

        // Listen for changes
        mediaQuery.addEventListener('change', updateSystemTheme);

        // Cleanup function
        return {
            subscribe,
            destroy: () => {
                mediaQuery.removeEventListener('change', updateSystemTheme);
            }
        };
    }

    return { subscribe, destroy: () => { } };
}

export const systemTheme = createSystemThemeStore();

// Resolved theme (actual theme being used)
export const resolvedTheme: Readable<ResolvedTheme> = derived(
    [theme, systemTheme],
    ([$theme, $systemTheme]) => {
        return $theme === 'system' ? $systemTheme : $theme;
    }
);

// Theme utility functions
function applyTheme(theme: Theme) {
    if (!browser) return;

    const root = document.documentElement;
    const body = document.body;

    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    body.classList.remove('light', 'dark');

    if (theme === 'system') {
        const systemIsDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const resolvedTheme = systemIsDark ? 'dark' : 'light';
        root.classList.add(resolvedTheme);
        body.classList.add(resolvedTheme);
    } else {
        root.classList.add(theme);
        body.classList.add(theme);
    }

    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        metaThemeColor.setAttribute('content', isDark ? '#1e293b' : '#ffffff');
    }
}

// Theme classes utility
export function getThemeClasses(theme: ResolvedTheme) {
    return {
        // Background colors
        bg: {
            primary: theme === 'dark' ? 'bg-gray-900' : 'bg-white',
            secondary: theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50',
            tertiary: theme === 'dark' ? 'bg-gray-700' : 'bg-gray-100',
            accent: theme === 'dark' ? 'bg-blue-600' : 'bg-blue-500',
            elevated: theme === 'dark' ? 'bg-gray-800' : 'bg-white'
        },

        // Text colors
        text: {
            primary: theme === 'dark' ? 'text-gray-100' : 'text-gray-900',
            secondary: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
            tertiary: theme === 'dark' ? 'text-gray-400' : 'text-gray-500',
            accent: theme === 'dark' ? 'text-blue-400' : 'text-blue-600',
            inverse: theme === 'dark' ? 'text-gray-900' : 'text-gray-100'
        },

        // Border colors
        border: {
            primary: theme === 'dark' ? 'border-gray-700' : 'border-gray-200',
            secondary: theme === 'dark' ? 'border-gray-600' : 'border-gray-300',
            accent: theme === 'dark' ? 'border-blue-500' : 'border-blue-400',
            focus: theme === 'dark' ? 'border-blue-400' : 'border-blue-500'
        },

        // Ring colors (for focus states)
        ring: {
            primary: theme === 'dark' ? 'ring-blue-400' : 'ring-blue-500',
            secondary: theme === 'dark' ? 'ring-gray-400' : 'ring-gray-500'
        },

        // Shadow colors
        shadow: {
            sm: theme === 'dark' ? 'shadow-gray-900/25' : 'shadow-gray-900/10',
            md: theme === 'dark' ? 'shadow-gray-900/25' : 'shadow-gray-900/10',
            lg: theme === 'dark' ? 'shadow-gray-900/25' : 'shadow-gray-900/10'
        }
    };
}

// CSS custom properties for theme
export function getThemeProperties(theme: ResolvedTheme) {
    const colors = {
        light: {
            '--color-bg-primary': '255 255 255',
            '--color-bg-secondary': '249 250 251',
            '--color-bg-tertiary': '243 244 246',
            '--color-text-primary': '17 24 39',
            '--color-text-secondary': '75 85 99',
            '--color-text-tertiary': '107 114 128',
            '--color-border-primary': '229 231 235',
            '--color-border-secondary': '209 213 219',
            '--color-accent': '59 130 246',
            '--color-accent-hover': '37 99 235'
        },
        dark: {
            '--color-bg-primary': '17 24 39',
            '--color-bg-secondary': '31 41 55',
            '--color-bg-tertiary': '55 65 81',
            '--color-text-primary': '243 244 246',
            '--color-text-secondary': '209 213 219',
            '--color-text-tertiary': '156 163 175',
            '--color-border-primary': '55 65 81',
            '--color-border-secondary': '75 85 99',
            '--color-accent': '96 165 250',
            '--color-accent-hover': '59 130 246'
        }
    };

    return colors[theme];
}

// Theme transition utility
export function enableThemeTransition() {
    if (!browser) return;

    const css = document.createElement('style');
    css.textContent = `
    *,
    *::before,
    *::after {
      transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease, fill 0.3s ease, stroke 0.3s ease;
    }
  `;

    document.head.appendChild(css);

    // Remove transition after a short delay to prevent flash
    setTimeout(() => {
        document.head.removeChild(css);
    }, 300);
}

// Theme-aware component props
export interface ThemeableProps {
    theme?: ResolvedTheme;
    darkMode?: boolean;
}

// Theme context for components
export function useTheme() {
    let currentTheme: ResolvedTheme = 'light';
    let unsubscribe: (() => void) | undefined;

    if (browser) {
        unsubscribe = resolvedTheme.subscribe(theme => {
            currentTheme = theme;
        });
    }

    const getThemeState = () => ({
        theme: currentTheme,
        isDark: currentTheme === 'dark',
        isLight: currentTheme === 'light',
        classes: getThemeClasses(currentTheme),
        properties: getThemeProperties(currentTheme)
    });

    return {
        ...getThemeState(),
        destroy: () => {
            if (unsubscribe) unsubscribe();
        }
    };
}

// Initialize theme on app start
export function initializeTheme() {
    if (browser) {
        theme.init();
        enableThemeTransition();
    }
}

// Theme toggle component helper
export function createThemeToggle() {
    return {
        toggle: () => theme.toggle(),
        setTheme: (newTheme: Theme) => theme.setTheme(newTheme),
        current: theme,
        resolved: resolvedTheme
    };
}
