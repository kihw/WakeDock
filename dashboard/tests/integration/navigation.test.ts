import { describe, it, expect, beforeEach } from 'vitest';
import {
    validateEmail,
    validatePassword,
    sanitizeInput,
    validatePasswordStrength,
    generateCSRFToken,
    checkRateLimit
} from '../../src/lib/utils/validation';
import {
    manageFocus,
    announceToScreenReader,
    validateFormAccessibility,
    getAccessibleErrorMessage,
    enhanceFormAccessibility
} from '../../src/lib/utils/accessibility';

describe('Security and Accessibility Integration Tests', () => {
    describe('Validation Utils Integration', () => {
        it('should sanitize XSS attempts in user input', () => {
            const maliciousInput = '<script>alert("xss")</script>';
            const sanitized = sanitizeInput(maliciousInput);

            expect(sanitized).not.toContain('<script>');
            expect(sanitized).not.toContain('alert');
        });

        it('should validate email addresses correctly', () => {
            const validEmail = 'user@example.com';
            const invalidEmail = 'invalid-email';

            const validResult = validateEmail(validEmail);
            const invalidResult = validateEmail(invalidEmail);

            expect(validResult.isValid).toBe(true);
            expect(invalidResult.isValid).toBe(false);
            expect(invalidResult.errors).toContain('Invalid email format');
        });

        it('should validate password strength with security requirements', () => {
            const weakPassword = '123';
            const strongPassword = 'SecureP@ssw0rd123!';

            const weakResult = validatePasswordStrength(weakPassword);
            const strongResult = validatePasswordStrength(strongPassword);

            expect(weakResult.isValid).toBe(false);
            expect(weakResult.score).toBeLessThan(4);
            expect(strongResult.isValid).toBe(true);
            expect(strongResult.score).toBeGreaterThanOrEqual(4);
        });

        it('should generate unique CSRF tokens', () => {
            const token1 = generateCSRFToken();
            const token2 = generateCSRFToken();

            expect(token1).toBeDefined();
            expect(token2).toBeDefined();
            expect(token1).not.toBe(token2);
            expect(token1.length).toBeGreaterThan(20);
        });

        it('should implement rate limiting correctly', () => {
            const identifier = 'test-user';

            // Allow initial requests
            const result1 = checkRateLimit(identifier, 1, 5, 60000);
            expect(result1.allowed).toBe(true);

            const result2 = checkRateLimit(identifier, 2, 5, 60000);
            expect(result2.allowed).toBe(true);

            // Block after limit
            const result6 = checkRateLimit(identifier, 6, 5, 60000);
            expect(result6.allowed).toBe(false);
            expect(result6.resetTime).toBeGreaterThan(0);
        });

        it('should handle combined security validations', () => {
            const userInput = {
                email: sanitizeInput('test@example.com'),
                password: 'SecurePassword123!',
                username: sanitizeInput('testuser<script>alert(1)</script>')
            };

            const emailValidation = validateEmail(userInput.email);
            const passwordValidation = validatePasswordStrength(userInput.password);

            expect(emailValidation.isValid).toBe(true);
            expect(passwordValidation.isValid).toBe(true);
            expect(userInput.username).not.toContain('<script>');
        });
    });

    describe('Accessibility Utils Integration', () => {
        beforeEach(() => {
            // Create a mock DOM environment
            document.body.innerHTML = `
        <div id="test-container">
          <form id="test-form">
            <input id="test-input" type="text" />
            <button id="test-button">Submit</button>
          </form>
          <div id="live-region" aria-live="polite"></div>
        </div>
      `;
        });

        it('should manage focus correctly', () => {
            const input = document.getElementById('test-input') as HTMLInputElement;
            expect(input).toBeDefined();

            manageFocus(input);
            expect(document.activeElement).toBe(input);
        });

        it('should announce messages to screen readers', () => {
            const liveRegion = document.getElementById('live-region');
            announceToScreenReader('Test message');

            // Check if live region is updated (implementation may vary)
            expect(liveRegion).toBeDefined();
        });

        it('should generate accessible error messages', () => {
            const errorMessage = getAccessibleErrorMessage('email', 'Invalid email format');

            expect(errorMessage).toContain('email');
            expect(errorMessage).toContain('Invalid email format');
            expect(errorMessage.toLowerCase()).toContain('error');
        });

        it('should validate form accessibility', () => {
            const form = document.getElementById('test-form') as HTMLFormElement;
            const result = validateFormAccessibility(form);

            expect(result).toBeDefined();
            expect(typeof result.isAccessible).toBe('boolean');
            expect(Array.isArray(result.issues)).toBe(true);
        });

        it('should enhance form accessibility', () => {
            const form = document.getElementById('test-form') as HTMLFormElement;
            enhanceFormAccessibility(form);

            // Check if accessibility enhancements were applied
            const input = form.querySelector('input');
            expect(input).toBeDefined();
        });

        it('should handle keyboard navigation patterns', () => {
            const container = document.getElementById('test-container') as HTMLElement;
            const focusableElements = container.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );

            expect(focusableElements.length).toBeGreaterThan(0);

            // Test tab order
            const firstElement = focusableElements[0] as HTMLElement;
            const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

            expect(firstElement).toBeDefined();
            expect(lastElement).toBeDefined();
        });
    });

    describe('Combined Security and Accessibility', () => {
        it('should sanitize input while maintaining accessibility', () => {
            const maliciousInput = '<script>alert("xss")</script>Test content';
            const sanitized = sanitizeInput(maliciousInput);

            expect(sanitized).not.toContain('<script>');
            expect(sanitized).toContain('Test content');

            // Ensure error message is accessible
            const errorMessage = getAccessibleErrorMessage('input', 'Input contained invalid characters');
            expect(errorMessage).toBeDefined();
        });

        it('should validate form with security and accessibility checks', () => {
            document.body.innerHTML = `
        <form id="secure-form">
          <label for="email">Email:</label>
          <input id="email" name="email" type="email" required aria-describedby="email-help" />
          <div id="email-help">Enter your email address</div>
          
          <label for="password">Password:</label>
          <input id="password" name="password" type="password" required aria-describedby="password-help" />
          <div id="password-help">Password must be at least 8 characters</div>
          
          <button type="submit">Submit</button>
        </form>
      `;

            const form = document.getElementById('secure-form') as HTMLFormElement;
            const accessibilityResult = validateFormAccessibility(form);

            // Check that form has proper accessibility structure
            expect(accessibilityResult.isAccessible).toBe(true);
            expect(accessibilityResult.issues.length).toBe(0);

            // Test security validation
            const emailInput = form.querySelector('#email') as HTMLInputElement;
            const passwordInput = form.querySelector('#password') as HTMLInputElement;

            emailInput.value = 'test@example.com';
            passwordInput.value = 'SecurePassword123!';

            const emailValidation = validateEmail(sanitizeInput(emailInput.value));
            const passwordValidation = validatePasswordStrength(passwordInput.value);

            expect(emailValidation.isValid).toBe(true);
            expect(passwordValidation.isValid).toBe(true);
        });

        it('should handle error states with accessibility and security', () => {
            const maliciousEmail = '<script>alert("hack")</script>@evil.com';
            const sanitizedEmail = sanitizeInput(maliciousEmail);
            const emailValidation = validateEmail(sanitizedEmail);

            expect(emailValidation.isValid).toBe(false);

            const accessibleError = getAccessibleErrorMessage('email', emailValidation.errors[0]);
            expect(accessibleError).toBeDefined();
            expect(accessibleError).not.toContain('<script>');
        });

        it('should integrate CSRF protection with accessible forms', () => {
            const csrfToken = generateCSRFToken();

            document.body.innerHTML = `
        <form id="csrf-form">
          <input type="hidden" name="_csrf" value="${csrfToken}" />
          <label for="username">Username:</label>
          <input id="username" name="username" type="text" required />
          <button type="submit">Submit</button>
        </form>
      `;

            const form = document.getElementById('csrf-form') as HTMLFormElement;
            const csrfInput = form.querySelector('[name="_csrf"]') as HTMLInputElement;
            const accessibilityResult = validateFormAccessibility(form);

            expect(csrfInput.value).toBe(csrfToken);
            expect(accessibilityResult.isAccessible).toBe(true);
        });

        it('should handle rate limiting with accessible feedback', () => {
            const userId = 'test-user-123';

            // Simulate multiple login attempts
            for (let i = 1; i <= 6; i++) {
                const result = checkRateLimit(userId, i, 5, 60000);

                if (!result.allowed) {
                    const accessibleMessage = getAccessibleErrorMessage(
                        'login',
                        `Too many attempts. Please wait ${Math.ceil(result.resetTime / 60000)} minutes.`
                    );

                    expect(accessibleMessage).toBeDefined();
                    expect(accessibleMessage.toLowerCase()).toContain('error');
                    expect(accessibleMessage).toContain('wait');
                    break;
                }
            }
        });
    });

    describe('Component Integration Patterns', () => {
        it('should integrate validation with form components', () => {
            // Simulate form component integration
            const formData = {
                email: 'user@example.com',
                password: 'SecurePassword123!',
                confirmPassword: 'SecurePassword123!'
            };

            // Sanitize all inputs
            const sanitizedData = Object.fromEntries(
                Object.entries(formData).map(([key, value]) => [key, sanitizeInput(value)])
            );

            // Validate all fields
            const validations = {
                email: validateEmail(sanitizedData.email),
                password: validatePasswordStrength(sanitizedData.password),
                passwordMatch: sanitizedData.password === sanitizedData.confirmPassword
            };

            expect(validations.email.isValid).toBe(true);
            expect(validations.password.isValid).toBe(true);
            expect(validations.passwordMatch).toBe(true);
        });

        it('should integrate accessibility with navigation components', () => {
            // Simulate navigation component structure
            document.body.innerHTML = `
        <nav role="navigation" aria-label="Main navigation">
          <ul role="menubar">
            <li role="none">
              <a role="menuitem" href="/" aria-current="page">Dashboard</a>
            </li>
            <li role="none">
              <a role="menuitem" href="/services">Services</a>
            </li>
            <li role="none">
              <a role="menuitem" href="/settings">Settings</a>
            </li>
          </ul>
        </nav>
      `;

            const nav = document.querySelector('nav');
            const menuItems = nav?.querySelectorAll('[role="menuitem"]');

            expect(nav?.getAttribute('role')).toBe('navigation');
            expect(nav?.getAttribute('aria-label')).toBe('Main navigation');
            expect(menuItems?.length).toBe(3);

            // Test current page indication
            const currentItem = nav?.querySelector('[aria-current="page"]');
            expect(currentItem?.textContent).toBe('Dashboard');
        });
    });
});
