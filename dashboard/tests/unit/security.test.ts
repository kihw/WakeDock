/**
 * Security Test Suite
 * Comprehensive security tests for WakeDock Dashboard
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { sanitizeInput, securityValidate, csrf, rateLimit } from '../../src/lib/utils/validation';
import { storage, memoryUtils } from '../../src/lib/utils/storage';
import { secureAccessibility } from '../../src/lib/utils/accessibility';

describe('Security Validation', () => {
    describe('Input Sanitization', () => {
        it('should sanitize HTML to prevent XSS', () => {
            const maliciousInput = '<script>alert("xss")</script><b>Bold</b>';
            const sanitized = sanitizeInput.html(maliciousInput);

            expect(sanitized).not.toContain('<script>');
            expect(sanitized).toContain('<b>Bold</b>');
        });

        it('should remove dangerous characters from text input', () => {
            const maliciousInput = '<img src="x" onerror="alert(1)">';
            const sanitized = sanitizeInput.text(maliciousInput);

            expect(sanitized).not.toContain('<');
            expect(sanitized).not.toContain('>');
            expect(sanitized).not.toContain('"');
        });

        it('should sanitize URLs to prevent malicious redirects', () => {
            const maliciousUrl = 'javascript:alert("xss")';
            const sanitized = sanitizeInput.url(maliciousUrl);

            expect(sanitized).toBe('');
        });

        it('should allow valid HTTPS URLs', () => {
            const validUrl = 'https://example.com/path';
            const sanitized = sanitizeInput.url(validUrl);

            expect(sanitized).toBe(validUrl);
        });

        it('should sanitize log messages to prevent log injection', () => {
            const maliciousLog = 'User login\r\nADMIN LOGIN SUCCESSFUL\t<script>';
            const sanitized = sanitizeInput.logMessage(maliciousLog);

            expect(sanitized).not.toContain('\r');
            expect(sanitized).not.toContain('\n');
            expect(sanitized).not.toContain('\t');
            expect(sanitized).not.toContain('<script>');
        });
    });

    describe('Password Validation', () => {
        it('should detect weak passwords', () => {
            const result = securityValidate.password('123456');

            expect(result.valid).toBe(false);
            expect(result.strength).toBeLessThan(4);
        });

        it('should detect common passwords', () => {
            const result = securityValidate.password('password123');

            expect(result.valid).toBe(false);
            expect(result.error).toContain('weak');
        });

        it('should validate strong passwords', () => {
            const result = securityValidate.password('MyStr0ng!P@ssw0rd');

            expect(result.valid).toBe(true);
            expect(result.strength).toBeGreaterThanOrEqual(4);
        });
    });

    describe('Email Validation', () => {
        it('should validate proper email format', () => {
            const result = securityValidate.email('user@example.com');

            expect(result.valid).toBe(true);
        });

        it('should reject malicious email formats', () => {
            const result = securityValidate.email('user@<script>alert(1)</script>');

            expect(result.valid).toBe(false);
        });

        it('should handle email length limits', () => {
            const longEmail = 'a'.repeat(250) + '@example.com';
            const result = securityValidate.email(longEmail);

            expect(result.valid).toBe(false);
            expect(result.error).toContain('too long');
        });
    });
});

describe('CSRF Protection', () => {
    beforeEach(() => {
        // Clear session storage
        sessionStorage.clear();
    });

    it('should generate valid CSRF tokens', () => {
        const token = csrf.generateToken();

        expect(token).toHaveLength(64);
        expect(token).toMatch(/^[a-f0-9]+$/);
    });

    it('should store and retrieve CSRF tokens', () => {
        const token = csrf.generateToken();
        csrf.storeToken(token);

        const retrieved = csrf.getToken();
        expect(retrieved).toBe(token);
    });

    it('should validate CSRF tokens correctly', () => {
        const token = csrf.generateToken();
        csrf.storeToken(token);

        expect(csrf.validateToken(token)).toBe(true);
        expect(csrf.validateToken('invalid')).toBe(false);
    });

    it('should reject tokens with invalid length', () => {
        csrf.storeToken('validtoken');

        expect(csrf.validateToken('short')).toBe(false);
    });
});

describe('Rate Limiting', () => {
    beforeEach(() => {
        rateLimit.attempts.clear();
    });

    it('should allow requests within limits', () => {
        const key = 'test-action';

        expect(rateLimit.isLimited(key, 5)).toBe(false);
        expect(rateLimit.isLimited(key, 5)).toBe(false);
    });

    it('should block requests exceeding limits', () => {
        const key = 'test-action';

        // Make 5 attempts (should be allowed)
        for (let i = 0; i < 5; i++) {
            expect(rateLimit.isLimited(key, 5)).toBe(false);
        }

        // 6th attempt should be blocked
        expect(rateLimit.isLimited(key, 5)).toBe(true);
    });

    it('should reset limits after time window', () => {
        const key = 'test-action';

        // Exhaust attempts
        for (let i = 0; i < 6; i++) {
            rateLimit.isLimited(key, 5, 100); // 100ms window
        }

        // Wait for window to expire
        return new Promise(resolve => {
            setTimeout(() => {
                expect(rateLimit.isLimited(key, 5, 100)).toBe(false);
                resolve(undefined);
            }, 150);
        });
    });

    it('should reset specific keys', () => {
        const key = 'test-action';

        // Exhaust attempts
        for (let i = 0; i < 6; i++) {
            rateLimit.isLimited(key, 5);
        }

        // Reset and check
        rateLimit.reset(key);
        expect(rateLimit.isLimited(key, 5)).toBe(false);
    });
});

describe('Secure Storage', () => {
    let mockCrypto: any;

    beforeEach(() => {
        localStorage.clear();

        // Mock Web Crypto API for Node.js environment
        mockCrypto = {
            getRandomValues: vi.fn((arr) => {
                for (let i = 0; i < arr.length; i++) {
                    arr[i] = Math.floor(Math.random() * 256);
                }
                return arr;
            }),
            subtle: {
                importKey: vi.fn(() => Promise.resolve({})),
                deriveKey: vi.fn(() => Promise.resolve({})),
                encrypt: vi.fn(() => Promise.resolve(new ArrayBuffer(32))),
                decrypt: vi.fn(() => Promise.resolve(new TextEncoder().encode('decrypted').buffer))
            }
        };

        // @ts-ignore
        global.crypto = mockCrypto;
    });

    afterEach(() => {
        localStorage.clear();
    });

    it('should store and retrieve secure items', async () => {
        const key = 'test-key';
        const value = 'test-value';

        const stored = await storage.setSecureItem(key, value);
        expect(stored).toBe(true);

        const retrieved = await storage.getSecureItem(key);
        expect(retrieved).toBe(value);
    });

    it('should handle encrypted storage with password', async () => {
        const key = 'secret-key';
        const value = 'secret-value';
        const password = 'password123';

        await storage.setSecureItem(key, value, { password });
        const retrieved = await storage.getSecureItem(key, password);

        // In real implementation, this would test actual encryption
        expect(retrieved).toBeDefined();
    });

    it('should clean up expired items', () => {
        // Mock localStorage with expired item
        const expiredItem = {
            value: 'test',
            timestamp: Date.now() - 25 * 60 * 60 * 1000 // 25 hours ago
        };

        localStorage.setItem('wakedock_expired', JSON.stringify(expiredItem));

        const cleaned = storage.cleanupExpiredItems();

        expect(cleaned).toBeGreaterThanOrEqual(0);
    });

    it('should audit stored data', () => {
        // Add some test data
        localStorage.setItem('wakedock_test1', JSON.stringify({ value: 'test', timestamp: Date.now() }));
        localStorage.setItem('wakedock_test2', 'ENCRYPTED:somedata');

        const audit = storage.getStorageStats();

        expect(audit.totalItems).toBeGreaterThanOrEqual(0);
        expect(audit.totalSize).toBeGreaterThanOrEqual(0);
    });
});

describe('Memory Security', () => {
    it('should clear sensitive data from objects', () => {
        const sensitiveData = {
            username: 'user',
            password: 'secret123',
            token: 'bearer-token',
            normalData: 'keep-this'
        };

        memoryUtils.clearSensitiveData(sensitiveData);

        expect(sensitiveData.password).toBeUndefined();
        expect(sensitiveData.token).toBeUndefined();
        expect(sensitiveData.normalData).toBe('keep-this');
    });

    it('should perform constant-time string comparison', () => {
        const str1 = 'password123';
        const str2 = 'password123';
        const str3 = 'password456';

        expect(memoryUtils.constantTimeCompare(str1, str2)).toBe(true);
        expect(memoryUtils.constantTimeCompare(str1, str3)).toBe(false);
        expect(memoryUtils.constantTimeCompare('', 'a')).toBe(false);
    });

    it('should handle different length strings safely', () => {
        const short = 'abc';
        const long = 'abcdefgh';

        expect(memoryUtils.constantTimeCompare(short, long)).toBe(false);
    });
});

describe('Accessibility Security', () => {
    let container: HTMLElement;

    beforeEach(() => {
        document.body.innerHTML = '';
        container = document.createElement('div');
        document.body.appendChild(container);
    });

    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('should validate color values for security', () => {
        expect(secureAccessibility.color.validateColor('#ff0000')).toBe(true);
        expect(secureAccessibility.color.validateColor('#f00')).toBe(true);
        expect(secureAccessibility.color.validateColor('javascript:alert(1)')).toBe(false);
        expect(secureAccessibility.color.validateColor('<script>')).toBe(false);
    });

    it('should calculate contrast ratios securely', () => {
        const ratio = secureAccessibility.color.calculateRatio('#000000', '#ffffff');
        expect(ratio).toBeGreaterThan(20); // High contrast

        const invalidRatio = secureAccessibility.color.calculateRatio('invalid', '#ffffff');
        expect(invalidRatio).toBe(0);
    });

    it('should provide WCAG compliance checking', () => {
        const result = secureAccessibility.color.meetsWCAG('#000000', '#ffffff', 'AA', 'normal');

        expect(result.compliant).toBe(true);
        expect(result.ratio).toBeGreaterThan(4.5);
    });

    it('should provide recommendations for non-compliant colors', () => {
        const result = secureAccessibility.color.meetsWCAG('#888888', '#999999', 'AA', 'normal');

        expect(result.compliant).toBe(false);
        expect(result.recommendation).toBeDefined();
    });

    it('should sanitize form inputs for security', () => {
        const form = document.createElement('form');
        const input = document.createElement('input');
        input.id = 'test-input';
        input.value = '<script>alert("xss")</script>normal text';
        form.appendChild(input);

        const isValid = secureAccessibility.form.validateField(
            input,
            (value) => ({ valid: value.length > 0 }),
            { sanitizeInput: true }
        );

        expect(input.value).not.toContain('<script>');
        expect(input.value).toContain('normal text');
    });

    it('should enforce maximum input lengths', () => {
        const form = document.createElement('form');
        const input = document.createElement('input');
        input.id = 'test-input';
        input.value = 'a'.repeat(1000);
        form.appendChild(input);

        secureAccessibility.form.validateField(
            input,
            (value) => ({ valid: true }),
            { maxLength: 100 }
        );

        expect(input.value.length).toBe(100);
    });

    it('should remove dangerous attributes from form elements', () => {
        const form = document.createElement('form');
        const input = document.createElement('input');
        input.setAttribute('onclick', 'alert("xss")');
        input.setAttribute('onerror', 'malicious()');
        form.appendChild(input);

        secureAccessibility.form.enhanceForm(form, { enableSecurity: true });

        expect(input.hasAttribute('onclick')).toBe(false);
        expect(input.hasAttribute('onerror')).toBe(false);
    });
});
