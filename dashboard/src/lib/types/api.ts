/**
 * API Type Definitions
 * Centralized type definitions for API requests and responses
 */

// Common API response structure
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
    hasNext?: boolean;
    hasPrev?: boolean;
  };
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: any;
}

// Pagination
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Authentication
export interface LoginRequest {
  username: string;
  password: string;
}

// Add type alias for backward compatibility
export type LoginCredentials = LoginRequest;

export interface LoginResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresIn: number;
  requiresTwoFactor?: boolean;
  twoFactorToken?: string;
}

export interface TwoFactorSetupRequest {
  password: string;
}

export interface TwoFactorSetupResponse {
  secret: string;
  qrCode: string;
  backupCodes: string[];
}

export interface TwoFactorVerifyRequest {
  code: string;
}

export interface TwoFactorDisableRequest {
  password: string;
  code: string;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface RefreshTokenResponse {
  token: string;
  refreshToken: string;
  expiresIn: number;
}

// User Management
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  permissions: string[];
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  password: string;
  roles?: string[];
  isActive?: boolean;
}

export interface UpdateUserRequest {
  email?: string;
  firstName?: string;
  lastName?: string;
  roles?: string[];
  isActive?: boolean;
}

// Docker Services
export interface DockerService {
  id: string;
  name: string;
  image: string;
  status: 'running' | 'stopped' | 'starting' | 'stopping' | 'error';
  state: string;
  health: 'healthy' | 'unhealthy' | 'starting' | 'unknown';
  ports: ServicePort[];
  networks: string[];
  volumes: ServiceVolume[];
  environment: ServiceEnvironment[];
  labels: Record<string, string>;
  replicas: {
    running: number;
    desired: number;
  };
  resources: {
    cpu: {
      limit?: number;
      usage?: number;
    };
    memory: {
      limit?: number;
      usage?: number;
    };
  };
  createdAt: string;
  updatedAt: string;
}

export interface ServicePort {
  host: number;
  container: number;
  protocol: 'tcp' | 'udp';
}

export interface ServiceVolume {
  host: string;
  container: string;
  mode: 'rw' | 'ro';
}

export interface ServiceEnvironment {
  key: string;
  value: string;
  isSecret: boolean;
}

export interface CreateServiceRequest {
  name: string;
  image: string;
  tag?: string;
  description?: string;
  ports?: ServicePort[];
  environment?: ServiceEnvironment[];
  volumes?: ServiceVolume[];
  networks?: string[];
  restart?: 'no' | 'always' | 'on-failure' | 'unless-stopped';
  replicas?: number;
  resources?: {
    cpu?: number;
    memory?: number;
  };
  healthCheck?: {
    command: string;
    interval: number;
    timeout: number;
    retries: number;
  };
  labels?: Record<string, string>;
}

export interface UpdateServiceRequest extends Partial<CreateServiceRequest> {
  id: string;
}

export interface ServiceAction {
  action: 'start' | 'stop' | 'restart' | 'remove';
  serviceId: string;
}

// Docker Containers
export interface DockerContainer {
  id: string;
  name: string;
  image: string;
  imageId: string;
  status: string;
  state: 'created' | 'running' | 'paused' | 'restarting' | 'removing' | 'exited' | 'dead';
  health?: 'healthy' | 'unhealthy' | 'starting' | 'none';
  ports: ContainerPort[];
  networks: Record<string, ContainerNetwork>;
  volumes: ContainerMount[];
  environment: string[];
  labels: Record<string, string>;
  stats?: ContainerStats;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
}

export interface ContainerPort {
  privatePort: number;
  publicPort?: number;
  type: 'tcp' | 'udp';
  ip?: string;
}

export interface ContainerNetwork {
  networkId: string;
  ipAddress: string;
  gateway: string;
  macAddress?: string;
}

export interface ContainerMount {
  type: 'bind' | 'volume' | 'tmpfs';
  source: string;
  destination: string;
  mode: string;
  rw: boolean;
}

export interface ContainerStats {
  cpu: {
    usage: number;
    limit: number;
    percentage: number;
  };
  memory: {
    usage: number;
    limit: number;
    percentage: number;
  };
  network: {
    rx_bytes: number;
    tx_bytes: number;
    rx_packets: number;
    tx_packets: number;
  };
  io: {
    read_bytes: number;
    write_bytes: number;
  };
  timestamp: string;
}

// Docker Images
export interface DockerImage {
  id: string;
  repository: string;
  tag: string;
  digest: string;
  size: number;
  created: string;
  labels: Record<string, string>;
  architecture: string;
  os: string;
  parentId?: string;
}

export interface PullImageRequest {
  image: string;
  tag?: string;
  auth?: {
    username: string;
    password: string;
    registry?: string;
  };
}

export interface BuildImageRequest {
  context: string;
  dockerfile?: string;
  tag: string;
  buildArgs?: Record<string, string>;
  labels?: Record<string, string>;
}

// Docker Networks
export interface DockerNetwork {
  id: string;
  name: string;
  driver: string;
  scope: 'local' | 'global' | 'swarm';
  ipam: {
    driver: string;
    config: Array<{
      subnet: string;
      gateway: string;
    }>;
  };
  containers: Record<
    string,
    {
      name: string;
      ipv4Address: string;
      ipv6Address?: string;
      macAddress?: string;
    }
  >;
  options: Record<string, string>;
  labels: Record<string, string>;
  created: string;
}

export interface CreateNetworkRequest {
  name: string;
  driver?: string;
  subnet?: string;
  gateway?: string;
  ipRange?: string;
  options?: Record<string, string>;
  labels?: Record<string, string>;
}

// Docker Volumes
export interface DockerVolume {
  name: string;
  driver: string;
  mountpoint: string;
  status?: Record<string, any>;
  labels: Record<string, string>;
  scope: 'local' | 'global';
  options: Record<string, string>;
  usageData?: {
    size: number;
    refCount: number;
  };
  createdAt: string;
}

export interface CreateVolumeRequest {
  name: string;
  driver?: string;
  driverOpts?: Record<string, string>;
  labels?: Record<string, string>;
}

// System Information
export interface SystemInfo {
  version: string;
  apiVersion: string;
  gitCommit: string;
  goVersion: string;
  os: string;
  arch: string;
  kernelVersion: string;
  buildTime: string;
  containers: {
    total: number;
    running: number;
    paused: number;
    stopped: number;
  };
  images: {
    total: number;
    size: number;
  };
  volumes: {
    total: number;
    size: number;
  };
  networks: {
    total: number;
  };
  plugins: {
    volume: string[];
    network: string[];
    authorization: string[];
    log: string[];
  };
  warnings?: string[];
}

export interface SystemStats {
  timestamp: string;
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
  load: {
    load1: number;
    load5: number;
    load15: number;
  };
}

// Events
export interface DockerEvent {
  id: string;
  type: 'container' | 'image' | 'volume' | 'network' | 'daemon' | 'service';
  action: string;
  actor: {
    id: string;
    attributes: Record<string, string>;
  };
  scope: 'local' | 'swarm';
  time: number;
  timeNano: number;
}

// Logs
export interface LogEntry {
  timestamp: string;
  level: 'error' | 'warn' | 'info' | 'debug';
  message: string;
  source: string;
  metadata?: Record<string, any>;
}

export interface LogsRequest {
  serviceId?: string;
  containerId?: string;
  since?: string;
  until?: string;
  tail?: number;
  follow?: boolean;
  timestamps?: boolean;
}

// Health Checks
export interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'starting';
  failingStreak: number;
  log: Array<{
    start: string;
    end: string;
    exitCode: number;
    output: string;
  }>;
}

// Security
export interface SecurityScan {
  id: string;
  imageId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  vulnerabilities: Vulnerability[];
  summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  createdAt: string;
  completedAt?: string;
}

export interface Vulnerability {
  id: string;
  packageName: string;
  installedVersion: string;
  fixedVersion?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  references: string[];
}

// Analytics
export interface AnalyticsData {
  period: string;
  metrics: {
    services: {
      total: number;
      running: number;
      stopped: number;
      failed: number;
    };
    containers: {
      total: number;
      running: number;
      stopped: number;
    };
    resources: {
      cpu: {
        average: number;
        peak: number;
      };
      memory: {
        average: number;
        peak: number;
      };
      network: {
        rx_bytes: number;
        tx_bytes: number;
      };
    };
    events: {
      total: number;
      errors: number;
      warnings: number;
    };
  };
  trends: Array<{
    timestamp: string;
    cpu: number;
    memory: number;
    containers: number;
    services: number;
  }>;
}

// Settings
export interface Settings {
  general: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
    refreshInterval: number;
  };
  docker: {
    host: string;
    tls: boolean;
    certPath?: string;
    version: string;
  };
  notifications: {
    enabled: boolean;
    email: boolean;
    webhook?: string;
    events: string[];
  };
  security: {
    sessionTimeout: number;
    enableAuditLog: boolean;
    enableImageScanning: boolean;
    allowDangerousOperations: boolean;
  };
  backup: {
    enabled: boolean;
    frequency: 'daily' | 'weekly' | 'monthly';
    retention: number;
    location: string;
  };
}

export interface UpdateSettingsRequest extends Partial<Settings> {}

// WebSocket Events
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface ServiceStatusUpdate {
  serviceId: string;
  status: string;
  health?: string;
  replicas?: {
    running: number;
    desired: number;
  };
}

export interface ContainerStatsUpdate {
  containerId: string;
  stats: ContainerStats;
}

export interface SystemStatsUpdate {
  stats: SystemStats;
}
