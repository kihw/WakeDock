/**
 * TypeScript definitions for UnifiedButton component
 * TASK-UI-001: Unification des Composants Button
 */

import type { HTMLButtonAttributes, HTMLAnchorAttributes } from 'svelte/elements';

// Button variant types
export type ButtonVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost';

// Size types  
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Icon position types
export type IconPosition = 'left' | 'right';

// Base button props interface
export interface BaseButtonProps {
  // Core functionality
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  
  // Icon support
  icon?: string;
  iconPosition?: IconPosition;
  iconOnly?: boolean;
  
  // Layout
  fullWidth?: boolean;
  outlined?: boolean;
  
  // Accessibility
  ariaLabel?: string;
  testId?: string;
  
  // Custom styling
  className?: string;
}

// Button element props (when href is not provided)
export interface ButtonElementProps extends BaseButtonProps {
  type?: 'button' | 'submit' | 'reset';
  href?: never;
  target?: never;
  rel?: never;
}

// Anchor element props (when href is provided) 
export interface AnchorElementProps extends BaseButtonProps {
  type?: never;
  href: string;
  target?: string;
  rel?: string;
}

// Union type for all button props
export type UnifiedButtonProps = ButtonElementProps | AnchorElementProps;

// Event types
export interface ButtonEvents {
  click: MouseEvent;
}

// Component API documentation
export interface ButtonAPI {
  props: UnifiedButtonProps;
  events: ButtonEvents;
  slots: {
    default: {};
  };
}

// Variant configuration type (for design system)
export interface VariantConfig {
  base: string;
  disabled: string;
}

// Size configuration type
export interface SizeConfig {
  regular: string;
  iconOnly: string;
}

// Icon size mapping
export interface IconSizeMapping {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
}

// Design system integration types
export interface ButtonDesignTokens {
  variants: Record<ButtonVariant, VariantConfig>;
  sizes: Record<ButtonSize, SizeConfig>;
  iconSizes: IconSizeMapping;
}

// Migration helper types for backward compatibility
export interface LegacyButtonProps {
  // Old PrimaryButton props
  primarySize?: 'sm' | 'md' | 'lg';
  primaryFullWidth?: boolean;
  
  // Old SecondaryButton props  
  secondarySize?: 'sm' | 'md' | 'lg';
  secondaryFullWidth?: boolean;
  
  // Old IconButton props
  iconVariant?: 'primary' | 'secondary' | 'ghost';
  
  // Old Button wrapper props
  legacyVariant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost';
}

// Migration mapping function type
export type MigrationMapper = (legacy: LegacyButtonProps) => UnifiedButtonProps;

// Component state types
export interface ButtonState {
  isDisabled: boolean;
  isLink: boolean;
  computedClasses: string;
  iconClasses: string;
}

// Testing utilities types
export interface ButtonTestUtils {
  getByVariant: (variant: ButtonVariant) => HTMLElement;
  getBySize: (size: ButtonSize) => HTMLElement;
  getByTestId: (testId: string) => HTMLElement;
  getByRole: (role: string) => HTMLElement;
}

// Storybook configuration types
export interface ButtonStoryArgs extends UnifiedButtonProps {
  slotContent?: string;
  onClickAction?: () => void;
}

export interface ButtonStoryMeta {
  title: string;
  component: any;
  parameters: {
    docs: {
      description: {
        component: string;
      };
    };
  };
  argTypes: Record<string, any>;
}

// Error types for component validation
export class ButtonConfigError extends Error {
  constructor(message: string, public readonly config: Partial<UnifiedButtonProps>) {
    super(`Button configuration error: ${message}`);
    this.name = 'ButtonConfigError';
  }
}

// Validation schema type
export interface ButtonValidationSchema {
  variant: {
    type: 'enum';
    values: ButtonVariant[];
    default: ButtonVariant;
  };
  size: {
    type: 'enum'; 
    values: ButtonSize[];
    default: ButtonSize;
  };
  disabled: {
    type: 'boolean';
    default: boolean;
  };
  loading: {
    type: 'boolean';
    default: boolean;
  };
}

// Component documentation types
export interface ButtonDocumentation {
  overview: string;
  usage: {
    basic: string;
    withIcon: string;
    loading: string;
    asLink: string;
    iconOnly: string;
  };
  accessibility: {
    ariaSupport: string[];
    keyboardNavigation: string[];
    screenReaderSupport: string[];
  };
  examples: {
    code: string;
    description: string;
  }[];
}

export default UnifiedButtonProps;