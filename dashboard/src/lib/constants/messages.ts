/**
 * Message Constants
 * Centralized user-facing messages and text content
 */

// Success messages
export const SUCCESS_MESSAGES = {
  // Authentication
  LOGIN_SUCCESS: 'Successfully logged in!',
  LOGOUT_SUCCESS: 'Successfully logged out!',
  REGISTER_SUCCESS: 'Account created successfully!',
  PASSWORD_RESET_SUCCESS: 'Password reset email sent!',
  PASSWORD_CHANGE_SUCCESS: 'Password changed successfully!',
  EMAIL_VERIFIED: 'Email verified successfully!',

  // Services
  SERVICE_CREATED: 'Service created successfully!',
  SERVICE_UPDATED: 'Service updated successfully!',
  SERVICE_DELETED: 'Service deleted successfully!',
  SERVICE_STARTED: 'Service started successfully!',
  SERVICE_STOPPED: 'Service stopped successfully!',
  SERVICE_RESTARTED: 'Service restarted successfully!',

  // Containers
  CONTAINER_STARTED: 'Container started successfully!',
  CONTAINER_STOPPED: 'Container stopped successfully!',
  CONTAINER_RESTARTED: 'Container restarted successfully!',
  CONTAINER_REMOVED: 'Container removed successfully!',

  // Images
  IMAGE_PULLED: 'Image pulled successfully!',
  IMAGE_BUILT: 'Image built successfully!',
  IMAGE_REMOVED: 'Image removed successfully!',
  IMAGE_TAGGED: 'Image tagged successfully!',

  // Networks
  NETWORK_CREATED: 'Network created successfully!',
  NETWORK_REMOVED: 'Network removed successfully!',
  NETWORK_CONNECTED: 'Container connected to network!',
  NETWORK_DISCONNECTED: 'Container disconnected from network!',

  // Volumes
  VOLUME_CREATED: 'Volume created successfully!',
  VOLUME_REMOVED: 'Volume removed successfully!',

  // Users
  USER_CREATED: 'User created successfully!',
  USER_UPDATED: 'User updated successfully!',
  USER_DELETED: 'User deleted successfully!',
  USER_ACTIVATED: 'User activated successfully!',
  USER_DEACTIVATED: 'User deactivated successfully!',

  // Settings
  SETTINGS_SAVED: 'Settings saved successfully!',
  SETTINGS_RESET: 'Settings reset to defaults!',
  BACKUP_CREATED: 'Backup created successfully!',
  BACKUP_RESTORED: 'Backup restored successfully!',

  // System
  SYSTEM_PRUNED: 'System cleaned up successfully!',
  CACHE_CLEARED: 'Cache cleared successfully!',

  // General
  SAVED: 'Saved successfully!',
  UPDATED: 'Updated successfully!',
  DELETED: 'Deleted successfully!',
  COPIED: 'Copied to clipboard!',
  EXPORTED: 'Data exported successfully!',
  IMPORTED: 'Data imported successfully!',
} as const;

// Error messages
export const ERROR_MESSAGES = {
  // Authentication
  INVALID_CREDENTIALS: 'Invalid username or password',
  UNAUTHORIZED: 'You are not authorized to perform this action',
  SESSION_EXPIRED: 'Your session has expired. Please log in again.',
  LOGIN_FAILED: 'Login failed. Please try again.',
  REGISTER_FAILED: 'Registration failed. Please try again.',
  PASSWORD_RESET_FAILED: 'Failed to send password reset email',
  WEAK_PASSWORD: 'Password must be at least 8 characters long',
  PASSWORD_MISMATCH: 'Passwords do not match',
  EMAIL_IN_USE: 'Email address is already in use',
  USERNAME_IN_USE: 'Username is already taken',

  // Services
  SERVICE_NOT_FOUND: 'Service not found',
  SERVICE_CREATE_FAILED: 'Failed to create service',
  SERVICE_UPDATE_FAILED: 'Failed to update service',
  SERVICE_DELETE_FAILED: 'Failed to delete service',
  SERVICE_START_FAILED: 'Failed to start service',
  SERVICE_STOP_FAILED: 'Failed to stop service',
  SERVICE_RESTART_FAILED: 'Failed to restart service',
  SERVICE_NAME_REQUIRED: 'Service name is required',
  SERVICE_IMAGE_REQUIRED: 'Docker image is required',
  INVALID_SERVICE_NAME: 'Invalid service name format',
  DUPLICATE_SERVICE_NAME: 'Service name already exists',
  INVALID_PORT_MAPPING: 'Invalid port mapping',

  // Containers
  CONTAINER_NOT_FOUND: 'Container not found',
  CONTAINER_START_FAILED: 'Failed to start container',
  CONTAINER_STOP_FAILED: 'Failed to stop container',
  CONTAINER_RESTART_FAILED: 'Failed to restart container',
  CONTAINER_REMOVE_FAILED: 'Failed to remove container',
  CONTAINER_EXEC_FAILED: 'Failed to execute command in container',

  // Images
  IMAGE_NOT_FOUND: 'Image not found',
  IMAGE_PULL_FAILED: 'Failed to pull image',
  IMAGE_BUILD_FAILED: 'Failed to build image',
  IMAGE_REMOVE_FAILED: 'Failed to remove image',
  IMAGE_TAG_FAILED: 'Failed to tag image',
  INVALID_IMAGE_NAME: 'Invalid image name format',

  // Networks
  NETWORK_NOT_FOUND: 'Network not found',
  NETWORK_CREATE_FAILED: 'Failed to create network',
  NETWORK_REMOVE_FAILED: 'Failed to remove network',
  NETWORK_CONNECT_FAILED: 'Failed to connect container to network',
  NETWORK_DISCONNECT_FAILED: 'Failed to disconnect container from network',
  INVALID_NETWORK_NAME: 'Invalid network name format',
  NETWORK_IN_USE: 'Network is currently in use',

  // Volumes
  VOLUME_NOT_FOUND: 'Volume not found',
  VOLUME_CREATE_FAILED: 'Failed to create volume',
  VOLUME_REMOVE_FAILED: 'Failed to remove volume',
  INVALID_VOLUME_NAME: 'Invalid volume name format',
  VOLUME_IN_USE: 'Volume is currently in use',

  // Users
  USER_NOT_FOUND: 'User not found',
  USER_CREATE_FAILED: 'Failed to create user',
  USER_UPDATE_FAILED: 'Failed to update user',
  USER_DELETE_FAILED: 'Failed to delete user',
  INVALID_EMAIL: 'Invalid email address format',
  INVALID_USERNAME: 'Invalid username format',

  // System
  SYSTEM_ERROR: 'A system error occurred',
  DOCKER_UNAVAILABLE: 'Docker daemon is not available',
  CONNECTION_FAILED: 'Failed to connect to Docker daemon',
  INSUFFICIENT_PERMISSIONS: 'Insufficient permissions to perform this action',
  RESOURCE_LIMIT_EXCEEDED: 'Resource limit exceeded',
  DISK_SPACE_LOW: 'Low disk space warning',
  MEMORY_LIMIT_EXCEEDED: 'Memory limit exceeded',

  // Network
  NETWORK_ERROR: 'Network error occurred',
  REQUEST_TIMEOUT: 'Request timed out',
  SERVER_UNAVAILABLE: 'Server is currently unavailable',
  CONNECTION_LOST: 'Connection lost. Please check your internet connection.',

  // Validation
  REQUIRED_FIELD: 'This field is required',
  INVALID_FORMAT: 'Invalid format',
  VALUE_TOO_LONG: 'Value is too long',
  VALUE_TOO_SHORT: 'Value is too short',
  INVALID_NUMBER: 'Must be a valid number',
  NUMBER_TOO_SMALL: 'Number is too small',
  NUMBER_TOO_LARGE: 'Number is too large',
  INVALID_DATE: 'Invalid date format',
  INVALID_URL: 'Invalid URL format',

  // File operations
  FILE_NOT_FOUND: 'File not found',
  FILE_TOO_LARGE: 'File size exceeds limit',
  INVALID_FILE_TYPE: 'Invalid file type',
  UPLOAD_FAILED: 'File upload failed',
  DOWNLOAD_FAILED: 'File download failed',

  // General
  UNKNOWN_ERROR: 'An unknown error occurred',
  OPERATION_FAILED: 'Operation failed',
  PERMISSION_DENIED: 'Permission denied',
  NOT_FOUND: 'Resource not found',
  CONFLICT: 'Resource conflict',
  RATE_LIMITED: 'Too many requests. Please try again later.',
  MAINTENANCE_MODE: 'System is under maintenance',
} as const;

// Info messages
export const INFO_MESSAGES = {
  LOADING: 'Loading...',
  PROCESSING: 'Processing...',
  SAVING: 'Saving...',
  DELETING: 'Deleting...',
  CONNECTING: 'Connecting...',
  DISCONNECTING: 'Disconnecting...',
  STARTING: 'Starting...',
  STOPPING: 'Stopping...',
  RESTARTING: 'Restarting...',
  BUILDING: 'Building...',
  PULLING: 'Pulling...',
  PUSHING: 'Pushing...',
  UPLOADING: 'Uploading...',
  DOWNLOADING: 'Downloading...',
  SYNCING: 'Syncing...',
  UPDATING: 'Updating...',
  REFRESHING: 'Refreshing...',
  SEARCHING: 'Searching...',
  VALIDATING: 'Validating...',
  AUTHENTICATING: 'Authenticating...',

  // Status messages
  NO_DATA: 'No data available',
  EMPTY_LIST: 'No items found',
  SEARCH_NO_RESULTS: 'No results found for your search',
  FILTER_NO_RESULTS: 'No items match your filters',

  // Service status
  SERVICE_RUNNING: 'Service is running',
  SERVICE_STOPPED: 'Service is stopped',
  SERVICE_STARTING: 'Service is starting',
  SERVICE_STOPPING: 'Service is stopping',
  SERVICE_HEALTHY: 'Service is healthy',
  SERVICE_UNHEALTHY: 'Service is unhealthy',

  // System status
  SYSTEM_HEALTHY: 'System is healthy',
  SYSTEM_WARNING: 'System warning',
  SYSTEM_CRITICAL: 'System critical',
  DOCKER_CONNECTED: 'Connected to Docker daemon',
  DOCKER_DISCONNECTED: 'Disconnected from Docker daemon',

  // Auto-refresh
  AUTO_REFRESH_ENABLED: 'Auto-refresh enabled',
  AUTO_REFRESH_DISABLED: 'Auto-refresh disabled',
  LAST_UPDATED: 'Last updated',

  // Navigation
  REDIRECTING: 'Redirecting...',
  PAGE_NOT_FOUND: 'Page not found',
  ACCESS_DENIED: 'Access denied',

  // Features
  FEATURE_COMING_SOON: 'This feature is coming soon',
  FEATURE_UNAVAILABLE: 'This feature is currently unavailable',
  BETA_FEATURE: 'This is a beta feature',
  EXPERIMENTAL_FEATURE: 'This is an experimental feature',
} as const;

// Warning messages
export const WARNING_MESSAGES = {
  UNSAVED_CHANGES: 'You have unsaved changes. Are you sure you want to leave?',
  DELETE_CONFIRMATION: 'Are you sure you want to delete this item?',
  DESTRUCTIVE_ACTION: 'This action cannot be undone',
  FORCE_DELETE_WARNING: 'Force delete will remove the resource immediately',
  CONTAINER_RUNNING: 'Container is currently running',
  SERVICE_DEPENDENCIES: 'This service has dependencies that may be affected',
  NETWORK_IN_USE_WARNING: 'This network is currently being used by containers',
  VOLUME_DATA_LOSS: 'Deleting this volume will result in permanent data loss',
  SYSTEM_PRUNE_WARNING: 'This will remove all unused containers, networks, and images',
  LOW_DISK_SPACE: 'Disk space is running low',
  HIGH_MEMORY_USAGE: 'Memory usage is high',
  HIGH_CPU_USAGE: 'CPU usage is high',
  SESSION_TIMEOUT_WARNING: 'Your session will expire soon',
  WEAK_PASSWORD_WARNING: 'Your password is weak. Consider using a stronger password.',
  INSECURE_CONNECTION: 'You are using an insecure connection',
  OUTDATED_BROWSER: 'Your browser is outdated. Some features may not work properly.',
  JAVASCRIPT_DISABLED: 'JavaScript is disabled. Some features may not work.',
  COOKIES_DISABLED: 'Cookies are disabled. This may affect functionality.',
} as const;

// Button labels
export const BUTTON_LABELS = {
  // Actions
  CREATE: 'Create',
  SAVE: 'Save',
  UPDATE: 'Update',
  DELETE: 'Delete',
  REMOVE: 'Remove',
  CANCEL: 'Cancel',
  SUBMIT: 'Submit',
  CONFIRM: 'Confirm',
  CONTINUE: 'Continue',
  RETRY: 'Retry',
  REFRESH: 'Refresh',
  RELOAD: 'Reload',
  RESET: 'Reset',
  CLEAR: 'Clear',
  SEARCH: 'Search',
  FILTER: 'Filter',
  SORT: 'Sort',
  EXPORT: 'Export',
  IMPORT: 'Import',
  UPLOAD: 'Upload',
  DOWNLOAD: 'Download',
  COPY: 'Copy',
  PASTE: 'Paste',
  EDIT: 'Edit',
  VIEW: 'View',
  CLOSE: 'Close',
  MINIMIZE: 'Minimize',
  MAXIMIZE: 'Maximize',

  // Navigation
  BACK: 'Back',
  NEXT: 'Next',
  PREVIOUS: 'Previous',
  HOME: 'Home',
  DASHBOARD: 'Dashboard',

  // Authentication
  LOGIN: 'Log In',
  LOGOUT: 'Log Out',
  REGISTER: 'Register',
  SIGN_UP: 'Sign Up',
  SIGN_IN: 'Sign In',
  FORGOT_PASSWORD: 'Forgot Password',
  RESET_PASSWORD: 'Reset Password',
  CHANGE_PASSWORD: 'Change Password',

  // Service actions
  START: 'Start',
  STOP: 'Stop',
  RESTART: 'Restart',
  PAUSE: 'Pause',
  RESUME: 'Resume',
  SCALE: 'Scale',
  DEPLOY: 'Deploy',
  PULL: 'Pull',
  BUILD: 'Build',
  PUSH: 'Push',

  // Docker actions
  PRUNE: 'Prune',
  INSPECT: 'Inspect',
  LOGS: 'Logs',
  STATS: 'Stats',
  EXEC: 'Execute',
  ATTACH: 'Attach',
  COMMIT: 'Commit',

  // Toggle states
  ENABLE: 'Enable',
  DISABLE: 'Disable',
  SHOW: 'Show',
  HIDE: 'Hide',
  EXPAND: 'Expand',
  COLLAPSE: 'Collapse',
  LOCK: 'Lock',
  UNLOCK: 'Unlock',

  // Time-based
  AUTO: 'Auto',
  MANUAL: 'Manual',
  SCHEDULE: 'Schedule',
  NOW: 'Now',
  LATER: 'Later',

  // States
  LOADING: 'Loading...',
  PROCESSING: 'Processing...',
  SAVING: 'Saving...',
  DELETING: 'Deleting...',
  CONNECTING: 'Connecting...',

  // Generic
  OK: 'OK',
  YES: 'Yes',
  NO: 'No',
  APPLY: 'Apply',
  DONE: 'Done',
  FINISH: 'Finish',
  SKIP: 'Skip',
  HELP: 'Help',
  SETTINGS: 'Settings',
  OPTIONS: 'Options',
  PREFERENCES: 'Preferences',
  ABOUT: 'About',
} as const;

// Field labels
export const FIELD_LABELS = {
  // User fields
  USERNAME: 'Username',
  EMAIL: 'Email',
  PASSWORD: 'Password',
  CONFIRM_PASSWORD: 'Confirm Password',
  FIRST_NAME: 'First Name',
  LAST_NAME: 'Last Name',
  FULL_NAME: 'Full Name',
  PHONE: 'Phone Number',
  ROLE: 'Role',
  PERMISSIONS: 'Permissions',

  // Service fields
  SERVICE_NAME: 'Service Name',
  IMAGE: 'Docker Image',
  TAG: 'Tag',
  DESCRIPTION: 'Description',
  PORTS: 'Port Mappings',
  ENVIRONMENT: 'Environment Variables',
  VOLUMES: 'Volume Mounts',
  NETWORKS: 'Networks',
  RESTART_POLICY: 'Restart Policy',
  REPLICAS: 'Replicas',
  CPU_LIMIT: 'CPU Limit',
  MEMORY_LIMIT: 'Memory Limit',
  HEALTH_CHECK: 'Health Check',
  LABELS: 'Labels',

  // Container fields
  CONTAINER_NAME: 'Container Name',
  CONTAINER_ID: 'Container ID',
  STATUS: 'Status',
  STATE: 'State',
  UPTIME: 'Uptime',

  // Image fields
  REPOSITORY: 'Repository',
  SIZE: 'Size',
  CREATED: 'Created',
  ARCHITECTURE: 'Architecture',
  OS: 'Operating System',

  // Network fields
  NETWORK_NAME: 'Network Name',
  DRIVER: 'Driver',
  SUBNET: 'Subnet',
  GATEWAY: 'Gateway',
  IP_RANGE: 'IP Range',

  // Volume fields
  VOLUME_NAME: 'Volume Name',
  MOUNT_POINT: 'Mount Point',
  DRIVER_OPTIONS: 'Driver Options',

  // System fields
  VERSION: 'Version',
  API_VERSION: 'API Version',
  KERNEL_VERSION: 'Kernel Version',
  ARCHITECTURE_SYS: 'Architecture',
  TOTAL_MEMORY: 'Total Memory',
  AVAILABLE_MEMORY: 'Available Memory',
  CPU_CORES: 'CPU Cores',
  DISK_SPACE: 'Disk Space',

  // General fields
  NAME: 'Name',
  TYPE: 'Type',
  VALUE: 'Value',
  DATE: 'Date',
  TIME: 'Time',
  TIMESTAMP: 'Timestamp',
  URL: 'URL',
  PATH: 'Path',
  COMMAND: 'Command',
  ARGUMENTS: 'Arguments',
  OPTIONS: 'Options',
  PRIORITY: 'Priority',
  CATEGORY: 'Category',
  TAGS_FIELD: 'Tags',
  NOTES: 'Notes',
  COMMENTS: 'Comments',
} as const;

// Placeholders
export const PLACEHOLDERS = {
  SEARCH: 'Search...',
  SEARCH_SERVICES: 'Search services...',
  SEARCH_CONTAINERS: 'Search containers...',
  SEARCH_IMAGES: 'Search images...',
  SEARCH_USERS: 'Search users...',

  ENTER_NAME: 'Enter name...',
  ENTER_EMAIL: 'Enter email address...',
  ENTER_PASSWORD: 'Enter password...',
  ENTER_URL: 'Enter URL...',
  ENTER_COMMAND: 'Enter command...',
  ENTER_DESCRIPTION: 'Enter description...',

  SELECT_OPTION: 'Select an option...',
  SELECT_IMAGE: 'Select Docker image...',
  SELECT_NETWORK: 'Select network...',
  SELECT_VOLUME: 'Select volume...',
  SELECT_USER: 'Select user...',

  NO_DESCRIPTION: 'No description provided',
  NO_TAGS: 'No tags',
  NO_LABELS: 'No labels',
  NO_ENVIRONMENT: 'No environment variables',
  NO_PORTS: 'No port mappings',
  NO_VOLUMES: 'No volume mounts',

  EXAMPLE_EMAIL: 'user@example.com',
  EXAMPLE_USERNAME: 'myusername',
  EXAMPLE_SERVICE: 'my-service',
  EXAMPLE_IMAGE: 'nginx:latest',
  EXAMPLE_PORT: '8080:80',
  EXAMPLE_ENV: 'NODE_ENV=production',
  EXAMPLE_VOLUME: '/host/path:/container/path',
} as const;

// Time-related messages
export const TIME_MESSAGES = {
  JUST_NOW: 'Just now',
  SECONDS_AGO: (n: number) => `${n} second${n === 1 ? '' : 's'} ago`,
  MINUTES_AGO: (n: number) => `${n} minute${n === 1 ? '' : 's'} ago`,
  HOURS_AGO: (n: number) => `${n} hour${n === 1 ? '' : 's'} ago`,
  DAYS_AGO: (n: number) => `${n} day${n === 1 ? '' : 's'} ago`,
  WEEKS_AGO: (n: number) => `${n} week${n === 1 ? '' : 's'} ago`,
  MONTHS_AGO: (n: number) => `${n} month${n === 1 ? '' : 's'} ago`,
  YEARS_AGO: (n: number) => `${n} year${n === 1 ? '' : 's'} ago`,

  IN_SECONDS: (n: number) => `in ${n} second${n === 1 ? '' : 's'}`,
  IN_MINUTES: (n: number) => `in ${n} minute${n === 1 ? '' : 's'}`,
  IN_HOURS: (n: number) => `in ${n} hour${n === 1 ? '' : 's'}`,
  IN_DAYS: (n: number) => `in ${n} day${n === 1 ? '' : 's'}`,

  UPTIME: 'Uptime',
  DOWNTIME: 'Downtime',
  LAST_SEEN: 'Last seen',
  NEXT_UPDATE: 'Next update',
  REFRESH_IN: 'Refresh in',
  SESSION_EXPIRES: 'Session expires',
} as const;

// Status messages for different states
export const STATUS_MESSAGES = {
  RUNNING: 'Running',
  STOPPED: 'Stopped',
  STARTING: 'Starting',
  STOPPING: 'Stopping',
  PAUSED: 'Paused',
  RESTARTING: 'Restarting',
  REMOVING: 'Removing',
  CREATED: 'Created',
  EXITED: 'Exited',
  DEAD: 'Dead',

  HEALTHY: 'Healthy',
  UNHEALTHY: 'Unhealthy',
  UNKNOWN: 'Unknown',

  ONLINE: 'Online',
  OFFLINE: 'Offline',

  CONNECTED: 'Connected',
  DISCONNECTED: 'Disconnected',
  CONNECTING: 'Connecting',

  ACTIVE: 'Active',
  INACTIVE: 'Inactive',

  ENABLED: 'Enabled',
  DISABLED: 'Disabled',

  SUCCESS: 'Success',
  FAILED: 'Failed',
  PENDING: 'Pending',

  UP_TO_DATE: 'Up to date',
  OUTDATED: 'Outdated',
  UPDATING: 'Updating',
} as const;

// Export message types
export type SuccessMessage = keyof typeof SUCCESS_MESSAGES;
export type ErrorMessage = keyof typeof ERROR_MESSAGES;
export type InfoMessage = keyof typeof INFO_MESSAGES;
export type WarningMessage = keyof typeof WARNING_MESSAGES;
export type ButtonLabel = keyof typeof BUTTON_LABELS;
export type FieldLabel = keyof typeof FIELD_LABELS;
export type Placeholder = keyof typeof PLACEHOLDERS;
export type StatusMessage = keyof typeof STATUS_MESSAGES;
