export interface User {
    id: number;
    username: string;
    email: string;
    role: 'admin' | 'user';
    active: boolean;
    created_at: string;
    updated_at: string;
    last_login?: string;
}

export interface CreateUserRequest {
    username: string;
    email: string;
    password: string;
    role: 'admin' | 'user';
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
