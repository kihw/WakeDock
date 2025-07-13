/**
 * Accessibility Utilities for WakeDock Design System
 * WCAG 2.1 AA compliance utilities and helpers
 */

// Color contrast ratios for WCAG compliance
export const WCAG_CONTRAST_RATIOS = {
  AA_NORMAL: 4.5,
  AA_LARGE: 3,
  AAA_NORMAL: 7,
  AAA_LARGE: 4.5
} as const;

// Large text threshold (18pt or 14pt bold)
export const LARGE_TEXT_SIZE = {
  PT_18: '1.125rem', // 18px
  PT_14_BOLD: '0.875rem' // 14px
} as const;

/**
 * Convert hex color to RGB values
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      }
    : null;
}

/**
 * Calculate relative luminance of a color
 */
function getLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map((c) => {
    const srgb = c / 255;
    return srgb <= 0.03928 ? srgb / 12.92 : Math.pow((srgb + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Calculate contrast ratio between two colors
 */
export function getContrastRatio(color1: string, color2: string): number {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);

  if (!rgb1 || !rgb2) {
    throw new Error('Invalid hex color format');
  }

  const lum1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
  const lum2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);

  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);

  return (brightest + 0.05) / (darkest + 0.05);
}

/**
 * Check if color combination meets WCAG contrast requirements
 */
export function meetsContrastRequirement(
  foreground: string,
  background: string,
  level: 'AA' | 'AAA' = 'AA',
  isLargeText = false
): boolean {
  const ratio = getContrastRatio(foreground, background);
  const requirement = isLargeText
    ? level === 'AA' ? WCAG_CONTRAST_RATIOS.AA_LARGE : WCAG_CONTRAST_RATIOS.AAA_LARGE
    : level === 'AA' ? WCAG_CONTRAST_RATIOS.AA_NORMAL : WCAG_CONTRAST_RATIOS.AAA_NORMAL;

  return ratio >= requirement;
}

/**
 * Accessibility utilities for common patterns
 */
export const accessibilityUtils = {
  /**
   * Generate unique IDs for accessibility attributes
   */
  generateId: (prefix = 'a11y'): string => {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * Build proper ARIA described-by relationships
   */
  buildDescribedBy: (ids: (string | undefined)[]): string | undefined => {
    const validIds = ids.filter(Boolean);
    return validIds.length > 0 ? validIds.join(' ') : undefined;
  },

  /**
   * Create screen reader only text
   */
  srOnly: (text: string): string => {
    return `<span class="sr-only">${text}</span>`;
  },

  /**
   * Validation for focus management
   */
  isFocusable: (element: HTMLElement): boolean => {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ];

    return focusableSelectors.some(selector => element.matches(selector));
  },

  /**
   * Get all focusable elements within a container
   */
  getFocusableElements: (container: HTMLElement): HTMLElement[] => {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ');

    return Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[];
  },

  /**
   * Trap focus within a container (for modals, dropdowns)
   */
  trapFocus: (container: HTMLElement): () => void => {
    const focusableElements = accessibilityUtils.getFocusableElements(container);
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  },

  /**
   * Announce message to screen readers
   */
  announce: (message: string, priority: 'polite' | 'assertive' = 'polite'): void => {
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    announcer.textContent = message;

    document.body.appendChild(announcer);

    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcer);
    }, 1000);
  }
};

/**
 * ARIA patterns for common components
 */
export const ariaPatterns = {
  button: {
    required: ['role', 'aria-label'],
    optional: ['aria-describedby', 'aria-expanded', 'aria-pressed']
  },
  
  textbox: {
    required: ['role', 'aria-label'],
    optional: ['aria-describedby', 'aria-required', 'aria-invalid', 'aria-multiline']
  },
  
  combobox: {
    required: ['role', 'aria-label', 'aria-expanded'],
    optional: ['aria-describedby', 'aria-activedescendant', 'aria-autocomplete']
  },
  
  dialog: {
    required: ['role', 'aria-labelledby'],
    optional: ['aria-describedby', 'aria-modal']
  },
  
  navigation: {
    required: ['role', 'aria-label'],
    optional: ['aria-describedby']
  },
  
  tab: {
    required: ['role', 'aria-selected'],
    optional: ['aria-controls', 'aria-describedby']
  },
  
  tabpanel: {
    required: ['role', 'aria-labelledby'],
    optional: ['aria-describedby']
  }
};

/**
 * Common keyboard event handlers
 */
export const keyboardHandlers = {
  /**
   * Handle arrow key navigation in lists
   */
  arrowNavigation: (
    event: KeyboardEvent,
    items: HTMLElement[],
    currentIndex: number,
    onSelect?: (index: number) => void
  ): number => {
    let newIndex = currentIndex;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        break;
      case 'ArrowUp':
        event.preventDefault();
        newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        break;
      case 'Home':
        event.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        event.preventDefault();
        newIndex = items.length - 1;
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        onSelect?.(currentIndex);
        return currentIndex;
    }

    if (newIndex !== currentIndex) {
      items[newIndex]?.focus();
    }

    return newIndex;
  },

  /**
   * Handle escape key for closing components
   */
  escapeHandler: (event: KeyboardEvent, onEscape: () => void): void => {
    if (event.key === 'Escape') {
      event.preventDefault();
      onEscape();
    }
  }
};

/**
 * Validation helpers for accessibility
 */
export const accessibilityValidation = {
  /**
   * Check if element has proper labeling
   */
  hasProperLabeling: (element: HTMLElement): boolean => {
    const hasAriaLabel = element.hasAttribute('aria-label');
    const hasAriaLabelledBy = element.hasAttribute('aria-labelledby');
    const hasAssociatedLabel = element.id && document.querySelector(`label[for="${element.id}"]`);

    return hasAriaLabel || hasAriaLabelledBy || hasAssociatedLabel;
  },

  /**
   * Check if interactive element has appropriate role
   */
  hasAppropriateRole: (element: HTMLElement): boolean => {
    const tagName = element.tagName.toLowerCase();
    const role = element.getAttribute('role');

    // Native semantic elements don't need explicit roles
    const semanticElements = ['button', 'a', 'input', 'select', 'textarea'];
    if (semanticElements.includes(tagName)) {
      return true;
    }

    // Non-semantic elements with interaction should have appropriate roles
    const hasInteraction = element.onclick || element.onkeydown || element.hasAttribute('tabindex');
    if (hasInteraction) {
      return !!role;
    }

    return true;
  },

  /**
   * Check if form controls have proper error handling
   */
  hasProperErrorHandling: (element: HTMLElement): boolean => {
    const hasAriaInvalid = element.hasAttribute('aria-invalid');
    const hasAriaDescribedBy = element.hasAttribute('aria-describedby');
    
    return hasAriaInvalid && hasAriaDescribedBy;
  }
};

/**
 * Focus management utilities
 */
export const focusManagement = {
  /**
   * Set focus to element and scroll into view if needed
   */
  setFocus: (element: HTMLElement, options?: { preventScroll?: boolean }): void => {
    element.focus(options);
    
    if (!options?.preventScroll) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  },

  /**
   * Manage focus restoration
   */
  createFocusManager: (): {
    save: () => void;
    restore: () => void;
  } => {
    let previousFocus: HTMLElement | null = null;

    return {
      save: () => {
        previousFocus = document.activeElement as HTMLElement;
      },
      restore: () => {
        if (previousFocus && document.contains(previousFocus)) {
          focusManagement.setFocus(previousFocus);
        }
      }
    };
  }
};

/**
 * Screen reader utilities
 */
export const screenReader = {
  /**
   * Create visually hidden but screen reader accessible text
   */
  createSROnlyElement: (text: string): HTMLElement => {
    const element = document.createElement('span');
    element.className = 'sr-only';
    element.textContent = text;
    return element;
  },

  /**
   * Update screen reader announcements
   */
  updateAnnouncement: (element: HTMLElement, message: string): void => {
    element.textContent = message;
  }
};