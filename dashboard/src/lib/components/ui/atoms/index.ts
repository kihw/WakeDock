// Atomic Components - WakeDock Design System
// These are the foundational UI components that can be used throughout the application

// UNIFIED BUTTON SYSTEM (TASK-UI-001) - Use UnifiedButton for all new development
export { default as UnifiedButton } from './UnifiedButton.svelte';
export type * from './UnifiedButton.types';

// LEGACY BUTTON COMPONENTS (DEPRECATED) - Will be removed after migration
// Use UnifiedButton instead of these components
export { default as Button } from './Button.svelte';
export { default as BaseButton } from './BaseButton.svelte';
export { default as PrimaryButton } from './PrimaryButton.svelte';
export { default as SecondaryButton } from './SecondaryButton.svelte';
export { default as IconButton } from './IconButton.svelte';
// REFACTORED INPUT SYSTEM (TASK-UI-002) - Use BaseInput for new development
export { default as BaseInput } from './BaseInput.svelte';
export type * from './BaseInput.types';

// LEGACY INPUT COMPONENTS (DEPRECATED) - Will be removed after migration
// Use BaseInput, FormInput, or FieldInput instead
export { default as Input } from './Input.svelte';
export { default as InputForm } from './InputForm.svelte';
export { default as Badge } from './Badge.svelte';
export { default as Card } from './Card.svelte';
export { default as LoadingSpinner } from './LoadingSpinner.svelte';
export { default as Toast } from './Toast.svelte';
export { default as Avatar } from './Avatar.svelte';
export { default as Alert } from './Alert.svelte';

// Re-export for convenience
export * from './Button.svelte';
export * from './Input.svelte';
export * from './Badge.svelte';
export * from './Card.svelte';
export * from './LoadingSpinner.svelte';
export * from './Toast.svelte';
export * from './Avatar.svelte';
