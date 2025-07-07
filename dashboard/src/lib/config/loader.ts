/**
 * Configuration Loader
 * Ensures proper initialization order for runtime configuration
 */
import { browser } from '$app/environment';
import { updateConfigFromRuntime } from './environment.js';

let initializationPromise: Promise<void> | null = null;

/**
 * Initialize configuration asynchronously
 * This ensures runtime configuration is loaded before any API calls
 */
export async function initializeConfig(): Promise<void> {
    // Only initialize once
    if (initializationPromise) {
        return initializationPromise;
    }

    // Only initialize in browser environment
    if (!browser) {
        return Promise.resolve();
    }

    console.log('🔄 Starting configuration initialization...');

    initializationPromise = updateConfigFromRuntime()
        .then(() => {
            console.log('✅ Configuration initialization complete');
        })
        .catch((error) => {
            console.error('❌ Configuration initialization failed:', error);
            // Don't fail completely - use default config
        });

    return initializationPromise;
}

/**
 * Ensure configuration is initialized before proceeding
 */
export async function ensureConfigInitialized(): Promise<void> {
    if (!initializationPromise) {
        await initializeConfig();
    } else {
        await initializationPromise;
    }
}
