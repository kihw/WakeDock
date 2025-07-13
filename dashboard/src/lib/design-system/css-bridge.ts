/**
 * CSS Custom Properties Bridge
 * Maps design tokens to CSS custom properties for components using var() syntax
 */

import { colors } from './tokens';

export const cssBridge = {
  // Generate CSS custom properties from design tokens
  getCSSCustomProperties: () => {
    return {
      // Primary color mappings
      '--color-primary': colors.primary[600],
      '--color-primary-hover': colors.primary[700],
      '--color-primary-light': colors.primary[100],
      
      // Secondary/Text colors
      '--color-text-primary': colors.secondary[900],
      '--color-text-secondary': colors.secondary[600],
      '--color-text-tertiary': colors.secondary[500],
      
      // Border colors
      '--color-border': colors.secondary[300],
      '--color-border-light': colors.secondary[200],
      '--color-border-dark': colors.secondary[700],
      
      // Background colors
      '--color-bg-primary': colors.secondary[50],
      '--color-bg-secondary': colors.secondary[100],
      '--color-bg-tertiary': colors.secondary[800],
      
      // State colors
      '--color-success': colors.success[600],
      '--color-success-bg': colors.success[100],
      '--color-warning': colors.warning[600],
      '--color-warning-bg': colors.warning[100],
      '--color-error': colors.error[600],
      '--color-error-bg': colors.error[100],
      
      // Focus and interaction
      '--color-focus': colors.primary[500],
      '--color-hover': colors.secondary[100],
    };
  },

  // Generate CSS string for injection
  getCSSString: () => {
    const properties = cssBridge.getCSSCustomProperties();
    const cssRules = Object.entries(properties)
      .map(([property, value]) => `  ${property}: ${value};`)
      .join('\n');
    
    return `:root {\n${cssRules}\n}`;
  },

  // Apply CSS custom properties to document
  applyToDocument: () => {
    if (typeof document !== 'undefined') {
      const styleId = 'design-system-css-bridge';
      let styleElement = document.getElementById(styleId) as HTMLStyleElement;
      
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = styleId;
        document.head.appendChild(styleElement);
      }
      
      styleElement.textContent = cssBridge.getCSSString();
    }
  }
};

// Auto-apply on module load in browser environment
if (typeof window !== 'undefined') {
  cssBridge.applyToDocument();
}

export default cssBridge;