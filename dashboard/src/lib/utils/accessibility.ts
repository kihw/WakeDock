/**
 * Accessibility Utilities
 * Tools and helpers for accessibility compliance and improvement
 */

export interface A11yConfig {
  enableAnnouncements: boolean;
  enableFocusManagement: boolean;
  enableKeyboardNavigation: boolean;
  announceDelay: number;
}

/**
 * Gestionnaire d'accessibilité global
 */
class AccessibilityManager {
  private config: A11yConfig;
  private announcer?: HTMLElement;
  private focusStack: HTMLElement[] = [];

  constructor(config: Partial<A11yConfig> = {}) {
    this.config = {
      enableAnnouncements: true,
      enableFocusManagement: true,
      enableKeyboardNavigation: true,
      announceDelay: 100,
      ...config,
    };

    if (typeof window !== 'undefined') {
      this.init();
    }
  }

  private init(): void {
    if (this.config.enableAnnouncements) {
      this.createAnnouncer();
    }

    if (this.config.enableKeyboardNavigation) {
      this.setupKeyboardNavigation();
    }
  }

  /**
   * Créer un élément pour les annonces screen reader
   */
  private createAnnouncer(): void {
    this.announcer = document.createElement('div');
    this.announcer.setAttribute('aria-live', 'polite');
    this.announcer.setAttribute('aria-atomic', 'true');
    this.announcer.style.position = 'absolute';
    this.announcer.style.left = '-10000px';
    this.announcer.style.width = '1px';
    this.announcer.style.height = '1px';
    this.announcer.style.overflow = 'hidden';
    document.body.appendChild(this.announcer);
  }

  /**
   * Configuration de la navigation clavier
   */
  private setupKeyboardNavigation(): void {
    document.addEventListener('keydown', (event) => {
      // Échap pour fermer les modales
      if (event.key === 'Escape') {
        const openModal = document.querySelector('[role="dialog"][aria-hidden="false"]');
        if (openModal) {
          this.closeModal(openModal as HTMLElement);
        }
      }

      // Tab piège pour les modales
      if (event.key === 'Tab') {
        const activeModal = document.querySelector('[role="dialog"][aria-hidden="false"]');
        if (activeModal) {
          this.trapFocus(event, activeModal as HTMLElement);
        }
      }
    });
  }

  /**
   * Piège le focus dans un élément
   */
  private trapFocus(event: KeyboardEvent, container: HTMLElement): void {
    const focusableElements = this.getFocusableElements(container);
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey) {
      if (document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }
  }

  /**
   * Annonce un message aux lecteurs d'écran
   */
  announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    if (!this.config.enableAnnouncements || !this.announcer) return;

    this.announcer.setAttribute('aria-live', priority);

    // Délai pour s'assurer que le message est lu
    setTimeout(() => {
      if (this.announcer) {
        this.announcer.textContent = message;
      }
    }, this.config.announceDelay);

    // Nettoyer après un délai
    setTimeout(() => {
      if (this.announcer) {
        this.announcer.textContent = '';
      }
    }, this.config.announceDelay + 3000);
  }

  /**
   * Gère le focus lors de l'ouverture d'une modale
   */
  openModal(modal: HTMLElement): void {
    if (!this.config.enableFocusManagement) return;

    // Sauvegarder l'élément actuellement focusé
    const currentFocus = document.activeElement as HTMLElement;
    if (currentFocus) {
      this.focusStack.push(currentFocus);
    }

    // Configurer la modale
    modal.setAttribute('aria-hidden', 'false');
    modal.setAttribute('role', 'dialog');

    // Focuser le premier élément focusable ou la modale elle-même
    const focusableElements = this.getFocusableElements(modal);
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    } else if (modal.tabIndex >= 0) {
      modal.focus();
    }

    // Ajouter un backdrop si nécessaire
    this.addModalBackdrop(modal);
  }

  /**
   * Gère le focus lors de la fermeture d'une modale
   */
  closeModal(modal: HTMLElement): void {
    modal.setAttribute('aria-hidden', 'true');
    modal.removeAttribute('role');

    // Restaurer le focus précédent
    if (this.config.enableFocusManagement && this.focusStack.length > 0) {
      const previousFocus = this.focusStack.pop();
      if (previousFocus && document.contains(previousFocus)) {
        previousFocus.focus();
      }
    }

    // Supprimer le backdrop
    this.removeModalBackdrop();
  }

  /**
   * Ajoute un backdrop pour la modale
   */
  private addModalBackdrop(modal: HTMLElement): void {
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.style.position = 'fixed';
    backdrop.style.top = '0';
    backdrop.style.left = '0';
    backdrop.style.width = '100%';
    backdrop.style.height = '100%';
    backdrop.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    backdrop.style.zIndex = '999';
    backdrop.setAttribute('aria-hidden', 'true');

    backdrop.addEventListener('click', () => this.closeModal(modal));

    document.body.appendChild(backdrop);
  }

  /**
   * Supprime le backdrop de la modale
   */
  private removeModalBackdrop(): void {
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
      backdrop.remove();
    }
  }

  /**
   * Obtient tous les éléments focusables dans un conteneur
   */
  getFocusableElements(container: HTMLElement): HTMLElement[] {
    const focusableSelectors = [
      'button:not([disabled])',
      '[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable]',
    ].join(', ');

    const elements = container.querySelectorAll(focusableSelectors) as NodeListOf<HTMLElement>;
    return Array.from(elements).filter((el) => {
      return (
        !el.hidden &&
        el.offsetWidth > 0 &&
        el.offsetHeight > 0 &&
        window.getComputedStyle(el).visibility !== 'hidden'
      );
    });
  }

  /**
   * Vérifie le contraste des couleurs
   */
  checkColorContrast(
    foreground: string,
    background: string
  ): { ratio: number; passes: { aa: boolean; aaa: boolean } } {
    const getLuminance = (color: string): number => {
      // Conversion simplifiée - pour une implémentation complète,
      // utiliser une bibliothèque comme chroma.js
      const rgb = this.hexToRgb(color);
      if (!rgb) return 0;

      const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((c) => {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      });

      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const l1 = getLuminance(foreground);
    const l2 = getLuminance(background);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

    return {
      ratio,
      passes: {
        aa: ratio >= 4.5,
        aaa: ratio >= 7,
      },
    };
  }

  /**
   * Convertit une couleur hex en RGB
   */
  private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
      : null;
  }

  /**
   * Ajoute des propriétés ARIA à un élément
   */
  setAriaAttributes(element: HTMLElement, attributes: Record<string, string>): void {
    Object.entries(attributes).forEach(([key, value]) => {
      element.setAttribute(key.startsWith('aria-') ? key : `aria-${key}`, value);
    });
  }

  /**
   * Génère un ID unique pour les éléments
   */
  generateId(prefix = 'a11y'): string {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Instance singleton
const a11yManager = new AccessibilityManager();

// Exported functions for easier usage in components
/**
 * Annonce un message pour les lecteurs d'écran
 *
 * @param message - Le message à annoncer
 * @param priority - La priorité (polite ou assertive)
 */
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  a11yManager.announce(message, priority);
}

/**
 * Alias pour announce - permet d'utiliser un nom plus explicite
 *
 * @param message - Le message à annoncer
 * @param priority - La priorité (polite ou assertive)
 */
export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
): void {
  a11yManager.announce(message, priority);
}

/**
 * Gère le focus d'un élément
 *
 * @param element - L'élément à focus
 */
export function manageFocus(element: HTMLElement): void {
  if (element) {
    element.focus();
  }
}

/**
 * Piège le focus dans un conteneur
 *
 * @param container - L'élément qui contient le focus
 */
export function trapFocus(container: HTMLElement): { destroy: () => void } | null {
  // Cette fonction est appelée directement avec un élément, non pas un événement
  // C'est donc une implémentation simplifiée par rapport à celle interne
  if (container) {
    container.setAttribute('tabindex', '-1');
    container.focus();
    return {
      destroy: () => {
        // Cleanup logic if needed
      },
    };
  }
  return null;
}

/**
 * Restaure le focus à l'élément précédent
 *
 * @param previousElement - L'élément qui avait le focus avant
 */
export function restoreFocus(previousElement: HTMLElement | null): void {
  if (previousElement) {
    previousElement.focus();
  }
}

/**
 * Validates form accessibility requirements
 */
export function validateFormAccessibility(form: HTMLFormElement): {
  isValid: boolean;
  issues: string[];
} {
  const issues: string[] = [];

  // Check for form labels
  const inputs = form.querySelectorAll('input, select, textarea');
  inputs.forEach((input: Element) => {
    const htmlInput = input as HTMLInputElement;
    const id = htmlInput.id;
    const label = form.querySelector(`label[for="${id}"]`);
    const ariaLabel = htmlInput.getAttribute('aria-label');
    const ariaLabelledBy = htmlInput.getAttribute('aria-labelledby');

    if (!label && !ariaLabel && !ariaLabelledBy) {
      issues.push(`Input "${htmlInput.name || htmlInput.type}" lacks proper labeling`);
    }
  });

  // Check for required field indicators
  const requiredInputs = form.querySelectorAll(
    'input[required], select[required], textarea[required]'
  );
  requiredInputs.forEach((input: Element) => {
    const htmlInput = input as HTMLInputElement;
    const ariaRequired = htmlInput.getAttribute('aria-required');
    if (!ariaRequired) {
      issues.push(
        `Required field "${htmlInput.name || htmlInput.type}" should have aria-required="true"`
      );
    }
  });

  return {
    isValid: issues.length === 0,
    issues,
  };
}

/**
 * Generates accessible error messages for form fields
 */
export function getAccessibleErrorMessage(fieldName: string, errorMessage: string): string {
  const fieldDisplayName =
    fieldName.charAt(0).toUpperCase() + fieldName.slice(1).replace(/([A-Z])/g, ' $1');
  return `${fieldDisplayName} error: ${errorMessage}`;
}

/**
 * Enhances form accessibility with ARIA attributes and keyboard navigation
 */
export function enhanceFormAccessibility(form: HTMLFormElement): void {
  // Add role and aria-label to form if not present
  if (!form.getAttribute('role')) {
    form.setAttribute('role', 'form');
  }

  if (!form.getAttribute('aria-label') && !form.getAttribute('aria-labelledby')) {
    form.setAttribute('aria-label', 'Registration form');
  }

  // Enhance all form inputs
  const inputs = form.querySelectorAll('input, select, textarea');
  inputs.forEach((input: Element, index: number) => {
    const htmlInput = input as HTMLInputElement;

    // Ensure each input has an ID
    if (!htmlInput.id) {
      htmlInput.id = `form-input-${index}`;
    }

    // Add aria-required for required fields
    if (htmlInput.hasAttribute('required') && !htmlInput.getAttribute('aria-required')) {
      htmlInput.setAttribute('aria-required', 'true');
    }

    // Add aria-invalid for validation
    if (!htmlInput.getAttribute('aria-invalid')) {
      htmlInput.setAttribute('aria-invalid', 'false');
    }

    // Setup error announcement container
    const errorId = `${htmlInput.id}-error`;
    let errorContainer = form.querySelector(`#${errorId}`);
    if (!errorContainer) {
      errorContainer = document.createElement('div');
      errorContainer.id = errorId;
      errorContainer.setAttribute('aria-live', 'polite');
      errorContainer.setAttribute('aria-atomic', 'true');
      errorContainer.className = 'sr-only';
      htmlInput.parentNode?.insertBefore(errorContainer, htmlInput.nextSibling);
    }

    // Link input to error container
    const ariaDescribedBy = htmlInput.getAttribute('aria-describedby');
    if (!ariaDescribedBy || !ariaDescribedBy.includes(errorId)) {
      htmlInput.setAttribute(
        'aria-describedby',
        ariaDescribedBy ? `${ariaDescribedBy} ${errorId}` : errorId
      );
    }
  });

  // Add keyboard navigation enhancements
  form.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && event.target instanceof HTMLInputElement) {
      const inputs = Array.from(form.querySelectorAll('input, select, textarea')) as HTMLElement[];
      const currentIndex = inputs.indexOf(event.target);
      const nextInput = inputs[currentIndex + 1];

      if (nextInput && event.target.type !== 'submit') {
        event.preventDefault();
        nextInput.focus();
      }
    }
  });
}

// Exporter l'instance pour usage avancé
export default a11yManager;

// Instance globale
export const a11y = new AccessibilityManager();

// Utilitaires d'accessibilité
export const a11yUtils = {
  /**
   * Vérifie si un élément est focusable
   */
  isFocusable: (element: HTMLElement): boolean => {
    return a11y.getFocusableElements(element.parentElement || document.body).includes(element);
  },

  /**
   * Crée un label invisible pour les lecteurs d'écran
   */
  createScreenReaderLabel: (text: string, id?: string): HTMLElement => {
    const label = document.createElement('span');
    if (id) label.id = id;
    label.textContent = text;
    label.className = 'sr-only';
    label.style.position = 'absolute';
    label.style.left = '-10000px';
    label.style.width = '1px';
    label.style.height = '1px';
    label.style.overflow = 'hidden';
    return label;
  },

  /**
   * Associe un label à un input
   */
  linkLabelToInput: (input: HTMLInputElement, labelText: string): void => {
    const labelId = a11y.generateId('label');
    const label = a11yUtils.createScreenReaderLabel(labelText, labelId);

    input.setAttribute('aria-labelledby', labelId);
    input.parentElement?.appendChild(label);
  },

  /**
   * Ajoute une description à un élément
   */
  addDescription: (element: HTMLElement, description: string): void => {
    const descId = a11y.generateId('desc');
    const descElement = a11yUtils.createScreenReaderLabel(description, descId);

    element.setAttribute('aria-describedby', descId);
    element.parentElement?.appendChild(descElement);
  },

  /**
   * Crée un bouton accessible
   */
  createAccessibleButton: (text: string, onClick?: () => void): HTMLButtonElement => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = text;
    button.setAttribute('aria-label', text);

    if (onClick) {
      button.addEventListener('click', onClick);
    }

    return button;
  },

  /**
   * Vérifie si les animations sont réduites
   */
  prefersReducedMotion: (): boolean => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },

  /**
   * Vérifie le thème préféré
   */
  prefersColorScheme: (): 'light' | 'dark' => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  },

  /**
   * Ajoute un skip link
   */
  addSkipLink: (targetId: string, text = 'Aller au contenu principal'): void => {
    const skipLink = document.createElement('a');
    skipLink.href = `#${targetId}`;
    skipLink.textContent = text;
    skipLink.className = 'skip-link';
    skipLink.style.position = 'absolute';
    skipLink.style.top = '-40px';
    skipLink.style.left = '6px';
    skipLink.style.background = '#000';
    skipLink.style.color = '#fff';
    skipLink.style.padding = '8px';
    skipLink.style.textDecoration = 'none';
    skipLink.style.zIndex = '1000';

    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';
    });

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);
  },

  /**
   * Notifie un changement d'état
   */
  announceStateChange: (element: HTMLElement, newState: string): void => {
    element.setAttribute('aria-live', 'polite');
    a11y.announce(`État changé: ${newState}`);
  },

  /**
   * Crée une liste accessible
   */
  makeListAccessible: (list: HTMLElement, itemRole = 'listitem'): void => {
    list.setAttribute('role', 'list');
    const items = list.children;

    for (let i = 0; i < items.length; i++) {
      const item = items[i] as HTMLElement;
      item.setAttribute('role', itemRole);
      item.setAttribute('aria-setsize', items.length.toString());
      item.setAttribute('aria-posinset', (i + 1).toString());
    }
  },

  /**
   * Crée un group de boutons radio accessible
   */
  makeRadioGroupAccessible: (container: HTMLElement, groupLabel: string): void => {
    container.setAttribute('role', 'radiogroup');
    container.setAttribute('aria-labelledby', a11y.generateId('radio-label'));

    const label = a11yUtils.createScreenReaderLabel(groupLabel);
    container.appendChild(label);

    const radios = container.querySelectorAll('input[type="radio"]');
    radios.forEach((radio, index) => {
      radio.setAttribute('role', 'radio');
      if (index === 0) {
        radio.setAttribute('tabindex', '0');
      } else {
        radio.setAttribute('tabindex', '-1');
      }
    });
  },
};

// Enhanced Focus Management for Security and Accessibility
export class SecureFocusManager {
  private focusStack: HTMLElement[] = [];
  private initialFocus: HTMLElement | null = null;
  private securityChecks = true;

  /**
   * Trap focus within a container with security validation
   */
  secureTrapFocus(container: HTMLElement, options: { validateOrigin?: boolean } = {}): void {
    // Security check: validate container is part of current document
    if (this.securityChecks && !document.contains(container)) {
      console.warn('Focus trap attempted on element not in document');
      return;
    }

    const focusableElements = this.getFocusableElements(container);
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      // Security: validate event origin
      if (options.validateOrigin && !e.isTrusted) {
        return;
      }

      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);

    // Store original focus
    this.initialFocus = document.activeElement as HTMLElement;

    // Focus first element
    firstElement.focus();

    // Store cleanup function
    container.setAttribute('data-focus-trap', 'true');
  }

  /**
   * Get all focusable elements with security filtering
   */
  private getFocusableElements(container: HTMLElement): HTMLElement[] {
    const selector = [
      'a[href]:not([tabindex="-1"])',
      'button:not([disabled]):not([tabindex="-1"])',
      'input:not([disabled]):not([tabindex="-1"])',
      'select:not([disabled]):not([tabindex="-1"])',
      'textarea:not([disabled]):not([tabindex="-1"])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]:not([tabindex="-1"])',
    ].join(', ');

    const elements = Array.from(container.querySelectorAll(selector)) as HTMLElement[];

    // Security filter: remove elements with suspicious attributes
    return elements.filter((element) => {
      // Check for malicious onclick handlers
      const onclickAttr = element.getAttribute('onclick');
      if (onclickAttr && /javascript:|data:|vbscript:/i.test(onclickAttr)) {
        console.warn('Suspicious onclick attribute detected, excluding from focus trap');
        return false;
      }

      // Check for suspicious href values
      const href = element.getAttribute('href');
      if (href && /javascript:|data:|vbscript:/i.test(href)) {
        console.warn('Suspicious href attribute detected, excluding from focus trap');
        return false;
      }

      return true;
    });
  }
}

// Enhanced Color Contrast with Security
export class SecureColorContrast {
  /**
   * Validate color values for security before processing
   */
  static validateColor(color: string): boolean {
    // Check for CSS injection attempts
    if (/<|>|javascript:|expression\(|url\(/i.test(color)) {
      console.warn('Potentially malicious color value detected:', color);
      return false;
    }

    // Validate hex format
    const hexPattern = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
    return hexPattern.test(color);
  }

  /**
   * Secure contrast ratio calculation
   */
  static calculateRatio(color1: string, color2: string): number {
    if (!this.validateColor(color1) || !this.validateColor(color2)) {
      return 0;
    }

    const rgb1 = this.hexToRgb(color1);
    const rgb2 = this.hexToRgb(color2);

    if (!rgb1 || !rgb2) return 0;

    const l1 = this.getLuminance(rgb1);
    const l2 = this.getLuminance(rgb2);

    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);

    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Check WCAG compliance with enhanced validation
   */
  static meetsWCAG(
    color1: string,
    color2: string,
    level: 'AA' | 'AAA' = 'AA',
    size: 'normal' | 'large' = 'normal'
  ): { compliant: boolean; ratio: number; recommendation?: string } {
    const ratio = this.calculateRatio(color1, color2);

    const requirements = {
      AA: { normal: 4.5, large: 3 },
      AAA: { normal: 7, large: 4.5 },
    };

    const required = requirements[level][size];
    const compliant = ratio >= required;

    let recommendation: string | undefined;
    if (!compliant) {
      recommendation = `Contrast ratio ${ratio.toFixed(2)} is below the required ${required}. Consider adjusting colors.`;
    }

    return { compliant, ratio, recommendation };
  }

  private static hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
      : null;
  }

  private static getLuminance(rgb: { r: number; g: number; b: number }): number {
    const { r, g, b } = rgb;

    const [rs, gs, bs] = [r, g, b].map((c) => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }
}

// Secure Form Accessibility with Enhanced Validation
export class SecureFormAccessibility {
  /**
   * Enhanced form validation with security and accessibility
   */
  static validateField(
    field: HTMLInputElement,
    validationFn: (value: string) => { valid: boolean; message?: string },
    options: { sanitizeInput?: boolean; maxLength?: number } = {}
  ): boolean {
    let value = field.value;

    // Security: sanitize input if requested
    if (options.sanitizeInput) {
      value = value.replace(/<[^>]*>/g, '').trim();
      if (value !== field.value) {
        field.value = value;
        console.warn('Input sanitized for security');
      }
    }

    // Security: enforce max length
    if (options.maxLength && value.length > options.maxLength) {
      value = value.substring(0, options.maxLength);
      field.value = value;
    }

    const result = validationFn(value);
    const errorId = `${field.id}-error`;
    let errorElement = document.getElementById(errorId);

    if (!result.valid) {
      // Create or update error message
      if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = errorId;
        errorElement.className = 'field-error';
        errorElement.setAttribute('role', 'alert');
        errorElement.setAttribute('aria-atomic', 'true');
        field.parentNode?.insertBefore(errorElement, field.nextSibling);
      }

      // Sanitize error message to prevent XSS
      const sanitizedMessage = (result.message || 'Invalid input')
        .replace(/<[^>]*>/g, '')
        .substring(0, 200);

      errorElement.textContent = sanitizedMessage;
      field.setAttribute('aria-invalid', 'true');
      field.setAttribute('aria-describedby', errorId);
      field.classList.add('error');

      return false;
    } else {
      // Remove error state
      if (errorElement) {
        errorElement.remove();
      }

      field.setAttribute('aria-invalid', 'false');
      field.removeAttribute('aria-describedby');
      field.classList.remove('error');

      return true;
    }
  }

  /**
   * Enhanced form security and accessibility setup
   */
  static enhanceForm(form: HTMLFormElement, options: { enableSecurity?: boolean } = {}): void {
    const fields = form.querySelectorAll('input, select, textarea');

    fields.forEach((field, index) => {
      const htmlField = field as HTMLInputElement;

      // Security: validate field configuration
      if (options.enableSecurity) {
        // Remove dangerous attributes
        const dangerousAttrs = ['onclick', 'onerror', 'onload', 'onmouseover'];
        dangerousAttrs.forEach((attr) => {
          if (htmlField.hasAttribute(attr)) {
            console.warn(`Removing potentially dangerous attribute: ${attr}`);
            htmlField.removeAttribute(attr);
          }
        });
      }

      // Ensure field has ID
      if (!htmlField.id) {
        htmlField.id = `field-${index}`;
      }

      // Find associated label
      const labelElement = form.querySelector(`label[for="${htmlField.id}"]`) as HTMLLabelElement;
      if (!labelElement) {
        console.warn(`No label found for field ${htmlField.id}`);
      }

      // Add required indicator
      if (htmlField.required && labelElement) {
        const requiredSpan = document.createElement('span');
        requiredSpan.className = 'sr-only';
        requiredSpan.textContent = ' (required)';
        labelElement.appendChild(requiredSpan);
      }
    });
  }

  /**
   * Announce error message to screen readers
   */
  static announceError(message: string, priority: 'polite' | 'assertive' = 'assertive'): void {
    try {
      // Sanitize message to prevent XSS
      const sanitizedMessage = message.replace(/<[^>]*>/g, '').substring(0, 200);
      if (typeof a11yManager !== 'undefined' && a11yManager.announce) {
        a11yManager.announce(`Error: ${sanitizedMessage}`, priority);
      } else {
        // Fallback: use console for debugging
        console.error(`Accessibility Error: ${sanitizedMessage}`);
        // Try to announce via live region if available
        const liveRegion = document.querySelector('[aria-live]');
        if (liveRegion) {
          liveRegion.textContent = `Error: ${sanitizedMessage}`;
        }
      }
    } catch (error) {
      console.error('Failed to announce error:', error);
    }
  }

  /**
   * Announce change to screen readers
   */
  static announceChange(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    try {
      // Sanitize message to prevent XSS
      const sanitizedMessage = message.replace(/<[^>]*>/g, '').substring(0, 200);
      if (typeof a11yManager !== 'undefined' && a11yManager.announce) {
        a11yManager.announce(sanitizedMessage, priority);
      } else {
        // Fallback: use console for debugging
        console.log(`Accessibility Change: ${sanitizedMessage}`);
        // Try to announce via live region if available
        const liveRegion = document.querySelector('[aria-live]');
        if (liveRegion) {
          liveRegion.textContent = sanitizedMessage;
        }
      }
    } catch (error) {
      console.error('Failed to announce change:', error);
    }
  }
}

// Global secure accessibility instance
export const secureAccessibility = {
  focus: new SecureFocusManager(),
  color: SecureColorContrast,
  form: SecureFormAccessibility,
};

// Configuration par défaut selon l'environnement
if (typeof window !== 'undefined') {
  // Ajouter les styles CSS de base pour l'accessibilité
  const style = document.createElement('style');
  style.textContent = `
		.sr-only {
			position: absolute !important;
			width: 1px !important;
			height: 1px !important;
			padding: 0 !important;
			margin: -1px !important;
			overflow: hidden !important;
			clip: rect(0, 0, 0, 0) !important;
			white-space: nowrap !important;
			border: 0 !important;
		}
		
		*:focus-visible {
			outline: 2px solid #4A90E2;
			outline-offset: 2px;
		}
		
		.skip-link:focus {
			position: absolute;
			top: 6px !important;
			left: 6px;
			background: #000;
			color: #fff;
			padding: 8px;
			text-decoration: none;
			z-index: 1000;
		}
	`;
  document.head.appendChild(style);
}
