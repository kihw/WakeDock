// WakeDock Design System - Main Export
// Atomic Design System components for consistent UI across the application

// Atomic Components
export * from './atoms';

// Molecular Components  
export * from './molecules';

// Design System Tokens
export { default as tokens } from '../../design-system/tokens';

// Utility types for component props
export interface ComponentVariant {
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

export interface ComponentSize {
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

export interface ComponentState {
    loading?: boolean;
    disabled?: boolean;
    readonly?: boolean;
}

export interface ComponentAccessibility {
    ariaLabel?: string;
    ariaDescribedBy?: string;
    testId?: string;
}

// Common component props interface
export interface BaseComponentProps extends ComponentVariant, ComponentSize, ComponentState, ComponentAccessibility {
    id?: string;
    className?: string;
    style?: string;
}

// Form component props
export interface FormComponentProps extends BaseComponentProps {
    name?: string;
    required?: boolean;
    placeholder?: string;
    value?: string | number;
    fullWidth?: boolean;
}

// Interactive component props
export interface InteractiveComponentProps extends BaseComponentProps {
    href?: string;
    target?: string;
    clickable?: boolean;
    focusable?: boolean;
}
