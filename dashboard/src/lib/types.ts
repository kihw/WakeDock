/**
 * TypeScript type definitions for WakeDock Dashboard
 */

// User and Authentication
export interface User {
    id: string;
    email: string;
    name: string;
    role: 'admin' | 'user' | 'readonly';
    created_at: string;
    last_login?: string;
    is_active: boolean;
}

export interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
}

// Services
export interface Service {
    id: string;
    name: string;
    image: string;
    status: 'running' | 'stopped' | 'starting' | 'stopping' | 'failed' | 'restarting';
    ports: Port[];
    environment: Record<string, string>;
    volumes: Volume[];
    networks: string[];
    created_at: string;
    updated_at: string;
    user_id: string;
    domain?: string;
    health_check?: HealthCheck;
    metrics?: ServiceMetrics;
}

export interface Port {
    internal: number;
    external?: number;
    protocol: 'tcp' | 'udp';
}

export interface Volume {
    host: string;
    container: string;
    mode: 'rw' | 'ro';
}

export interface HealthCheck {
    command: string;
    interval: number;
    timeout: number;
    retries: number;
    start_period: number;
}

export interface ServiceMetrics {
    cpu_usage: number;
    memory_usage: number;
    memory_limit: number;
    network_rx: number;
    network_tx: number;
    disk_read: number;
    disk_write: number;
    timestamp: string;
}

// System Metrics
export interface SystemMetrics {
    cpu: {
        usage: number;
        cores: number;
    };
    memory: {
        used: number;
        total: number;
        available: number;
        percentage: number;
    };
    disk: {
        used: number;
        total: number;
        available: number;
        percentage: number;
    };
    network: {
        rx_bytes: number;
        tx_bytes: number;
        rx_packets: number;
        tx_packets: number;
    };
    docker: {
        containers_running: number;
        containers_stopped: number;
        images_count: number;
        volumes_count: number;
    };
    timestamp: string;
}

// Logs
export interface LogEntry {
    id: string;
    service_id?: string;
    level: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
    message: string;
    timestamp: string;
    source: string;
    metadata?: Record<string, unknown>;
}

// WebSocket Messages
export interface WebSocketMessage {
    type: 'service_update' | 'service_removed' | 'metrics_update' | 'log_entry' | 'notification' | 'error' | 'ping' | 'pong' | 'auth' | 'subscribe' | 'unsubscribe';
    data?: unknown;
    channel?: string;
    timestamp?: string;
    token?: string;
}

// Settings
export interface SystemSettings {
    general: {
        app_name: string;
        app_description: string;
        default_domain: string;
        admin_email: string;
    };
    docker: {
        socket_path: string;
        network_name: string;
        default_restart_policy: string;
        image_pull_policy: 'always' | 'if-not-present' | 'never';
    };
    caddy: {
        config_path: string;
        auto_https: boolean;
        admin_api_enabled: boolean;
        admin_api_port: number;
    };
    security: {
        session_timeout: number;
        max_login_attempts: number;
        password_min_length: number;
        require_strong_passwords: boolean;
        rate_limit_enabled: boolean;
        rate_limit_requests: number;
        rate_limit_window: number;
    };
    logging: {
        level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
        max_log_size: number;
        log_retention_days: number;
        structured_logging: boolean;
    };
    monitoring: {
        metrics_enabled: boolean;
        health_check_interval: number;
        alert_email: string;
        slack_webhook_url: string;
    };
}

// Notifications
export interface Notification {
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
    actions?: NotificationAction[];
}

export interface NotificationAction {
    label: string;
    action: string;
    style: 'primary' | 'secondary' | 'danger';
}

// Dashboard
export interface DashboardStats {
    services: {
        total: number;
        running: number;
        stopped: number;
        failed: number;
    };
    system: {
        cpu_usage: number;
        memory_usage: number;
        disk_usage: number;
        uptime: string;
    };
    recent_activity: ActivityEntry[];
}

export interface ActivityEntry {
    id: string;
    type: 'service_started' | 'service_stopped' | 'service_created' | 'service_deleted' | 'user_login' | 'system_alert';
    description: string;
    timestamp: string;
    user_id?: string;
    service_id?: string;
}

// API Response types
export interface ApiResponse<T = unknown> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

export interface PaginatedResponse<T = unknown> {
    data: T[];
    pagination: {
        page: number;
        limit: number;
        total: number;
        pages: number;
    };
}

// Form types
export interface FormField {
    name: string;
    label: string;
    type: 'text' | 'email' | 'password' | 'number' | 'select' | 'checkbox' | 'textarea';
    required: boolean;
    placeholder?: string;
    options?: { value: string; label: string }[];
    validation?: {
        min?: number;
        max?: number;
        pattern?: string;
        custom?: (value: unknown) => string | null;
    };
}

export interface FormData {
    [key: string]: unknown;
}

export interface FormErrors {
    [key: string]: string;
}

// Theme and UI
export interface ThemeConfig {
    mode: 'light' | 'dark' | 'auto';
    primaryColor: string;
    accentColor: string;
    fontSize: 'sm' | 'md' | 'lg';
    sidebarCollapsed: boolean;
    animations: boolean;
}

// Cache
export interface CacheEntry<T = unknown> {
    data: T;
    timestamp: number;
    expiresAt: number;
}

export interface CacheStats {
    hits: number;
    misses: number;
    size: number;
    maxSize: number;
}
