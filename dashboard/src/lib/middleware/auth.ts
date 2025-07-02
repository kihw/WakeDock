/**
 * Authentication Middleware
 * Manages route protection and authentication checks
 */
import { redirect } from '@sveltejs/kit';
import { api } from '../api.js';
import type { RequestEvent } from '@sveltejs/kit';
/// <reference path="../../app.d.ts" />

interface AuthMiddlewareOptions {
  requireAuth?: boolean;
  requireAdmin?: boolean;
  redirectTo?: string;
}

/**
 * Authentication middleware for protecting routes
 */
export async function authMiddleware(event: RequestEvent, options: AuthMiddlewareOptions = {}) {
  const { requireAuth = true, requireAdmin = false, redirectTo = '/login' } = options;

  // Get token from cookie or local storage (handled by API client)
  const token = api.getToken();

  if (requireAuth && !token) {
    throw redirect(302, redirectTo);
  }

  if (token) {
    try {
      // Verify token and get current user
      const user = await api.auth.getCurrentUser();

      // Check admin requirements
      if (requireAdmin && user.role !== 'admin') {
        throw redirect(302, '/unauthorized');
      }

      // Add user to locals for use in components
      (event.locals as any).user = user;
      (event.locals as any).isAuthenticated = true;
    } catch (error) {
      // Token is invalid, clear it and redirect
      await api.auth.logout();

      if (requireAuth) {
        throw redirect(302, redirectTo);
      }

      (event.locals as any).user = null;
      (event.locals as any).isAuthenticated = false;
    }
  } else {
    (event.locals as any).user = null;
    (event.locals as any).isAuthenticated = false;
  }
}

/**
 * Check if user is authenticated (for use in components)
 */
export function isAuthenticated(): boolean {
  return api.isAuthenticated();
}

/**
 * Require authentication decorator for pages
 */
export function requireAuth(options: Omit<AuthMiddlewareOptions, 'requireAuth'> = {}) {
  return (event: RequestEvent) => authMiddleware(event, { ...options, requireAuth: true });
}

/**
 * Require admin access decorator for pages
 */
export function requireAdmin(
  options: Omit<AuthMiddlewareOptions, 'requireAuth' | 'requireAdmin'> = {}
) {
  return (event: RequestEvent) =>
    authMiddleware(event, {
      ...options,
      requireAuth: true,
      requireAdmin: true,
    });
}

/**
 * Optional authentication (for pages that work with/without auth)
 */
export function optionalAuth(options: Omit<AuthMiddlewareOptions, 'requireAuth'> = {}) {
  return (event: RequestEvent) => authMiddleware(event, { ...options, requireAuth: false });
}

/**
 * Check if user has specific permission
 */
export function hasPermission(user: any, permission: string): boolean {
  if (!user || !user.permissions) return false;

  // Admin has all permissions
  if (user.role === 'admin') return true;

  return user.permissions.includes(permission);
}

/**
 * Check if user has specific role
 */
export function hasRole(user: any, role: string): boolean {
  if (!user) return false;
  return user.role === role;
}

/**
 * Get current user from API
 */
export async function getCurrentUser() {
  try {
    return await api.auth.getCurrentUser();
  } catch {
    return null;
  }
}
