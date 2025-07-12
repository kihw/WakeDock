/**
 * Authentication Types
 * Separate types for frontend forms vs API requests
 */

// Frontend form data (what LoginForm.svelte collects)
export interface LoginCredentials {
  usernameOrEmail: string;
  password: string;
  twoFactorCode?: string;
  rememberMe?: boolean;
  csrfToken?: string;
}

// API request data (what gets sent to backend)
export interface LoginRequest {
  username: string;
  password: string;
}

// Login result from form submission
export interface LoginResult {
  success: boolean;
  requiresTwoFactor?: boolean;
  twoFactorToken?: string;
  error?: string;
}

// Login options for auth store
export interface LoginOptions {
  rememberMe?: boolean;
  device?: string;
  fingerprint?: string;
}