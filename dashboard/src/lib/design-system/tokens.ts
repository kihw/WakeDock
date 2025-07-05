/**
 * Design System Tokens for WakeDock
 * Central configuration for colors, spacing, typography, and animations
 */

// Color Palette
export const colors = {
    // Primary colors
    primary: {
        50: '#eff6ff',
        100: '#dbeafe',
        200: '#bfdbfe',
        300: '#93c5fd',
        400: '#60a5fa',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
        800: '#1e40af',
        900: '#1e3a8a',
        950: '#172554'
    },

    // Secondary colors
    secondary: {
        50: '#f8fafc',
        100: '#f1f5f9',
        200: '#e2e8f0',
        300: '#cbd5e1',
        400: '#94a3b8',
        500: '#64748b',
        600: '#475569',
        700: '#334155',
        800: '#1e293b',
        900: '#0f172a',
        950: '#020617'
    },

    // Semantic colors
    success: {
        50: '#f0fdf4',
        100: '#dcfce7',
        200: '#bbf7d0',
        300: '#86efac',
        400: '#4ade80',
        500: '#22c55e',
        600: '#16a34a',
        700: '#15803d',
        800: '#166534',
        900: '#14532d',
        950: '#052e16'
    },

    warning: {
        50: '#fffbeb',
        100: '#fef3c7',
        200: '#fde68a',
        300: '#fcd34d',
        400: '#fbbf24',
        500: '#f59e0b',
        600: '#d97706',
        700: '#b45309',
        800: '#92400e',
        900: '#78350f',
        950: '#451a03'
    },

    error: {
        50: '#fef2f2',
        100: '#fee2e2',
        200: '#fecaca',
        300: '#fca5a5',
        400: '#f87171',
        500: '#ef4444',
        600: '#dc2626',
        700: '#b91c1c',
        800: '#991b1b',
        900: '#7f1d1d',
        950: '#450a0a'
    },

    // Neutral colors
    neutral: {
        50: '#fafafa',
        100: '#f5f5f5',
        200: '#e5e5e5',
        300: '#d4d4d4',
        400: '#a3a3a3',
        500: '#737373',
        600: '#525252',
        700: '#404040',
        800: '#262626',
        900: '#171717',
        950: '#0a0a0a'
    }
};

// Typography
export const typography = {
    fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Monaco', 'Consolas', 'monospace']
    },

    fontSize: {
        xs: '0.75rem',      // 12px
        sm: '0.875rem',     // 14px
        base: '1rem',       // 16px
        lg: '1.125rem',     // 18px
        xl: '1.25rem',      // 20px
        '2xl': '1.5rem',    // 24px
        '3xl': '1.875rem',  // 30px
        '4xl': '2.25rem',   // 36px
        '5xl': '3rem',      // 48px
        '6xl': '3.75rem',   // 60px
        '7xl': '4.5rem',    // 72px
        '8xl': '6rem',      // 96px
        '9xl': '8rem'       // 128px
    },

    fontWeight: {
        thin: '100',
        extralight: '200',
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
        black: '900'
    },

    lineHeight: {
        none: '1',
        tight: '1.25',
        snug: '1.375',
        normal: '1.5',
        relaxed: '1.625',
        loose: '2'
    }
};

// Spacing
export const spacing = {
    px: '1px',
    0: '0',
    0.5: '0.125rem',  // 2px
    1: '0.25rem',     // 4px
    1.5: '0.375rem',  // 6px
    2: '0.5rem',      // 8px
    2.5: '0.625rem',  // 10px
    3: '0.75rem',     // 12px
    3.5: '0.875rem',  // 14px
    4: '1rem',        // 16px
    5: '1.25rem',     // 20px
    6: '1.5rem',      // 24px
    7: '1.75rem',     // 28px
    8: '2rem',        // 32px
    9: '2.25rem',     // 36px
    10: '2.5rem',     // 40px
    11: '2.75rem',    // 44px
    12: '3rem',       // 48px
    14: '3.5rem',     // 56px
    16: '4rem',       // 64px
    20: '5rem',       // 80px
    24: '6rem',       // 96px
    28: '7rem',       // 112px
    32: '8rem',       // 128px
    36: '9rem',       // 144px
    40: '10rem',      // 160px
    44: '11rem',      // 176px
    48: '12rem',      // 192px
    52: '13rem',      // 208px
    56: '14rem',      // 224px
    60: '15rem',      // 240px
    64: '16rem',      // 256px
    72: '18rem',      // 288px
    80: '20rem',      // 320px
    96: '24rem'       // 384px
};

// Border radius
export const borderRadius = {
    none: '0',
    sm: '0.125rem',   // 2px
    DEFAULT: '0.25rem', // 4px
    md: '0.375rem',   // 6px
    lg: '0.5rem',     // 8px
    xl: '0.75rem',    // 12px
    '2xl': '1rem',    // 16px
    '3xl': '1.5rem',  // 24px
    full: '9999px'
};

// Shadows
export const shadows = {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    none: 'none'
};

// Animations
export const animations = {
    duration: {
        75: '75ms',
        100: '100ms',
        150: '150ms',
        200: '200ms',
        300: '300ms',
        500: '500ms',
        700: '700ms',
        1000: '1000ms'
    },

    easing: {
        linear: 'linear',
        in: 'cubic-bezier(0.4, 0, 1, 1)',
        out: 'cubic-bezier(0, 0, 0.2, 1)',
        inOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
    },

    keyframes: {
        fadeIn: {
            '0%': { opacity: '0' },
            '100%': { opacity: '1' }
        },
        fadeOut: {
            '0%': { opacity: '1' },
            '100%': { opacity: '0' }
        },
        slideInRight: {
            '0%': { transform: 'translateX(100%)' },
            '100%': { transform: 'translateX(0)' }
        },
        slideInLeft: {
            '0%': { transform: 'translateX(-100%)' },
            '100%': { transform: 'translateX(0)' }
        },
        slideInUp: {
            '0%': { transform: 'translateY(100%)' },
            '100%': { transform: 'translateY(0)' }
        },
        slideInDown: {
            '0%': { transform: 'translateY(-100%)' },
            '100%': { transform: 'translateY(0)' }
        },
        scaleIn: {
            '0%': { transform: 'scale(0.9)', opacity: '0' },
            '100%': { transform: 'scale(1)', opacity: '1' }
        },
        scaleOut: {
            '0%': { transform: 'scale(1)', opacity: '1' },
            '100%': { transform: 'scale(0.9)', opacity: '0' }
        },
        spin: {
            '0%': { transform: 'rotate(0deg)' },
            '100%': { transform: 'rotate(360deg)' }
        },
        pulse: {
            '0%, 100%': { opacity: '1' },
            '50%': { opacity: '0.5' }
        },
        bounce: {
            '0%, 100%': { transform: 'translateY(-25%)', animationTimingFunction: 'cubic-bezier(0.8,0,1,1)' },
            '50%': { transform: 'none', animationTimingFunction: 'cubic-bezier(0,0,0.2,1)' }
        }
    }
};

// Breakpoints
export const breakpoints = {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px'
};

// Z-index layers
export const zIndex = {
    hide: -1,
    auto: 'auto',
    base: 0,
    docked: 10,
    dropdown: 1000,
    sticky: 1100,
    banner: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    skipLink: 1600,
    toast: 1700,
    tooltip: 1800
};

// Component variants
export const variants = {
    button: {
        primary: {
            base: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
            disabled: 'bg-primary-300 text-primary-100 cursor-not-allowed'
        },
        secondary: {
            base: 'bg-secondary-100 text-secondary-900 hover:bg-secondary-200 focus:ring-secondary-500',
            disabled: 'bg-secondary-50 text-secondary-400 cursor-not-allowed'
        },
        success: {
            base: 'bg-success-600 text-white hover:bg-success-700 focus:ring-success-500',
            disabled: 'bg-success-300 text-success-100 cursor-not-allowed'
        },
        warning: {
            base: 'bg-warning-600 text-white hover:bg-warning-700 focus:ring-warning-500',
            disabled: 'bg-warning-300 text-warning-100 cursor-not-allowed'
        },
        error: {
            base: 'bg-error-600 text-white hover:bg-error-700 focus:ring-error-500',
            disabled: 'bg-error-300 text-error-100 cursor-not-allowed'
        },
        ghost: {
            base: 'text-secondary-700 hover:bg-secondary-100 focus:ring-secondary-500',
            disabled: 'text-secondary-400 cursor-not-allowed'
        }
    },

    input: {
        base: 'border-secondary-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500',
        error: 'border-error-500 focus:ring-error-500 focus:border-error-500',
        success: 'border-success-500 focus:ring-success-500 focus:border-success-500',
        disabled: 'bg-secondary-50 border-secondary-200 text-secondary-500 cursor-not-allowed'
    },

    card: {
        base: 'bg-white rounded-lg shadow-md border border-secondary-200',
        elevated: 'bg-white rounded-lg shadow-lg border border-secondary-200',
        outlined: 'bg-white rounded-lg border-2 border-secondary-300',
        filled: 'bg-secondary-50 rounded-lg border border-secondary-200'
    },

    badge: {
        primary: 'bg-primary-100 text-primary-800 border-primary-200',
        secondary: 'bg-secondary-100 text-secondary-800 border-secondary-200',
        success: 'bg-success-100 text-success-800 border-success-200',
        warning: 'bg-warning-100 text-warning-800 border-warning-200',
        error: 'bg-error-100 text-error-800 border-error-200'
    }
};

// Dark mode variants
export const darkMode = {
    colors: {
        background: {
            primary: '#0f172a',
            secondary: '#1e293b',
            tertiary: '#334155'
        },
        text: {
            primary: '#f8fafc',
            secondary: '#cbd5e1',
            tertiary: '#94a3b8'
        },
        border: {
            primary: '#334155',
            secondary: '#475569',
            tertiary: '#64748b'
        }
    }
};

export default {
    colors,
    typography,
    spacing,
    borderRadius,
    shadows,
    animations,
    breakpoints,
    zIndex,
    variants,
    darkMode
};
