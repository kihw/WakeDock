/**
 * Advanced Theme Manager
 * Provides runtime theme switching and advanced customization capabilities
 */

import { writable, derived, type Readable } from 'svelte/store';
import { colors, variants, darkMode } from './tokens';
import { cssBridge } from './css-bridge';

export type ThemeMode = 'light' | 'dark' | 'auto';
export type ThemeVariant = 'default' | 'compact' | 'comfortable';

interface ThemeConfig {
  mode: ThemeMode;
  variant: ThemeVariant;
  customColors?: Partial<typeof colors>;
  customVariants?: Partial<typeof variants>;
}

interface ThemeState {
  currentMode: ThemeMode;
  resolvedMode: 'light' | 'dark'; // Resolved auto mode
  variant: ThemeVariant;
  isSystemDark: boolean;
}

// Create theme stores
export const themeConfig = writable<ThemeConfig>({
  mode: 'light',
  variant: 'default'
});

export const themeState = writable<ThemeState>({
  currentMode: 'light',
  resolvedMode: 'light',
  variant: 'default',
  isSystemDark: false
});

// Derived store for computed theme values
export const computedTheme = derived(
  [themeConfig, themeState],
  ([$config, $state]) => {
    const baseColors = $config.customColors ? 
      { ...colors, ...$config.customColors } : colors;
    
    const themeColors = $state.resolvedMode === 'dark' ? 
      { ...baseColors, ...darkMode.colors } : baseColors;
    
    const themeVariants = $config.customVariants ? 
      { ...variants, ...$config.customVariants } : variants;

    return {
      colors: themeColors,
      variants: themeVariants,
      mode: $state.resolvedMode,
      variant: $state.variant
    };
  }
);

class ThemeManager {
  private mediaQuery: MediaQueryList | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.initializeSystemThemeDetection();
      this.loadStoredTheme();
    }
  }

  private initializeSystemThemeDetection() {
    if (typeof window !== 'undefined' && window.matchMedia) {
      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      // Update system theme state
      this.updateSystemTheme();
      
      // Listen for system theme changes
      this.mediaQuery.addEventListener('change', () => {
        this.updateSystemTheme();
      });
    }
  }

  private updateSystemTheme() {
    if (this.mediaQuery) {
      themeState.update(state => ({
        ...state,
        isSystemDark: this.mediaQuery!.matches,
        resolvedMode: state.currentMode === 'auto' 
          ? (this.mediaQuery!.matches ? 'dark' : 'light')
          : state.currentMode === 'dark' ? 'dark' : 'light'
      }));
      
      this.updateDocumentClasses();
      this.updateCSSCustomProperties();
    }
  }

  private loadStoredTheme() {
    if (typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem('wakedock-theme');
      if (stored) {
        try {
          const config = JSON.parse(stored) as ThemeConfig;
          this.setTheme(config);
        } catch (e) {
          console.warn('Failed to parse stored theme config');
        }
      }
    }
  }

  private saveTheme(config: ThemeConfig) {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('wakedock-theme', JSON.stringify(config));
    }
  }

  private updateDocumentClasses() {
    if (typeof document !== 'undefined') {
      const html = document.documentElement;
      const currentState = this.getCurrentState();
      
      // Update mode classes
      html.classList.remove('light', 'dark');
      html.classList.add(currentState.resolvedMode);
      
      // Update variant classes
      html.classList.remove('theme-default', 'theme-compact', 'theme-comfortable');
      html.classList.add(`theme-${currentState.variant}`);
    }
  }

  private updateCSSCustomProperties() {
    // Update CSS custom properties based on current theme
    cssBridge.applyToDocument();
  }

  // Public API
  setMode(mode: ThemeMode) {
    themeConfig.update(config => ({ ...config, mode }));
    themeState.update(state => {
      const resolvedMode = mode === 'auto' 
        ? (state.isSystemDark ? 'dark' : 'light')
        : mode;
      
      return { ...state, currentMode: mode, resolvedMode };
    });
    
    this.updateDocumentClasses();
    this.updateCSSCustomProperties();
    this.saveTheme(this.getCurrentConfig());
  }

  setVariant(variant: ThemeVariant) {
    themeConfig.update(config => ({ ...config, variant }));
    themeState.update(state => ({ ...state, variant }));
    
    this.updateDocumentClasses();
    this.saveTheme(this.getCurrentConfig());
  }

  setTheme(config: ThemeConfig) {
    themeConfig.set(config);
    themeState.update(state => ({
      ...state,
      currentMode: config.mode,
      variant: config.variant,
      resolvedMode: config.mode === 'auto' 
        ? (state.isSystemDark ? 'dark' : 'light')
        : config.mode
    }));
    
    this.updateDocumentClasses();
    this.updateCSSCustomProperties();
    this.saveTheme(config);
  }

  toggleMode() {
    const currentState = this.getCurrentState();
    const nextMode: ThemeMode = currentState.currentMode === 'light' ? 'dark' : 'light';
    this.setMode(nextMode);
  }

  getCurrentConfig(): ThemeConfig {
    let config: ThemeConfig = { mode: 'light', variant: 'default' };
    themeConfig.subscribe(c => config = c)();
    return config;
  }

  getCurrentState(): ThemeState {
    let state: ThemeState = { 
      currentMode: 'light', 
      resolvedMode: 'light', 
      variant: 'default', 
      isSystemDark: false 
    };
    themeState.subscribe(s => state = s)();
    return state;
  }

  // Advanced customization
  setCustomColors(customColors: Partial<typeof colors>) {
    themeConfig.update(config => ({ ...config, customColors }));
    this.updateCSSCustomProperties();
    this.saveTheme(this.getCurrentConfig());
  }

  setCustomVariants(customVariants: Partial<typeof variants>) {
    themeConfig.update(config => ({ ...config, customVariants }));
    this.saveTheme(this.getCurrentConfig());
  }

  // Reset to defaults
  reset() {
    this.setTheme({ mode: 'light', variant: 'default' });
  }

  // Export current theme as JSON
  exportTheme(): string {
    const theme = this.getCurrentConfig();
    return JSON.stringify(theme, null, 2);
  }

  // Import theme from JSON
  importTheme(themeJson: string): boolean {
    try {
      const config = JSON.parse(themeJson) as ThemeConfig;
      this.setTheme(config);
      return true;
    } catch (e) {
      console.error('Invalid theme JSON:', e);
      return false;
    }
  }
}

// Create singleton instance
export const themeManager = new ThemeManager();

// Convenience stores for components
export const isDarkMode: Readable<boolean> = derived(
  themeState,
  $state => $state.resolvedMode === 'dark'
);

export const currentThemeMode: Readable<ThemeMode> = derived(
  themeState,
  $state => $state.currentMode
);

export const currentVariant: Readable<ThemeVariant> = derived(
  themeState,
  $state => $state.variant
);

// Utility functions for components
export function getThemeClass(baseClass: string, variants?: Record<string, string>): string {
  if (!variants) return baseClass;
  
  const state = themeManager.getCurrentState();
  const variantClass = variants[state.resolvedMode] || variants[state.variant];
  
  return variantClass ? `${baseClass} ${variantClass}` : baseClass;
}

export default themeManager;