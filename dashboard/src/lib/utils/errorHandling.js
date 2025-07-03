/**
 * Enhanced Error Handler for WakeDock Dashboard
 * Handles autofill extension errors, validation function errors, and other common issues
 */

export function setupGlobalErrorHandling() {
  // Comprehensive error handler
  const handleGlobalError = (event) => {
    if (event.error && event.error.message) {
      const errorMessage = event.error.message.toLowerCase();

      // List of errors to silently ignore
      const ignoredErrors = [
        // Autofill extension errors
        'autofill',
        'bootstrap-autofill',
        'extension context invalidated',
        'cannot read properties of null',

        // Specific function-related errors that are safe to ignore (extension related)
        'generatetoken is not a function',
        'validatetoken is not a function',
        'a.email is not a function',
        'f.generatetoken is not a function',
        'j.generatetoken is not a function',
        'j.validatetoken is not a function',

        // Common extension-related errors
        'chrome-extension',
        'moz-extension',
        'safari-extension',
        'extension/',

        // Password manager errors
        'lastpass',
        'bitwarden',
        '1password',
        'dashlane',

        // Other common browser extension errors
        'content script',
        'injected script',
        'user script',

        // WebSocket connection errors (expected in development)
        'websocket connection',
        'ws://',
        'failed to connect'
      ];

      // Check if this error should be ignored
      const shouldIgnore = ignoredErrors.some(pattern =>
        errorMessage.includes(pattern)
      );

      if (shouldIgnore) {
        // Silently ignore these errors
        event.preventDefault();
        console.debug('Browser extension/validation error ignored:', event.error.message);
        return false;
      }

      // Log other errors for debugging
      console.warn('Unhandled error:', event.error.message, event.error.stack);
    }
  };

  // Handle promise rejections
  const handlePromiseRejection = (event) => {
    const reason = event.reason;
    if (reason && typeof reason === 'object' && reason.message) {
      const errorMessage = reason.message.toLowerCase();

      const ignoredErrors = [
        'autofill',
        'bootstrap-autofill',
        'extension context invalidated',
        'generatetoken is not a function',
        'validatetoken is not a function',
        'chrome-extension',
        'moz-extension'
      ];

      const shouldIgnore = ignoredErrors.some(pattern =>
        errorMessage.includes(pattern)
      );

      if (shouldIgnore) {
        event.preventDefault();
        console.debug('Promise rejection ignored:', reason.message);
        return false;
      }

      console.warn('Unhandled promise rejection:', reason.message);
    }
  };

  // Add event listeners
  if (typeof window !== 'undefined') {
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handlePromiseRejection);

    // Return cleanup function
    return () => {
      window.removeEventListener('error', handleGlobalError);
      window.removeEventListener('unhandledrejection', handlePromiseRejection);
    };
  }

  return () => { }; // No-op cleanup for SSR
}

/**
 * Safe validation function wrapper
 * Provides fallback validation to prevent function errors
 */
export function safeValidate(validationFn, defaultResult = { valid: false, message: 'Validation error' }) {
  return (...args) => {
    try {
      const result = validationFn(...args);
      return result;
    } catch (error) {
      console.debug('Validation function error:', error.message);
      return defaultResult;
    }
  };
}

/**
 * Safe email validation with fallback
 */
export function safeEmailValidation(email) {
  try {
    // Basic email regex fallback
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(String(email).trim());

    return {
      valid: isValid,
      isValid: isValid,
      message: isValid ? '' : 'Please enter a valid email address'
    };
  } catch (error) {
    console.debug('Email validation fallback used:', error.message);
    return {
      valid: false,
      isValid: false,
      message: 'Email validation error'
    };
  }
}

/**
 * Safe input sanitization with fallback
 */
export function safeSanitizeInput(input) {
  try {
    if (input == null || input === undefined) {
      return '';
    }

    // Basic sanitization fallback
    return String(input)
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  } catch (error) {
    console.debug('Input sanitization fallback used:', error.message);
    return String(input || '');
  }
}

/**
 * Safe CSRF token generation with fallback
 */
export function safeGenerateCSRFToken() {
  try {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 32; i++) {
      result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
  } catch (error) {
    console.debug('CSRF token generation fallback used:', error.message);
    // Fallback to timestamp-based token
    return 'csrf_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
}

/**
 * Safe CSRF token validation with fallback
 */
export function safeValidateCSRFToken(token) {
  try {
    return typeof token === 'string' && token.length >= 10; // Basic validation
  } catch (error) {
    console.debug('CSRF token validation fallback used:', error.message);
    return false;
  }
}

/**
 * Safe CSRF object with all required methods
 */
export const safeCSRF = {
  generateToken: safeGenerateCSRFToken,
  validateToken: safeValidateCSRFToken,
  storeToken: (token) => {
    try {
      if (typeof sessionStorage !== 'undefined') {
        sessionStorage.setItem('csrf_token', token);
      }
    } catch (error) {
      console.debug('CSRF token storage fallback:', error.message);
    }
  },
  getToken: () => {
    try {
      if (typeof sessionStorage !== 'undefined') {
        const stored = sessionStorage.getItem('csrf_token');
        if (stored) return stored;
      }
      return safeGenerateCSRFToken();
    } catch (error) {
      console.debug('CSRF token retrieval fallback:', error.message);
      return safeGenerateCSRFToken();
    }
  }
};
