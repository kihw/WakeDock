export interface User {
  id: string | number;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: 'admin' | 'user';
  roles: string[];
  permissions: string[];
  active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  // 2FA fields
  twoFactorEnabled?: boolean;
  twoFactorSecret?: string;
  backupCodes?: string[];
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  role: 'admin' | 'user';
  roles?: string[];
  active: boolean;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  password?: string;
  role?: 'admin' | 'user';
  active?: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface UserSession {
  user: User;
  token: string;
  expiresAt: Date;
}

export type UserRole = 'admin' | 'user' | 'viewer';

export const UserRoles = {
  ADMIN: 'admin' as UserRole,
  USER: 'user' as UserRole,
  VIEWER: 'viewer' as UserRole,
} as const;

export const UserPermissions = {
  // Service permissions
  SERVICE_CREATE: 'service:create',
  SERVICE_READ: 'service:read',
  SERVICE_UPDATE: 'service:update',
  SERVICE_DELETE: 'service:delete',
  SERVICE_LOGS: 'service:logs',

  // User permissions
  USER_CREATE: 'user:create',
  USER_READ: 'user:read',
  USER_UPDATE: 'user:update',
  USER_DELETE: 'user:delete',

  // System permissions
  SYSTEM_READ: 'system:read',
  SYSTEM_UPDATE: 'system:update',
  ANALYTICS_READ: 'analytics:read',
  SETTINGS_UPDATE: 'settings:update',
} as const;

export function hasPermission(user: User, permission: string): boolean {
  return (
    user.permissions?.includes(permission) || user.roles?.includes('admin') || user.role === 'admin'
  );
}

export function hasRole(user: User, role: UserRole): boolean {
  return user.roles?.includes(role) || user.role === role;
}

export function isAdmin(user: User): boolean {
  return hasRole(user, UserRoles.ADMIN);
}

export function canManageUsers(user: User): boolean {
  return (
    hasPermission(user, UserPermissions.USER_CREATE) ||
    hasPermission(user, UserPermissions.USER_UPDATE) ||
    hasPermission(user, UserPermissions.USER_DELETE)
  );
}

export function canManageServices(user: User): boolean {
  return (
    hasPermission(user, UserPermissions.SERVICE_CREATE) ||
    hasPermission(user, UserPermissions.SERVICE_UPDATE) ||
    hasPermission(user, UserPermissions.SERVICE_DELETE)
  );
}
