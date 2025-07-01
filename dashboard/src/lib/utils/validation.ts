/**
 * Validation Utilities
 * A comprehensive set of validation helpers for forms and inputs
 */

import { announce } from './accessibility';
import { secureAccessibility } from './accessibility';

// Types
export interface ValidationRule<T = string> {
    validate: (value: T, form?: Record<string, any>) => boolean;
    message: string;
}

export interface ValidationResult {
    valid: boolean;
    isValid: boolean; // Add alias for compatibility
    message?: string;
    errors?: Record<string, string>; // Add errors object
}

export interface FieldValidationOptions {
    announceResult?: boolean;
    announceOnlyErrors?: boolean;
    focusOnError?: boolean;
    scrollToError?: boolean;
    displayErrorIcon?: boolean;
}

// Validation patterns
export const PATTERNS = {
    EMAIL: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    URL: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/,
    ALPHANUMERIC: /^[a-zA-Z0-9]+$/,
    NUMERIC: /^[0-9]+$/,
    PASSWORD: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/,
    IPV4: /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
    PORT: /^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/,
    UUID: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
};

// Common validation rules
export const rules = {
    required: (message = 'This field is required'): ValidationRule => ({
        validate: (value: any) => {
            if (value === null || value === undefined) return false;
            if (typeof value === 'string') return value.trim().length > 0;
            if (Array.isArray(value)) return value.length > 0;
            return true;
        },
        message
    }),

    minLength: (length: number, message?: string): ValidationRule => ({
        validate: (value) => String(value).trim().length >= length,
        message: message || `Must be at least ${length} characters`
    }),

    maxLength: (length: number, message?: string): ValidationRule => ({
        validate: (value) => String(value).trim().length <= length,
        message: message || `Must be at most ${length} characters`
    }),

    pattern: (pattern: RegExp, message = 'Invalid format'): ValidationRule => ({
        validate: (value) => pattern.test(String(value)),
        message
    }),

    email: (message = 'Please enter a valid email address'): ValidationRule => ({
        validate: (value) => PATTERNS.EMAIL.test(String(value).trim()),
        message
    }),

    url: (message = 'Please enter a valid URL'): ValidationRule => ({
        validate: (value) => PATTERNS.URL.test(String(value).trim()),
        message
    }),

    numeric: (message = 'Must contain only numbers'): ValidationRule => ({
        validate: (value) => PATTERNS.NUMERIC.test(String(value).trim()),
        message
    }),

    alphanumeric: (message = 'Must contain only letters and numbers'): ValidationRule => ({
        validate: (value) => PATTERNS.ALPHANUMERIC.test(String(value).trim()),
        message
    }),

    match: (field: string, fieldName?: string, message?: string): ValidationRule => ({
        validate: (value, form) => {
            if (!form) return true; // Si pas de formulaire, on ne peut pas comparer
            return value === form[field];
        },
        message: message || `Must match ${fieldName || field} field`
    }),

    min: (min: number, message?: string): ValidationRule<number | string> => ({
        validate: (value) => {
            const numValue = typeof value === 'number' ? value : Number(value);
            return !isNaN(numValue) && numValue >= min;
        },
        message: message || `Must be at least ${min}`
    }),

    max: (max: number, message?: string): ValidationRule<number | string> => ({
        validate: (value) => {
            const numValue = typeof value === 'number' ? value : Number(value);
            return !isNaN(numValue) && numValue <= max;
        },
        message: message || `Must be at most ${max}`
    }),

    range: (min: number, max: number, message?: string): ValidationRule<number | string> => ({
        validate: (value) => {
            const numValue = typeof value === 'number' ? value : Number(value);
            return !isNaN(numValue) && numValue >= min && numValue <= max;
        },
        message: message || `Must be between ${min} and ${max}`
    }),

    password: (message = 'Password must be at least 8 characters with at least one letter and one number'): ValidationRule => ({
        validate: (value) => PATTERNS.PASSWORD.test(String(value)),
        message
    }),

    ipv4: (message = 'Please enter a valid IPv4 address'): ValidationRule => ({
        validate: (value) => PATTERNS.IPV4.test(String(value).trim()),
        message
    }),

    port: (message = 'Please enter a valid port number (1-65535)'): ValidationRule => ({
        validate: (value) => PATTERNS.PORT.test(String(value).trim()),
        message
    }),

    custom: <T>(validateFn: (value: T, form?: Record<string, any>) => boolean, message: string): ValidationRule<T> => ({
        validate: validateFn,
        message
    })
};

/**
 * Validates a value against one or more validation rules
 */
export function validate<T = string>(
    value: T,
    validationRules: ValidationRule<T>[],
    form?: Record<string, any>
): ValidationResult {
    if (!Array.isArray(validationRules)) {
        return { valid: true, isValid: true };
    }

    for (const rule of validationRules) {
        if (!rule.validate(value, form)) {
            return { valid: false, isValid: false, message: rule.message };
        }
    }

    return { valid: true, isValid: true };
}

/**
 * Validates a field with accessibility support
 */
export function validateField(
    field: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
    rules: ValidationRule[],
    options: FieldValidationOptions = {}
): ValidationResult {
    const {
        announceResult = true,
        announceOnlyErrors = true,
        focusOnError = false,
        scrollToError = false,
        displayErrorIcon = true
    } = options;

    // Get field value
    const value = field.value;

    // Apply validation
    const result = validate(value, rules);

    // Apply field state updates
    updateFieldValidation(field, result, displayErrorIcon);

    // Announce result for screen readers if needed
    if (announceResult && (!announceOnlyErrors || !result.valid)) {
        announce(result.valid
            ? `${field.name || 'Field'} is valid`
            : `${field.name || 'Field'} error: ${result.message}`,
            result.valid ? 'polite' : 'assertive');
    }

    // Handle focus management if needed
    if (!result.valid && focusOnError) {
        field.focus();

        if (scrollToError) {
            field.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    return result;
}

/**
 * Updates field validation state
 */
function updateFieldValidation(
    field: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
    result: ValidationResult,
    displayErrorIcon = true
): void {
    // Set aria attributes
    field.setAttribute('aria-invalid', result.valid ? 'false' : 'true');

    // Update error state
    if (result.valid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');

        // Remove error message if it exists
        const errorId = `${field.id}-error`;
        const errorElement = document.getElementById(errorId);
        if (errorElement) {
            errorElement.remove();
            field.removeAttribute('aria-describedby');
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');

        // Add/update error message
        if (result.message) {
            const errorId = `${field.id}-error`;
            let errorElement = document.getElementById(errorId);

            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.id = errorId;
                errorElement.className = 'invalid-feedback';
                errorElement.setAttribute('role', 'alert');
                errorElement.setAttribute('aria-live', 'assertive');

                if (field.parentNode) {
                    field.parentNode.insertBefore(errorElement, field.nextSibling);
                }

                field.setAttribute('aria-describedby', errorId);
            }

            errorElement.textContent = result.message;

            // Add error icon if needed
            if (displayErrorIcon && !errorElement.querySelector('.error-icon')) {
                const iconWrapper = document.createElement('span');
                iconWrapper.className = 'error-icon';
                iconWrapper.setAttribute('aria-hidden', 'true');
                iconWrapper.innerHTML = '⚠️';
                errorElement.prepend(iconWrapper);
            }
        }
    }
}

/**
 * Validates an entire form
 */
export function validateForm(
    form: HTMLFormElement,
    fieldRules: Record<string, ValidationRule[]>,
    options: FieldValidationOptions = {}
): { valid: boolean, errors: Record<string, string> } {
    const errors: Record<string, string> = {};
    let formValid = true;

    // Secure the form with accessibility enhancements
    secureAccessibility.form.enhanceForm(form, { enableSecurity: true });

    // Validate each field
    Object.entries(fieldRules).forEach(([fieldName, rules]) => {
        const field = form.elements.namedItem(fieldName) as HTMLInputElement;
        if (field) {
            const result = validateField(field, rules, options);
            if (!result.valid) {
                formValid = false;
                errors[fieldName] = result.message || 'Invalid field';
            }
        }
    });

    // Announce overall form validity status
    if (!formValid) {
        announce(`Form validation failed with ${Object.keys(errors).length} errors. Please correct the highlighted fields.`, 'assertive');

        // Focus first invalid field
        const firstInvalidField = form.querySelector('[aria-invalid="true"]') as HTMLElement;
        if (firstInvalidField && options.focusOnError) {
            firstInvalidField.focus();
        }
    }

    return { valid: formValid, errors };
}

/**
 * Sanitizes a string for safe display
 */
export function sanitizeInput(input: string): string {
    return input
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Formats a value based on a pattern
 * @example formatValue('1234567890', '(XXX) XXX-XXXX') => '(123) 456-7890'
 */
export function formatValue(value: string, pattern: string, placeholder = 'X'): string {
    const valueChars = value.split('');
    let result = pattern;

    valueChars.forEach(char => {
        result = result.replace(placeholder, char);
    });

    // Keep placeholders that weren't replaced
    return result;
}

// Export secure form validation
export const secureValidation = {
    /**
     * Validate with enhanced security measures
     */
    validateSecurely(
        value: string,
        rules: ValidationRule[],
        securityOptions: {
            sanitize?: boolean,
            maxLength?: number
        } = {}
    ): ValidationResult {
        const { sanitize = true, maxLength } = securityOptions;

        // Apply security measures
        let secureValue = value;

        if (sanitize) {
            secureValue = sanitizeInput(secureValue);
        }

        if (maxLength && secureValue.length > maxLength) {
            secureValue = secureValue.substring(0, maxLength);
        }

        // Validate the secured value
        return validate(secureValue, rules);
    }
};

// Export form validation with accessibility
export const accessibleValidation = {
    /**
     * Enhanced validation with accessibility features
     */
    validateWithA11y(
        field: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
        rules: ValidationRule[],
        a11yOptions: {
            announceErrors?: boolean,
            errorPriority?: 'polite' | 'assertive',
            addErrorIcon?: boolean
        } = {}
    ): ValidationResult {
        const {
            announceErrors = true,
            errorPriority = 'assertive',
            addErrorIcon = true
        } = a11yOptions;

        const result = validate(field.value, rules);

        // Update field state
        updateFieldValidation(field, result, addErrorIcon);

        // Announce for screen readers
        if (announceErrors && !result.valid && result.message) {
            announce(result.message, errorPriority);
        }

        return result;
    }
};

/**
 * CSRF Token Generation and Validation
 */
export function generateCSRFToken(): string {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 32; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

export function verifyCSRFToken(token: string): boolean {
    return typeof token === 'string' && token.length === 32;
}

/**
 * Rate Limiting
 */
const rateLimitStore = new Map<string, { count: number; timestamp: number }>();

export function checkRateLimit(
    keyOrAttempts: string | number,
    limitOrLastAttempt?: number,
    windowMsOrMaxAttempts?: number,
    rateLimitWindow?: number
): boolean | { allowed: boolean } {
    // Handle legacy 4-parameter call pattern
    if (typeof keyOrAttempts === 'number' && typeof limitOrLastAttempt === 'number' && typeof windowMsOrMaxAttempts === 'number' && typeof rateLimitWindow === 'number') {
        const attempts = keyOrAttempts;
        const lastAttemptTime = limitOrLastAttempt;
        const maxAttempts = windowMsOrMaxAttempts;
        const window = rateLimitWindow;

        const now = Date.now();
        const timeSinceLastAttempt = now - lastAttemptTime;

        // If enough time has passed, reset the counter
        if (timeSinceLastAttempt > window) {
            return { allowed: true };
        }

        // Check if we've exceeded the limit
        return { allowed: attempts < maxAttempts };
    }

    // Handle normal 3-parameter call pattern
    const key = keyOrAttempts as string;
    const limit = limitOrLastAttempt || 10;
    const windowMs = windowMsOrMaxAttempts || 60000;

    const now = Date.now();
    const entry = rateLimitStore.get(key);

    if (!entry || now - entry.timestamp > windowMs) {
        rateLimitStore.set(key, { count: 1, timestamp: now });
        return true;
    }

    if (entry.count >= limit) {
        return false;
    }

    entry.count++;
    return true;
}

export function resetRateLimit(key: string): void {
    rateLimitStore.delete(key);
}

/**
 * Security Validation
 */
export function securityValidate(data: Record<string, any>): boolean {
    // Basic security validation
    for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'string') {
            // Check for basic XSS patterns
            if (/<script|javascript:|on\w+=/i.test(value)) {
                return false;
            }
        }
    }
    return true;
}

/**
 * Service Configuration Validation
 */
export function validateServiceConfig(config: Record<string, any>): ValidationResult {
    const errors: string[] = [];

    if (!config.name || typeof config.name !== 'string' || config.name.trim().length === 0) {
        errors.push('Service name is required');
    }

    if (!config.image || typeof config.image !== 'string' || config.image.trim().length === 0) {
        errors.push('Docker image is required');
    }

    if (config.ports && Array.isArray(config.ports)) {
        for (const port of config.ports) {
            if (!port.host || !port.container) {
                errors.push('Port mappings must have both host and container ports');
            }
        }
    }

    return {
        valid: errors.length === 0,
        isValid: errors.length === 0,
        message: errors.join(', '),
        errors: errors.length > 0 ? { general: errors.join(', ') } : {}
    };
}

/**
 * CSRF Token Management
 */
export const csrf = {
    generate: generateCSRFToken,
    verify: verifyCSRFToken,
    getToken: () => {
        // Get token from meta tag or generate one
        const meta = typeof document !== 'undefined' ? document.querySelector('meta[name="csrf-token"]') : null;
        return meta?.getAttribute('content') || generateCSRFToken();
    }
};

/**
 * Rate Limit Management
 */
export const rateLimit = {
    check: checkRateLimit,
    reset: resetRateLimit,
    isLimited: (key: string, limit: number = 10, windowMs: number = 60000): boolean => {
        return !checkRateLimit(key, limit, windowMs);
    }
};
