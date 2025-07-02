/**
 * Formatter Utilities
 * Data formatting functions for display
 */

/**
 * Format bytes to human readable format
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format uptime in seconds to human readable format
 */
export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  const parts: string[] = [];

  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

  return parts.join(' ');
}

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const target = typeof date === 'string' ? new Date(date) : date;
  const diff = now.getTime() - target.getTime();

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const weeks = Math.floor(days / 7);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);

  if (years > 0) return `${years} year${years > 1 ? 's' : ''} ago`;
  if (months > 0) return `${months} month${months > 1 ? 's' : ''} ago`;
  if (weeks > 0) return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  if (seconds > 0) return `${seconds} second${seconds > 1 ? 's' : ''} ago`;

  return 'just now';
}

/**
 * Format date to local string
 */
export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const target = typeof date === 'string' ? new Date(date) : date;

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };

  return target.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

/**
 * Format percentage
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format number with thousands separator
 */
export function formatNumber(value: number, decimals?: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format currency
 */
export function formatCurrency(value: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(value);
}

/**
 * Format duration in milliseconds to human readable
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  return `${(ms / 3600000).toFixed(1)}h`;
}

/**
 * Format service status with color
 */
export function formatServiceStatus(status: string): { text: string; color: string; icon: string } {
  switch (status.toLowerCase()) {
    case 'running':
      return { text: 'Running', color: 'text-green-600', icon: '🟢' };
    case 'stopped':
      return { text: 'Stopped', color: 'text-gray-600', icon: '⚫' };
    case 'error':
      return { text: 'Error', color: 'text-red-600', icon: '🔴' };
    case 'starting':
      return { text: 'Starting', color: 'text-yellow-600', icon: '🟡' };
    case 'stopping':
      return { text: 'Stopping', color: 'text-orange-600', icon: '🟠' };
    default:
      return { text: 'Unknown', color: 'text-gray-400', icon: '❓' };
  }
}

/**
 * Format health status
 */
export function formatHealthStatus(status: string): { text: string; color: string; icon: string } {
  switch (status?.toLowerCase()) {
    case 'healthy':
      return { text: 'Healthy', color: 'text-green-600', icon: '✅' };
    case 'unhealthy':
      return { text: 'Unhealthy', color: 'text-red-600', icon: '❌' };
    case 'unknown':
    default:
      return { text: 'Unknown', color: 'text-gray-400', icon: '❓' };
  }
}

/**
 * Format log level with color
 */
export function formatLogLevel(level: string): { text: string; color: string } {
  switch (level.toLowerCase()) {
    case 'debug':
      return { text: 'DEBUG', color: 'text-blue-600' };
    case 'info':
      return { text: 'INFO', color: 'text-green-600' };
    case 'warn':
    case 'warning':
      return { text: 'WARN', color: 'text-yellow-600' };
    case 'error':
      return { text: 'ERROR', color: 'text-red-600' };
    default:
      return { text: level.toUpperCase(), color: 'text-gray-600' };
  }
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Capitalize first letter
 */
export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

/**
 * Convert snake_case to Title Case
 */
export function snakeToTitle(text: string): string {
  return text
    .split('_')
    .map((word) => capitalize(word))
    .join(' ');
}

/**
 * Convert camelCase to Title Case
 */
export function camelToTitle(text: string): string {
  return text
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
}

/**
 * Format Docker image name for display
 */
export function formatDockerImage(image: string): { registry?: string; name: string; tag: string } {
  const parts = image.split('/');
  const lastPart = parts[parts.length - 1];
  const [name, tag = 'latest'] = lastPart.split(':');

  if (parts.length === 1) {
    // Official image (e.g., "nginx:latest")
    return { name, tag };
  } else if (parts.length === 2) {
    // User/org image (e.g., "library/nginx:latest")
    return { name: `${parts[0]}/${name}`, tag };
  } else {
    // Full registry path (e.g., "registry.com/user/nginx:latest")
    const registry = parts.slice(0, -1).join('/');
    return { registry, name, tag };
  }
}

/**
 * Format environment variables for display
 */
export function formatEnvVars(
  envVars: Record<string, string>
): Array<{ key: string; value: string; masked?: boolean }> {
  return Object.entries(envVars).map(([key, value]) => {
    const isSensitive = /password|secret|key|token/i.test(key);
    return {
      key,
      value: isSensitive ? '***' : value,
      masked: isSensitive,
    };
  });
}

/**
 * Format port mapping for display
 */
export function formatPortMapping(port: {
  host: number;
  container: number;
  protocol?: string;
}): string {
  const protocol = port.protocol || 'tcp';
  return `${port.host}:${port.container}/${protocol}`;
}

/**
 * Format volume mapping for display
 */
export function formatVolumeMapping(volume: {
  host: string;
  container: string;
  mode?: string;
}): string {
  const mode = volume.mode || 'rw';
  return `${volume.host}:${volume.container}:${mode}`;
}
