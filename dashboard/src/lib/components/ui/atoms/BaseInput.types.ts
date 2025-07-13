/**
 * TypeScript definitions for refactored Input system
 * TASK-UI-002: Refactorisation du Système d'Input
 */

// Input types supported across the system
export type InputType = 
  | 'text'
  | 'email'
  | 'password'
  | 'number'
  | 'tel'
  | 'url'
  | 'search'
  | 'date'
  | 'time'
  | 'datetime-local'
  | 'month'
  | 'week'
  | 'color'
  | 'file'
  | 'range';

// Input sizes
export type InputSize = 'sm' | 'md' | 'lg';

// Input variants
export type InputVariant = 'default' | 'success' | 'warning' | 'error';

// Icon position for enhanced inputs
export type IconPosition = 'left' | 'right';

// Base input props (atomic level)
export interface BaseInputProps {
  // Input configuration
  type?: InputType;
  value?: string | number;
  placeholder?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;

  // Sizing and appearance
  size?: InputSize;
  variant?: InputVariant;
  fullWidth?: boolean;

  // HTML attributes
  id?: string;
  name?: string;
  autocomplete?: string;
  autofocus?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number | string;
  max?: number | string;
  step?: number | string;
  pattern?: string;

  // Accessibility
  ariaLabel?: string;
  ariaDescribedBy?: string;
  testId?: string;

  // Custom styling
  className?: string;
}

// Enhanced input props (molecular level)
export interface FormInputProps extends BaseInputProps {
  // Label and help text
  label?: string;
  helperText?: string;
  error?: string;
  success?: string;

  // Validation
  validationRules?: ValidationRule[];
  validateOnBlur?: boolean;
  validateOnInput?: boolean;

  // Form integration
  formName?: string;
  fieldName?: string;
}

// Field input props (full-featured)
export interface FieldInputProps extends FormInputProps {
  // Icons and decorations
  leftIcon?: string;
  rightIcon?: string;
  iconPosition?: IconPosition;

  // Advanced features
  clearable?: boolean;
  showPasswordToggle?: boolean;
  loading?: boolean;
  debounceMs?: number;

  // Copy/paste actions
  copyable?: boolean;
  pasteAction?: () => void;
}

// Validation rule interface
export interface ValidationRule {
  type: 'required' | 'email' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  value?: string | number | RegExp;
  message?: string;
  validator?: (value: string | number) => boolean | string;
}

// Input events
export interface InputEvents {
  input: Event;
  change: Event;
  focus: FocusEvent;
  blur: FocusEvent;
  keydown: KeyboardEvent;
  keyup: KeyboardEvent;
  clear?: Event;
  togglePassword?: Event;
  validate?: { isValid: boolean; errors: string[] };
}

// Enhanced input events (for molecular/organism components)
export interface EnhancedInputEvents extends InputEvents {
  iconClick?: { position: IconPosition; event: MouseEvent };
  copy?: { value: string };
  paste?: { value: string };
  debounceInput?: { value: string | number };
}

// Input state interface
export interface InputState {
  value: string | number;
  isFocused: boolean;
  isValid: boolean;
  errors: string[];
  isDirty: boolean;
  isTouched: boolean;
}

// Validation result interface
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// Input configuration for forms
export interface InputConfig {
  component: 'BaseInput' | 'FormInput' | 'FieldInput';
  props: BaseInputProps | FormInputProps | FieldInputProps;
  validation?: ValidationRule[];
  dependencies?: string[]; // Other field names this input depends on
}

// Form field registry interface
export interface FormFieldRegistry {
  [fieldName: string]: InputConfig;
}

// Design system integration
export interface InputDesignTokens {
  sizes: Record<InputSize, {
    padding: string;
    fontSize: string;
    height: string;
  }>;
  variants: Record<InputVariant, {
    borderColor: string;
    focusBorderColor: string;
    backgroundColor: string;
    textColor: string;
  }>;
  states: {
    disabled: string;
    readonly: string;
    focus: string;
    hover: string;
  };
}

// Migration helpers for legacy components
export interface LegacyInputProps {
  // From old Input.svelte (722 lines)
  leftIcon?: string;
  rightIcon?: string;
  clearable?: boolean;
  showPasswordToggle?: boolean;
  loading?: boolean;
  debounceMs?: number;
  errorText?: string;
  successText?: string;
  helperText?: string;
  rounded?: boolean;
}

// Migration mapping function
export type InputMigrationMapper = (legacy: LegacyInputProps) => {
  baseInput: BaseInputProps;
  formInput?: FormInputProps;
  fieldInput?: FieldInputProps;
};

// Component API documentation
export interface InputAPI {
  BaseInput: {
    props: BaseInputProps;
    events: InputEvents;
    slots: {};
  };
  FormInput: {
    props: FormInputProps;
    events: InputEvents & { validate: ValidationResult };
    slots: {
      label?: {};
      helperText?: {};
      error?: {};
    };
  };
  FieldInput: {
    props: FieldInputProps;
    events: EnhancedInputEvents;
    slots: {
      leftIcon?: {};
      rightIcon?: {};
      label?: {};
      helperText?: {};
      error?: {};
    };
  };
}

// Testing utilities
export interface InputTestUtils {
  simulateInput: (element: HTMLInputElement, value: string) => void;
  simulateKeydown: (element: HTMLInputElement, key: string) => void;
  simulateFocus: (element: HTMLInputElement) => void;
  simulateBlur: (element: HTMLInputElement) => void;
  getValidationErrors: (element: HTMLInputElement) => string[];
}

// Accessibility helpers
export interface InputAccessibility {
  labelId: string;
  errorId: string;
  helperId: string;
  describedBy: string;
  ariaInvalid: boolean;
  ariaRequired: boolean;
}

// Form integration types
export interface FormContext {
  registerField: (name: string, config: InputConfig) => void;
  unregisterField: (name: string) => void;
  validateField: (name: string) => ValidationResult;
  validateForm: () => { isValid: boolean; errors: Record<string, string[]> };
  getFieldValue: (name: string) => string | number;
  setFieldValue: (name: string, value: string | number) => void;
  resetForm: () => void;
  submitForm: () => void;
}

// Error handling
export class InputValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string,
    public readonly rule: ValidationRule,
    public readonly value: string | number
  ) {
    super(`Input validation error for field '${field}': ${message}`);
    this.name = 'InputValidationError';
  }
}

// Performance optimization types
export interface InputPerformanceConfig {
  debounceMs: number;
  throttleMs: number;
  lazy: boolean; // Only validate on blur
  immediate: boolean; // Validate on every keystroke
}

// Internationalization
export interface InputI18n {
  required: string;
  invalid: string;
  tooShort: string;
  tooLong: string;
  invalidEmail: string;
  invalidUrl: string;
  invalidNumber: string;
  clear: string;
  showPassword: string;
  hidePassword: string;
  copy: string;
  paste: string;
}

// Export main types
export type {
  BaseInputProps as default,
  FormInputProps,
  FieldInputProps,
  InputEvents,
  ValidationRule,
  ValidationResult,
  InputState,
  InputConfig
};