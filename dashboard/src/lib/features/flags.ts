/**
 * Feature Flags System
 * Provides runtime feature toggles and A/B testing infrastructure
 */

export interface FeatureFlag {
  key: string;
  name: string;
  description: string;
  enabled: boolean;
  rolloutPercentage: number;
  environments: string[];
  variants?: {
    [key: string]: {
      enabled: boolean;
      rolloutPercentage: number;
      config?: Record<string, any>;
    };
  };
}

export interface FeatureFlagsConfig {
  flags: Record<string, FeatureFlag>;
  userId?: string;
  environment: string;
  overrides?: Record<string, boolean>;
}

class FeatureFlagsManager {
  private config: FeatureFlagsConfig;
  private listeners: Map<string, ((enabled: boolean) => void)[]> = new Map();

  constructor(config: FeatureFlagsConfig) {
    this.config = config;
  }

  /**
   * Check if a feature is enabled
   */
  isEnabled(flagKey: string): boolean {
    // Check for overrides first (useful for development/testing)
    if (this.config.overrides?.[flagKey] !== undefined) {
      return this.config.overrides[flagKey];
    }

    const flag = this.config.flags[flagKey];
    if (!flag) {
      console.warn(`Feature flag '${flagKey}' not found`);
      return false;
    }

    // Check if flag is enabled for current environment
    if (!flag.environments.includes(this.config.environment)) {
      return false;
    }

    // Check rollout percentage
    if (flag.rolloutPercentage < 100) {
      const hash = this.hashUserId(this.config.userId || 'anonymous', flagKey);
      const userPercentile = hash % 100;
      if (userPercentile >= flag.rolloutPercentage) {
        return false;
      }
    }

    return flag.enabled;
  }

  /**
   * Get feature variant
   */
  getVariant(flagKey: string): string | null {
    if (!this.isEnabled(flagKey)) {
      return null;
    }

    const flag = this.config.flags[flagKey];
    if (!flag?.variants) {
      return 'default';
    }

    const hash = this.hashUserId(this.config.userId || 'anonymous', flagKey);
    let cumulativePercentage = 0;
    const userPercentile = hash % 100;

    for (const [variantName, variant] of Object.entries(flag.variants)) {
      if (!variant.enabled) {
        continue;
      }

      cumulativePercentage += variant.rolloutPercentage;
      if (userPercentile < cumulativePercentage) {
        return variantName;
      }
    }

    return 'default';
  }

  /**
   * Get variant configuration
   */
  getVariantConfig(flagKey: string): Record<string, any> | null {
    const variant = this.getVariant(flagKey);
    if (!variant || variant === 'default') {
      return null;
    }

    return this.config.flags[flagKey]?.variants?.[variant]?.config || null;
  }

  /**
   * Override a feature flag (useful for development/testing)
   */
  override(flagKey: string, enabled: boolean): void {
    if (!this.config.overrides) {
      this.config.overrides = {};
    }
    this.config.overrides[flagKey] = enabled;
    this.notifyListeners(flagKey, enabled);
  }

  /**
   * Clear all overrides
   */
  clearOverrides(): void {
    this.config.overrides = {};
  }

  /**
   * Subscribe to feature flag changes
   */
  subscribe(flagKey: string, callback: (enabled: boolean) => void): () => void {
    if (!this.listeners.has(flagKey)) {
      this.listeners.set(flagKey, []);
    }
    this.listeners.get(flagKey)!.push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(flagKey);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<FeatureFlagsConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get all enabled flags
   */
  getEnabledFlags(): string[] {
    return Object.keys(this.config.flags).filter((key) => this.isEnabled(key));
  }

  /**
   * Hash user ID for consistent rollout
   */
  private hashUserId(userId: string, flagKey: string): number {
    const str = `${userId}:${flagKey}`;
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  /**
   * Notify listeners of flag changes
   */
  private notifyListeners(flagKey: string, enabled: boolean): void {
    const callbacks = this.listeners.get(flagKey);
    if (callbacks) {
      callbacks.forEach((callback) => callback(enabled));
    }
  }
}

// Default feature flags configuration
export const defaultFeatureFlags: Record<string, FeatureFlag> = {
  analytics: {
    key: 'analytics',
    name: 'Analytics Dashboard',
    description: 'Enable advanced analytics and reporting features',
    enabled: true,
    rolloutPercentage: 100,
    environments: ['development', 'production'],
  },
  'realtime-notifications': {
    key: 'realtime-notifications',
    name: 'Real-time Notifications',
    description: 'Enable WebSocket-based real-time notifications',
    enabled: true,
    rolloutPercentage: 100,
    environments: ['development', 'production'],
  },
  'advanced-monitoring': {
    key: 'advanced-monitoring',
    name: 'Advanced Monitoring',
    description: 'Enable detailed system monitoring and alerts',
    enabled: true,
    rolloutPercentage: 80,
    environments: ['production'],
  },
  'ai-assistant': {
    key: 'ai-assistant',
    name: 'AI Assistant',
    description: 'Enable AI-powered assistance features',
    enabled: false,
    rolloutPercentage: 0,
    environments: ['development'],
    variants: {
      basic: {
        enabled: true,
        rolloutPercentage: 50,
        config: {
          features: ['basic-help', 'quick-commands'],
        },
      },
      advanced: {
        enabled: true,
        rolloutPercentage: 50,
        config: {
          features: ['basic-help', 'quick-commands', 'predictive-analysis'],
        },
      },
    },
  },
  'beta-ui': {
    key: 'beta-ui',
    name: 'Beta UI Components',
    description: 'Enable new experimental UI components',
    enabled: false,
    rolloutPercentage: 10,
    environments: ['development'],
  },
  'performance-monitoring': {
    key: 'performance-monitoring',
    name: 'Performance Monitoring',
    description: 'Enable client-side performance monitoring',
    enabled: true,
    rolloutPercentage: 100,
    environments: ['development', 'production'],
  },
};

// Environment detection
function getEnvironment(): string {
  if (typeof window === 'undefined') {
    return 'server';
  }

  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'development';
  }

  if (window.location.hostname.includes('staging')) {
    return 'staging';
  }

  return 'production';
}

// Create global feature flags instance
export const featureFlags = new FeatureFlagsManager({
  flags: defaultFeatureFlags,
  environment: getEnvironment(),
  userId: undefined, // Will be set after authentication
});

// Utility functions for common patterns
export const withFeatureFlag = (flagKey: string, callback: () => void): void => {
  if (featureFlags.isEnabled(flagKey)) {
    callback();
  }
};

export const featureToggle = <T>(flagKey: string, enabledValue: T, disabledValue: T): T => {
  return featureFlags.isEnabled(flagKey) ? enabledValue : disabledValue;
};

// Type-safe feature flag hooks for Svelte
export const createFeatureFlagStore = (flagKey: string) => {
  const { subscribe, set } = writable(featureFlags.isEnabled(flagKey));

  // Subscribe to flag changes
  const unsubscribe = featureFlags.subscribe(flagKey, (enabled) => {
    set(enabled);
  });

  return {
    subscribe,
    // Cleanup function
    destroy: unsubscribe,
  };
};

// Development utilities
export const devTools = {
  /**
   * List all feature flags and their status
   */
  listFlags(): void {
    console.table(
      Object.values(featureFlags['config'].flags).map((flag) => ({
        key: flag.key,
        name: flag.name,
        enabled: featureFlags.isEnabled(flag.key),
        rollout: `${flag.rolloutPercentage}%`,
        environments: flag.environments.join(', '),
      }))
    );
  },

  /**
   * Enable a feature flag
   */
  enable(flagKey: string): void {
    featureFlags.override(flagKey, true);
    console.log(`✅ Feature flag '${flagKey}' enabled`);
  },

  /**
   * Disable a feature flag
   */
  disable(flagKey: string): void {
    featureFlags.override(flagKey, false);
    console.log(`❌ Feature flag '${flagKey}' disabled`);
  },

  /**
   * Clear all overrides
   */
  reset(): void {
    featureFlags.clearOverrides();
    console.log('🔄 All feature flag overrides cleared');
  },
};

// Make dev tools available in development
if (getEnvironment() === 'development' && typeof window !== 'undefined') {
  (window as any).__featureFlags = devTools;
}

// Import writable from svelte/store
import { writable } from 'svelte/store';
