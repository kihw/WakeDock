/**
 * WakeDock Secrets Management
 * Secure handling of sensitive configuration data
 */

export interface SecretConfig {
    readonly key: string;
    readonly required: boolean;
    readonly defaultValue?: string;
    readonly validator?: (value: string) => boolean;
}

export interface SecretsManager {
    get(key: string): string | null;
    set(key: string, value: string): void;
    remove(key: string): void;
    isAvailable(): boolean;
    rotate(key: string): Promise<void>;
}

// Default secrets configuration
export const SECRETS_CONFIG: Record<string, SecretConfig> = {
    API_KEY: {
        key: 'WAKEDOCK_API_KEY',
        required: true,
        validator: (value) => value.length >= 32
    },
    JWT_SECRET: {
        key: 'WAKEDOCK_JWT_SECRET',
        required: true,
        validator: (value) => value.length >= 32
    },
    ENCRYPTION_KEY: {
        key: 'WAKEDOCK_ENCRYPTION_KEY',
        required: true,
        validator: (value) => value.length >= 16
    },
    CSRF_SECRET: {
        key: 'WAKEDOCK_CSRF_SECRET',
        required: true,
        validator: (value) => value.length >= 16
    },
    DATABASE_URL: {
        key: 'WAKEDOCK_DATABASE_URL',
        required: false,
        defaultValue: 'sqlite:///wakedock.db'
    },
    REDIS_URL: {
        key: 'WAKEDOCK_REDIS_URL',
        required: false,
        defaultValue: 'redis://localhost:6379'
    }
};

/**
 * Environment-based secrets manager
 */
export class EnvironmentSecretsManager implements SecretsManager {
    private cache = new Map<string, string>();
    private initialized = false;

    constructor() {
        this.init();
    }

    private init(): void {
        if (this.initialized) return;

        // Pre-load all configured secrets
        Object.values(SECRETS_CONFIG).forEach(config => {
            const value = this.getFromEnvironment(config.key);
            if (value) {
                this.cache.set(config.key, value);
            }
        });

        this.initialized = true;
    }

    private getFromEnvironment(key: string): string | null {
        // Browser environment - check for runtime config
        if (typeof window !== 'undefined') {
            // @ts-ignore - Global runtime config
            return window.__WAKEDOCK_CONFIG__?.[key] || null;
        }

        // Node.js environment
        return process.env[key] || null;
    }

    get(key: string): string | null {
        // Check cache first
        if (this.cache.has(key)) {
            return this.cache.get(key) || null;
        }

        // Check environment
        const value = this.getFromEnvironment(key);
        if (value) {
            this.cache.set(key, value);
            return value;
        }

        // Check for default value
        const config = SECRETS_CONFIG[key];
        if (config?.defaultValue) {
            this.cache.set(key, config.defaultValue);
            return config.defaultValue;
        }

        return null;
    }

    set(key: string, value: string): void {
        // Validate if validator exists
        const config = SECRETS_CONFIG[key];
        if (config?.validator && !config.validator(value)) {
            throw new Error(`Invalid value for secret: ${key}`);
        }

        this.cache.set(key, value);
    }

    remove(key: string): void {
        this.cache.delete(key);
    }

    isAvailable(): boolean {
        return this.initialized;
    }

    async rotate(key: string): Promise<void> {
        // Placeholder for secret rotation
        console.warn(`Secret rotation not implemented for: ${key}`);
        // In a real implementation, this would:
        // 1. Generate new secret
        // 2. Update backing store
        // 3. Update cache
        // 4. Notify services of rotation
    }

    /**
     * Validate all required secrets are available
     */
    validateRequired(): string[] {
        const missing: string[] = [];

        Object.values(SECRETS_CONFIG).forEach(config => {
            if (config.required && !this.get(config.key)) {
                missing.push(config.key);
            }
        });

        return missing;
    }
}

/**
 * Secure localStorage-based secrets manager for client-side
 */
export class SecureStorageSecretsManager implements SecretsManager {
    private readonly storageKey = 'wakedock_secrets';
    private cache = new Map<string, string>();
    private initialized = false;

    constructor() {
        this.init();
    }

    private init(): void {
        if (this.initialized || typeof window === 'undefined') return;

        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const secrets = JSON.parse(stored);
                Object.entries(secrets).forEach(([key, value]) => {
                    this.cache.set(key, value as string);
                });
            }
        } catch (error) {
            console.warn('Failed to load secrets from storage:', error);
        }

        this.initialized = true;
    }

    private save(): void {
        if (typeof window === 'undefined') return;

        try {
            const secrets = Object.fromEntries(this.cache);
            localStorage.setItem(this.storageKey, JSON.stringify(secrets));
        } catch (error) {
            console.warn('Failed to save secrets to storage:', error);
        }
    }

    get(key: string): string | null {
        return this.cache.get(key) || null;
    }

    set(key: string, value: string): void {
        // Validate if validator exists
        const config = SECRETS_CONFIG[key];
        if (config?.validator && !config.validator(value)) {
            throw new Error(`Invalid value for secret: ${key}`);
        }

        this.cache.set(key, value);
        this.save();
    }

    remove(key: string): void {
        this.cache.delete(key);
        this.save();
    }

    isAvailable(): boolean {
        return this.initialized && typeof window !== 'undefined';
    }

    async rotate(key: string): Promise<void> {
        // Client-side rotation not recommended for most secrets
        throw new Error('Client-side secret rotation not supported');
    }

    /**
     * Clear all secrets (logout/cleanup)
     */
    clear(): void {
        this.cache.clear();
        if (typeof window !== 'undefined') {
            localStorage.removeItem(this.storageKey);
        }
    }
}

// Default secrets manager instance
export const secretsManager = new EnvironmentSecretsManager();

// Validate required secrets on startup
if (typeof window !== 'undefined') {
    const missing = secretsManager.validateRequired();
    if (missing.length > 0) {
        console.error('Missing required secrets:', missing);
    }
}
