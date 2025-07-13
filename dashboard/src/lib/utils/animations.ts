/**
 * Animation Utilities - WakeDock Design System
 * Provides consistent animations and transitions across the application
 */

import { cubicInOut, cubicOut, quartOut, quintOut } from 'svelte/easing';

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Get animation duration respecting user preferences
 */
export function getAnimationDuration(duration: number): number {
    return prefersReducedMotion() ? 0 : duration;
}

// Animation duration constants
export const DURATIONS = {
    fast: 150,
    normal: 200,
    slow: 300,
    slower: 500,
    slowest: 800
} as const;

// Easing functions
export const EASINGS = {
    linear: (t: number) => t,
    ease: cubicInOut,
    easeIn: (t: number) => t * t,
    easeOut: cubicOut,
    easeInOut: cubicInOut,
    bounce: quartOut,
    spring: quintOut
} as const;

// Common animation presets
export const ANIMATIONS = {
    // Fade animations
    fadeIn: {
        duration: DURATIONS.normal,
        easing: EASINGS.ease,
        css: (t: number) => `opacity: ${t}`
    },

    fadeOut: {
        duration: DURATIONS.normal,
        easing: EASINGS.ease,
        css: (t: number) => `opacity: ${t}`
    },

    // Slide animations
    slideInLeft: {
        duration: DURATIONS.normal,
        easing: EASINGS.spring,
        css: (t: number) => `transform: translateX(${(1 - t) * -100}%); opacity: ${t}`
    },

    slideInRight: {
        duration: DURATIONS.normal,
        easing: EASINGS.spring,
        css: (t: number) => `transform: translateX(${(1 - t) * 100}%); opacity: ${t}`
    },

    slideInUp: {
        duration: DURATIONS.normal,
        easing: EASINGS.spring,
        css: (t: number) => `transform: translateY(${(1 - t) * 100}%); opacity: ${t}`
    },

    slideInDown: {
        duration: DURATIONS.normal,
        easing: EASINGS.spring,
        css: (t: number) => `transform: translateY(${(1 - t) * -100}%); opacity: ${t}`
    },

    // Scale animations
    scaleIn: {
        duration: DURATIONS.normal,
        easing: EASINGS.spring,
        css: (t: number) => `transform: scale(${0.8 + t * 0.2}); opacity: ${t}`
    },

    scaleOut: {
        duration: DURATIONS.normal,
        easing: EASINGS.ease,
        css: (t: number) => `transform: scale(${0.8 + t * 0.2}); opacity: ${t}`
    },

    // Rotation animations
    rotateIn: {
        duration: DURATIONS.slow,
        easing: EASINGS.spring,
        css: (t: number) => `transform: rotate(${(1 - t) * -180}deg); opacity: ${t}`
    },

    // Flip animations
    flipIn: {
        duration: DURATIONS.slow,
        easing: EASINGS.spring,
        css: (t: number) => `transform: rotateY(${(1 - t) * -90}deg); opacity: ${t}`
    },

    // Bounce animations
    bounceIn: {
        duration: DURATIONS.slower,
        easing: EASINGS.bounce,
        css: (t: number) => `transform: scale(${0.3 + t * 0.7}); opacity: ${t}`
    },

    // Drawer/Modal animations
    drawerSlide: {
        duration: DURATIONS.slow,
        easing: EASINGS.spring,
        css: (t: number) => `transform: translateX(${(1 - t) * 100}%)`
    },

    modalScale: {
        duration: DURATIONS.normal,
        easing: EASINGS.spring,
        css: (t: number) => `transform: scale(${0.9 + t * 0.1}); opacity: ${t}`
    },

    // Toast animations
    toastSlide: {
        duration: DURATIONS.normal,
        easing: EASINGS.spring,
        css: (t: number) => `transform: translateX(${(1 - t) * 100}%); opacity: ${t}`
    },

    // Dropdown animations
    dropdownScale: {
        duration: DURATIONS.fast,
        easing: EASINGS.spring,
        css: (t: number) => `transform: scale(${0.95 + t * 0.05}) translateY(${(1 - t) * -10}px); opacity: ${t}`
    }
} as const;

// Animation utilities
export function createAnimation(params: {
    duration?: number;
    easing?: (t: number) => number;
    css?: (t: number) => string;
    delay?: number;
}) {
    return {
        duration: params.duration || DURATIONS.normal,
        easing: params.easing || EASINGS.ease,
        css: params.css || ((t: number) => `opacity: ${t}`),
        delay: params.delay || 0
    };
}

// Stagger animation utility
export function createStaggeredAnimation(
    baseAnimation: any,
    staggerDelay: number = 50
) {
    return (index: number = 0) => ({
        ...baseAnimation,
        delay: (baseAnimation.delay || 0) + (index * staggerDelay)
    });
}

// Parallax animation utility
export function createParallaxAnimation(
    speed: number = 0.5,
    direction: 'vertical' | 'horizontal' = 'vertical'
) {
    return {
        duration: 0,
        css: (t: number) => {
            const offset = (1 - t) * 100 * speed;
            const transform = direction === 'vertical'
                ? `translateY(${offset}px)`
                : `translateX(${offset}px)`;
            return `transform: ${transform}`;
        }
    };
}

// Micro-interaction animations
export const MICRO_ANIMATIONS = {
    // Button press effect
    buttonPress: {
        duration: 100,
        easing: EASINGS.ease,
        css: (t: number) => `transform: scale(${0.95 + t * 0.05})`
    },

    // Hover lift effect
    hoverLift: {
        duration: 200,
        easing: EASINGS.ease,
        css: (t: number) => `transform: translateY(${(1 - t) * -4}px)`
    },

    // Focus ring
    focusRing: {
        duration: 200,
        easing: EASINGS.ease,
        css: (t: number) => `box-shadow: 0 0 0 ${t * 3}px rgba(59, 130, 246, ${t * 0.3})`
    },

    // Shake effect (for errors)
    shake: {
        duration: 500,
        easing: EASINGS.ease,
        css: (t: number) => {
            const intensity = Math.sin(t * Math.PI * 4) * (1 - t) * 10;
            return `transform: translateX(${intensity}px)`;
        }
    },

    // Pulse effect
    pulse: {
        duration: 1000,
        easing: EASINGS.ease,
        css: (t: number) => `transform: scale(${1 + Math.sin(t * Math.PI) * 0.1})`
    },

    // Glow effect
    glow: {
        duration: 800,
        easing: EASINGS.ease,
        css: (t: number) => {
            const intensity = Math.sin(t * Math.PI) * 0.5;
            return `box-shadow: 0 0 ${intensity * 20}px rgba(59, 130, 246, ${intensity})`;
        }
    }
} as const;

// Animation sequences
export function createAnimationSequence(animations: any[]) {
    return {
        duration: animations.reduce((total, anim) => total + anim.duration, 0),
        css: (t: number) => {
            let elapsed = 0;

            for (const anim of animations) {
                const animStart = elapsed / animations.reduce((total, a) => total + a.duration, 0);
                const animEnd = (elapsed + anim.duration) / animations.reduce((total, a) => total + a.duration, 0);

                if (t >= animStart && t <= animEnd) {
                    const animProgress = (t - animStart) / (animEnd - animStart);
                    return anim.css(animProgress);
                }

                elapsed += anim.duration;
            }

            return '';
        }
    };
}

// CSS-in-JS animation utilities
export function generateKeyframes(name: string, keyframes: Record<string, string>) {
    const keyframeEntries = Object.entries(keyframes)
        .map(([key, value]) => `${key} { ${value} }`)
        .join(' ');

    return `@keyframes ${name} { ${keyframeEntries} }`;
}

// Animation class utilities
export const ANIMATION_CLASSES = {
    // Entrance animations
    fadeIn: 'animate-fade-in',
    slideInLeft: 'animate-slide-in-left',
    slideInRight: 'animate-slide-in-right',
    slideInUp: 'animate-slide-in-up',
    slideInDown: 'animate-slide-in-down',
    scaleIn: 'animate-scale-in',
    rotateIn: 'animate-rotate-in',
    bounceIn: 'animate-bounce-in',

    // Exit animations
    fadeOut: 'animate-fade-out',
    slideOutLeft: 'animate-slide-out-left',
    slideOutRight: 'animate-slide-out-right',
    slideOutUp: 'animate-slide-out-up',
    slideOutDown: 'animate-slide-out-down',
    scaleOut: 'animate-scale-out',
    rotateOut: 'animate-rotate-out',
    bounceOut: 'animate-bounce-out',

    // Attention animations
    pulse: 'animate-pulse',
    spin: 'animate-spin',
    bounce: 'animate-bounce',
    shake: 'animate-shake',
    glow: 'animate-glow',

    // Hover animations
    hoverLift: 'hover:animate-lift',
    hoverScale: 'hover:animate-scale',
    hoverGlow: 'hover:animate-glow'
} as const;

// Performance optimized animations
export function createOptimizedAnimation(params: {
    duration?: number;
    easing?: (t: number) => number;
    css?: (t: number) => string;
    willChange?: string;
}) {
    return {
        ...params,
        duration: params.duration || DURATIONS.normal,
        easing: params.easing || EASINGS.ease,
        css: (t: number) => {
            const baseCSS = params.css ? params.css(t) : `opacity: ${t}`;
            const willChange = params.willChange || 'transform, opacity';
            return `${baseCSS}; will-change: ${willChange}`;
        }
    };
}

// Responsive animations (reduce motion for accessibility)
export function createResponsiveAnimation(animation: any) {
    return {
        ...animation,
        css: (t: number) => {
            // Check for reduced motion preference
            const prefersReducedMotion = typeof window !== 'undefined' &&
                window.matchMedia('(prefers-reduced-motion: reduce)').matches;

            if (prefersReducedMotion) {
                return `opacity: ${t}`;
            }

            return animation.css(t);
        }
    };
}

/**
 * Animation functions with prefers-reduced-motion support
 */
export function createAccessibleAnimation(
    baseAnimation: any,
    fallback?: any
) {
    if (prefersReducedMotion()) {
        return fallback || {
            duration: 0,
            css: () => ''
        };
    }
    return {
        ...baseAnimation,
        duration: getAnimationDuration(baseAnimation.duration)
    };
}

/**
 * Enhanced fade animation with reduced motion support
 */
export function accessibleFade(node: Element, params: {
    duration?: number;
    easing?: (t: number) => number;
    delay?: number;
} = {}) {
    const {
        duration = DURATIONS.normal,
        easing = EASINGS.ease,
        delay = 0
    } = params;

    const actualDuration = getAnimationDuration(duration);

    return {
        duration: actualDuration,
        delay,
        easing,
        css: (t: number) => `opacity: ${t}`
    };
}

/**
 * Enhanced slide animation with reduced motion support
 */
export function accessibleSlide(node: Element, params: {
    direction?: 'up' | 'down' | 'left' | 'right';
    duration?: number;
    easing?: (t: number) => number;
    delay?: number;
    distance?: number;
} = {}) {
    const {
        direction = 'up',
        duration = DURATIONS.normal,
        easing = EASINGS.spring,
        delay = 0,
        distance = 20
    } = params;

    const actualDuration = getAnimationDuration(duration);

    if (actualDuration === 0) {
        return {
            duration: 0,
            css: () => ''
        };
    }

    const transforms = {
        up: (t: number) => `translateY(${(1 - t) * distance}px)`,
        down: (t: number) => `translateY(${(1 - t) * -distance}px)`,
        left: (t: number) => `translateX(${(1 - t) * distance}px)`,
        right: (t: number) => `translateX(${(1 - t) * -distance}px)`
    };

    return {
        duration: actualDuration,
        delay,
        easing,
        css: (t: number) => `
            transform: ${transforms[direction](t)};
            opacity: ${t}
        `
    };
}

/**
 * CSS custom properties for reduced motion
 */
export const REDUCED_MOTION_CSS = `
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
`;

/**
 * Apply reduced motion CSS to document
 */
export function applyReducedMotionCSS() {
    if (typeof document === 'undefined') return;

    const styleId = 'wakedock-reduced-motion';
    let existingStyle = document.getElementById(styleId);

    if (!existingStyle) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = REDUCED_MOTION_CSS;
        document.head.appendChild(style);
    }
}

// Auto-apply reduced motion CSS when module loads
if (typeof window !== 'undefined') {
    applyReducedMotionCSS();
}

// Export all animations for easy access
export const animations = {
    ...ANIMATIONS,
    ...MICRO_ANIMATIONS
};

export type AnimationName = keyof typeof animations;
export type AnimationPreset = typeof animations[AnimationName];

// Default export for convenience
export default {
    DURATIONS,
    EASINGS,
    ANIMATIONS,
    MICRO_ANIMATIONS,
    ANIMATION_CLASSES,
    createAnimation,
    createStaggeredAnimation,
    createParallaxAnimation,
    createAnimationSequence,
    createOptimizedAnimation,
    createResponsiveAnimation,
    generateKeyframes,
    animations
};
