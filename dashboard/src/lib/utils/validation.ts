/**
 * Validation Utilities
 * Input validation functions for forms and data
 */

import DOMPurify from 'dompurify';

export interface ValidationResult {
    isValid: boolean;
    errors: string[];
}

export interface ValidationRule<T = any> {
    name: string;
    validator: (value: T) => boolean;
    message: string;
}

/**
 * Base validation class
 */
export class Validator<T = any> {
    private rules: ValidationRule<T>[] = [];

    /**
     * Add a validation rule
     */
    addRule(rule: ValidationRule<T>): Validator<T> {
        this.rules.push(rule);
        return this;
    }

    /**
     * Validate a value against all rules
     */
    validate(value: T): ValidationResult {
        const errors: string[] = [];

        for (const rule of this.rules) {
            if (!rule.validator(value)) {
                errors.push(rule.message);
            }
        }

        return {
            isValid: errors.length === 0,
            errors,
        };
    }

    /**
     * Validate and throw on first error
     */
    validateStrict(value: T): void {
        const result = this.validate(value);
        if (!result.isValid) {
            throw new Error(result.errors[0]);
        }
    }
}

/**
 * Email validation
 */
export function isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Password validation
 */
export function isValidPassword(password: string): boolean {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
}

/**
 * Username validation
 */
export function isValidUsername(username: string): boolean {
    // 3-30 characters, letters, numbers, underscores, hyphens
    const usernameRegex = /^[a-zA-Z0-9_-]{3,30}$/;
    return usernameRegex.test(username);
}

/**
 * Service name validation
 */
export function isValidServiceName(name: string): boolean {
    // Docker container name rules: [a-zA-Z0-9][a-zA-Z0-9_.-]*
    const serviceNameRegex = /^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/;
    return serviceNameRegex.test(name) && name.length >= 1 && name.length <= 253;
}

/**
 * Port validation
 */
export function isValidPort(port: number): boolean {
    return Number.isInteger(port) && port >= 1 && port <= 65535;
}

/**
 * URL validation
 */
export function isValidUrl(url: string): boolean {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

/**
 * Docker image name validation
 */
export function isValidDockerImage(image: string): boolean {
    // Simplified Docker image name validation
    const imageRegex = /^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:\/[a-z0-9]+(?:[._-][a-z0-9]+)*)*(?::[a-zA-Z0-9._-]+)?$/;
    return imageRegex.test(image);
}

/**
 * Environment variable name validation
 */
export function isValidEnvVarName(name: string): boolean {
    const envVarRegex = /^[A-Z_][A-Z0-9_]*$/;
    return envVarRegex.test(name);
}

/**
 * File path validation (Unix-style)
 */
export function isValidFilePath(path: string): boolean {
    // Basic Unix path validation
    return path.startsWith('/') && !path.includes('..') && path.length > 0;
}

/**
 * Required field validation
 */
export function required<T>(value: T): boolean {
    if (typeof value === 'string') {
        return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
}

/**
 * Minimum length validation
 */
export function minLength(min: number) {
    return (value: string): boolean => {
        return value.length >= min;
    };
}

/**
 * Maximum length validation
 */
export function maxLength(max: number) {
    return (value: string): boolean => {
        return value.length <= max;
    };
}

/**
 * Numeric range validation
 */
export function inRange(min: number, max: number) {
    return (value: number): boolean => {
        return value >= min && value <= max;
    };
}

/**
 * Pattern validation
 */
export function matchesPattern(pattern: RegExp) {
    return (value: string): boolean => {
        return pattern.test(value);
    };
}

/**
 * Custom validation function
 */
export function custom<T>(validator: (value: T) => boolean) {
    return validator;
}

/**
 * Pre-configured validators
 */
export const validators = {
    email: new Validator<string>()
        .addRule({
            name: 'required',
            validator: required,
            message: 'Email is required',
        })
        .addRule({
            name: 'email',
            validator: isValidEmail,
            message: 'Please enter a valid email address',
        }),

    password: new Validator<string>()
        .addRule({
            name: 'required',
            validator: required,
            message: 'Password is required',
        })
        .addRule({
            name: 'password',
            validator: isValidPassword,
            message: 'Password must be at least 8 characters with uppercase, lowercase, and number',
        }),

    username: new Validator<string>()
        .addRule({
            name: 'required',
            validator: required,
            message: 'Username is required',
        })
        .addRule({
            name: 'username',
            validator: isValidUsername,
            message: 'Username must be 3-30 characters (letters, numbers, _, -)',
        }),

    serviceName: new Validator<string>()
        .addRule({
            name: 'required',
            validator: required,
            message: 'Service name is required',
        })
        .addRule({
            name: 'serviceName',
            validator: isValidServiceName,
            message: 'Invalid service name format',
        }),

    dockerImage: new Validator<string>()
        .addRule({
            name: 'required',
            validator: required,
            message: 'Docker image is required',
        })
        .addRule({
            name: 'dockerImage',
            validator: isValidDockerImage,
            message: 'Invalid Docker image format',
        }),

    port: new Validator<number>()
        .addRule({
            name: 'port',
            validator: isValidPort,
            message: 'Port must be between 1 and 65535',
        }),
};

/**
 * Validate an object against a schema
 */
export function validateObject<T extends Record<string, any>>(
    obj: T,
    schema: Record<keyof T, Validator>
): { isValid: boolean; errors: Record<keyof T, string[]> } {
    const errors: Record<keyof T, string[]> = {} as any;
    let isValid = true;

    for (const [key, validator] of Object.entries(schema)) {
        const result = validator.validate(obj[key]);
        if (!result.isValid) {
            errors[key as keyof T] = result.errors;
            isValid = false;
        }
    }

    return { isValid, errors };
}

/**
 * Service Configuration Validation
 */
export function validateServiceConfig(config: any): ValidationResult {
    const errors: string[] = [];

    // Validate required fields
    if (!config.name || typeof config.name !== 'string' || config.name.trim().length === 0) {
        errors.push('Service name is required');
    }

    if (!config.image || typeof config.image !== 'string' || config.image.trim().length === 0) {
        errors.push('Docker image is required');
    }

    // Validate name format (Docker service name rules)
    if (config.name && !/^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/.test(config.name)) {
        errors.push('Service name must contain only letters, numbers, hyphens, underscores, and periods');
    }

    // Validate ports
    if (config.ports && Array.isArray(config.ports)) {
        config.ports.forEach((port: any, index: number) => {
            if (typeof port !== 'object' || port === null) {
                errors.push(`Port ${index + 1} must be an object`);
                return;
            }

            if (!port.containerPort || !Number.isInteger(Number(port.containerPort))) {
                errors.push(`Port ${index + 1} container port must be a valid number`);
            }

            if (port.hostPort && !Number.isInteger(Number(port.hostPort))) {
                errors.push(`Port ${index + 1} host port must be a valid number`);
            }

            const containerPort = Number(port.containerPort);
            const hostPort = port.hostPort ? Number(port.hostPort) : null;

            if (containerPort < 1 || containerPort > 65535) {
                errors.push(`Port ${index + 1} container port must be between 1 and 65535`);
            }

            if (hostPort && (hostPort < 1 || hostPort > 65535)) {
                errors.push(`Port ${index + 1} host port must be between 1 and 65535`);
            }
        });
    }

    // Validate environment variables
    if (config.environment && Array.isArray(config.environment)) {
        config.environment.forEach((env: any, index: number) => {
            if (typeof env !== 'object' || env === null) {
                errors.push(`Environment variable ${index + 1} must be an object`);
                return;
            }

            if (!env.name || typeof env.name !== 'string' || env.name.trim().length === 0) {
                errors.push(`Environment variable ${index + 1} name is required`);
            }

            if (env.name && !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(env.name)) {
                errors.push(`Environment variable ${index + 1} name must contain only letters, numbers, and underscores`);
            }
        });
    }

    // Validate volumes
    if (config.volumes && Array.isArray(config.volumes)) {
        config.volumes.forEach((volume: any, index: number) => {
            if (typeof volume !== 'object' || volume === null) {
                errors.push(`Volume ${index + 1} must be an object`);
                return;
            }

            if (!volume.containerPath || typeof volume.containerPath !== 'string' || volume.containerPath.trim().length === 0) {
                errors.push(`Volume ${index + 1} container path is required`);
            }

            if (volume.hostPath && typeof volume.hostPath !== 'string') {
                errors.push(`Volume ${index + 1} host path must be a string`);
            }

            // Validate container path format (Unix-style paths)
            if (volume.containerPath && !/^\//.test(volume.containerPath)) {
                errors.push(`Volume ${index + 1} container path must be an absolute path starting with /`);
            }
        });
    }

    // Validate restart policy
    if (config.restartPolicy && !['no', 'always', 'unless-stopped', 'on-failure'].includes(config.restartPolicy)) {
        errors.push('Restart policy must be one of: no, always, unless-stopped, on-failure');
    }

    // Validate networks
    if (config.networks && Array.isArray(config.networks)) {
        config.networks.forEach((network: any, index: number) => {
            if (typeof network !== 'string' || network.trim().length === 0) {
                errors.push(`Network ${index + 1} must be a non-empty string`);
            }
        });
    }

    // Validate labels
    if (config.labels && typeof config.labels === 'object') {
        Object.entries(config.labels).forEach(([key, value], index) => {
            if (typeof key !== 'string' || key.trim().length === 0) {
                errors.push(`Label ${index + 1} key must be a non-empty string`);
            }

            if (typeof value !== 'string') {
                errors.push(`Label ${index + 1} value must be a string`);
            }
        });
    }

    return {
        isValid: errors.length === 0,
        errors,
    };
}

// Input sanitization utilities for security
export const sanitizeInput = {
    /**
     * Sanitize HTML content to prevent XSS
     */
    html(input: string): string {
        return DOMPurify.sanitize(input, {
            ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br'],
            ALLOWED_ATTR: []
        });
    },

    /**
     * Sanitize text input (remove HTML, special chars)
     */
    text(input: string): string {
        return input
            .replace(/<[^>]*>/g, '') // Remove HTML tags
            .replace(/[<>'"&]/g, '') // Remove dangerous characters
            .trim();
    },

    /**
     * Sanitize email format
     */
    email(input: string): string {
        return input
            .toLowerCase()
            .replace(/[^\w@.-]/g, '')
            .trim();
    },

    /**
     * Sanitize URL to prevent malicious redirects
     */
    url(input: string): string {
        try {
            const url = new URL(input);
            // Only allow http/https protocols
            if (!['http:', 'https:'].includes(url.protocol)) {
                throw new Error('Invalid protocol');
            }
            return url.toString();
        } catch {
            return '';
        }
    },

    /**
     * Sanitize log messages to prevent log injection
     */
    logMessage(input: string): string {
        return input
            .replace(/[\r\n\t]/g, ' ') // Remove newlines/tabs
            .replace(/[^\x20-\x7E]/g, '') // Remove non-printable chars
            .substring(0, 1000); // Limit length
    }
};

// Enhanced validation patterns for security
export const securityValidators = {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    strongPassword: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
    username: /^[a-zA-Z0-9_-]{3,20}$/,
    url: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
    ipAddress: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
    port: /^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/
};

// Common password list (subset for security)
const commonPasswords = new Set([
    'password', '123456', 'password123', 'admin', 'qwerty', 'letmein',
    'welcome', 'monkey', '1234567890', 'abc123', 'password1', 'login'
]);

function isCommonPassword(password: string): boolean {
    return commonPasswords.has(password.toLowerCase());
}

// Enhanced security validation functions
export const securityValidate = {
    /**
     * Validate email with enhanced security checks
     */
    email(email: string): { valid: boolean; error?: string } {
        const sanitized = sanitizeInput.email(email);

        if (!sanitized) {
            return { valid: false, error: 'Email is required' };
        }

        if (!securityValidators.email.test(sanitized)) {
            return { valid: false, error: 'Invalid email format' };
        }

        if (sanitized.length > 254) {
            return { valid: false, error: 'Email too long' };
        }

        return { valid: true };
    },

    /**
     * Validate password with comprehensive strength checking
     */
    password(password: string): { valid: boolean; error?: string; strength: number } {
        if (!password) {
            return { valid: false, error: 'Password is required', strength: 0 };
        }

        let strength = 0;
        const checks = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            numbers: /\d/.test(password),
            special: /[@$!%*?&]/.test(password),
            noCommon: !isCommonPassword(password)
        };

        strength = Object.values(checks).filter(Boolean).length;

        if (!checks.length) {
            return { valid: false, error: 'Password must be at least 8 characters', strength };
        }

        if (strength < 4) {
            return { valid: false, error: 'Password too weak', strength };
        }

        return { valid: true, strength };
    },

    /**
     * Validate service configuration with security checks
     */
    serviceConfig(config: any): { valid: boolean; errors: string[] } {
        const errors: string[] = [];

        if (!config.name || typeof config.name !== 'string') {
            errors.push('Service name is required');
        } else if (config.name.length > 50) {
            errors.push('Service name too long');
        }

        if (config.port && !securityValidators.port.test(config.port.toString())) {
            errors.push('Invalid port number');
        }

        if (config.domain && !securityValidators.url.test(`https://${config.domain}`)) {
            errors.push('Invalid domain format');
        }

        return { valid: errors.length === 0, errors };
    }
};

// CSRF token utilities
export const csrf = {
    /**
     * Generate CSRF token
     */
    generateToken(): string {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    },

    /**
     * Store CSRF token
     */
    storeToken(token: string): void {
        sessionStorage.setItem('csrf_token', token);
    },

    /**
     * Get stored CSRF token
     */
    getToken(): string | null {
        return sessionStorage.getItem('csrf_token');
    },

    /**
     * Validate CSRF token
     */
    validateToken(token: string): boolean {
        const storedToken = this.getToken();
        return storedToken === token && token.length === 64;
    }
};

// Rate limiting utilities
export const rateLimit = {
    attempts: new Map<string, { count: number; lastAttempt: number }>(),

    /**
     * Check if action is rate limited
     */
    isLimited(key: string, maxAttempts = 5, windowMs = 15 * 60 * 1000): boolean {
        const now = Date.now();
        const attempt = this.attempts.get(key);

        if (!attempt) {
            this.attempts.set(key, { count: 1, lastAttempt: now });
            return false;
        }

        // Reset if window expired
        if (now - attempt.lastAttempt > windowMs) {
            this.attempts.set(key, { count: 1, lastAttempt: now });
            return false;
        }

        // Increment attempt count
        attempt.count++;
        attempt.lastAttempt = now;

        return attempt.count > maxAttempts;
    },

    /**
     * Reset rate limit for key
     */
    reset(key: string): void {
        this.attempts.delete(key);
    }
};
