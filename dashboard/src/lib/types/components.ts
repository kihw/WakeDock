/**
 * Component Type Definitions
 * Type definitions for UI components and their props
 */

import type { SvelteComponent } from 'svelte';

// Common component props
export interface BaseComponentProps {
  class?: string;
  id?: string;
  disabled?: boolean;
}

// Button component
export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'success' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  type?: 'button' | 'submit' | 'reset';
  loading?: boolean;
  icon?: string;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  outlined?: boolean;
}

// Input component
export interface InputProps extends BaseComponentProps {
  type?:
    | 'text'
    | 'email'
    | 'password'
    | 'number'
    | 'url'
    | 'tel'
    | 'search'
    | 'date'
    | 'time'
    | 'datetime-local'
    | 'color';
  value?: string | number;
  placeholder?: string;
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  readonly?: boolean;
  autocomplete?: string;
  min?: number | string;
  max?: number | string;
  step?: number | string;
  pattern?: string;
  maxlength?: number;
  minlength?: number;
  size?: 'sm' | 'md' | 'lg';
  icon?: string;
  iconPosition?: 'left' | 'right';
}

// Select component
export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  group?: string;
}

export interface SelectProps extends BaseComponentProps {
  value?: string | number;
  options: SelectOption[];
  placeholder?: string;
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  multiple?: boolean;
  searchable?: boolean;
  clearable?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Textarea component
export interface TextareaProps extends BaseComponentProps {
  value?: string;
  placeholder?: string;
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  readonly?: boolean;
  rows?: number;
  cols?: number;
  resize?: 'none' | 'both' | 'horizontal' | 'vertical';
  maxlength?: number;
  minlength?: number;
}

// Modal component
export interface ModalProps extends BaseComponentProps {
  isOpen?: boolean;
  title?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnClickOutside?: boolean;
  closeOnEscape?: boolean;
  persistent?: boolean;
  centered?: boolean;
}

// Table component
export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  format?: (value: any) => string;
  render?: (value: any, row: any) => any;
}

export interface TableProps extends BaseComponentProps {
  data: any[];
  columns: TableColumn[];
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  searchable?: boolean;
  filterable?: boolean;
  paginated?: boolean;
  pageSize?: number;
  currentPage?: number;
  loading?: boolean;
  empty?: string;
  selectable?: boolean;
  selectedRows?: any[];
}

// Icon component
export interface IconProps extends BaseComponentProps {
  name: string;
  size?: number | string;
  color?: string;
  stroke?: number;
}

// Chart component
export interface ChartDataPoint {
  x: string | number | Date;
  y: number;
  label?: string;
  color?: string;
}

export interface ChartProps extends BaseComponentProps {
  data: ChartDataPoint[];
  type?: 'line' | 'bar' | 'area' | 'pie' | 'doughnut';
  width?: number | string;
  height?: number | string;
  responsive?: boolean;
  animated?: boolean;
  colors?: string[];
  legend?: boolean;
  tooltip?: boolean;
  grid?: boolean;
  axes?: {
    x?: {
      label?: string;
      format?: (value: any) => string;
    };
    y?: {
      label?: string;
      format?: (value: any) => string;
    };
  };
}

// Badge component
export interface BadgeProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  rounded?: boolean;
  outline?: boolean;
  dot?: boolean;
  pulse?: boolean;
}

// Alert component
export interface AlertProps extends BaseComponentProps {
  variant?: 'success' | 'warning' | 'danger' | 'info';
  title?: string;
  dismissible?: boolean;
  icon?: string;
  actions?: Array<{
    label: string;
    action: () => void;
    variant?: ButtonProps['variant'];
  }>;
}

// Progress component
export interface ProgressProps extends BaseComponentProps {
  value: number;
  max?: number;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  color?: string;
  showLabel?: boolean;
  animated?: boolean;
  striped?: boolean;
}

// Spinner component
export interface SpinnerProps extends BaseComponentProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: string;
  thickness?: number;
}

// Dropdown component
export interface DropdownItem {
  label: string;
  value?: any;
  icon?: string;
  disabled?: boolean;
  separator?: boolean;
  action?: () => void;
  href?: string;
  target?: string;
}

export interface DropdownProps extends BaseComponentProps {
  items: DropdownItem[];
  trigger?: 'click' | 'hover';
  position?: 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right';
  closeOnClick?: boolean;
  offset?: number;
}

// Tabs component
export interface Tab {
  id: string;
  label: string;
  icon?: string;
  disabled?: boolean;
  badge?: string | number;
}

export interface TabsProps extends BaseComponentProps {
  tabs: Tab[];
  activeTab?: string;
  variant?: 'default' | 'pills' | 'underline';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

// Accordion component
export interface AccordionItem {
  id: string;
  title: string;
  content: any;
  disabled?: boolean;
  icon?: string;
}

export interface AccordionProps extends BaseComponentProps {
  items: AccordionItem[];
  multiple?: boolean;
  defaultOpen?: string[];
}

// Tooltip component
export interface TooltipProps extends BaseComponentProps {
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: 'hover' | 'click' | 'focus';
  delay?: number;
  offset?: number;
}

// Breadcrumb component
export interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
  icon?: string;
}

export interface BreadcrumbProps extends BaseComponentProps {
  items: BreadcrumbItem[];
  separator?: string;
  maxItems?: number;
}

// Pagination component
export interface PaginationProps extends BaseComponentProps {
  currentPage: number;
  totalPages: number;
  pageSize?: number;
  totalItems?: number;
  showInfo?: boolean;
  showFirstLast?: boolean;
  showPrevNext?: boolean;
  maxVisiblePages?: number;
}

// Navigation component
export interface NavItem {
  id: string;
  label: string;
  href?: string;
  icon?: string;
  badge?: string | number;
  active?: boolean;
  disabled?: boolean;
  children?: NavItem[];
}

export interface NavigationProps extends BaseComponentProps {
  items: NavItem[];
  orientation?: 'horizontal' | 'vertical';
  variant?: 'default' | 'pills' | 'sidebar';
  collapsible?: boolean;
  collapsed?: boolean;
}

// Card component
export interface CardProps extends BaseComponentProps {
  variant?: 'default' | 'outlined' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  clickable?: boolean;
}

// Form component types
export interface FormField {
  name: string;
  type:
    | 'text'
    | 'email'
    | 'password'
    | 'number'
    | 'select'
    | 'textarea'
    | 'checkbox'
    | 'radio'
    | 'date'
    | 'file';
  label?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  options?: SelectOption[];
  validation?: {
    pattern?: string;
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
    custom?: (value: any) => string | null;
  };
  hint?: string;
  grid?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

export interface FormProps extends BaseComponentProps {
  fields: FormField[];
  values?: Record<string, any>;
  errors?: Record<string, string>;
  loading?: boolean;
  submitLabel?: string;
  cancelLabel?: string;
  showCancel?: boolean;
  layout?: 'vertical' | 'horizontal' | 'inline';
}

// Layout component types
export interface LayoutProps extends BaseComponentProps {
  sidebar?: boolean;
  header?: boolean;
  footer?: boolean;
  fluid?: boolean;
}

export interface SidebarProps extends BaseComponentProps {
  collapsed?: boolean;
  collapsible?: boolean;
  position?: 'left' | 'right';
  width?: string;
  variant?: 'default' | 'compact' | 'overlay';
}

export interface HeaderProps extends BaseComponentProps {
  fixed?: boolean;
  transparent?: boolean;
  height?: string;
  variant?: 'default' | 'compact';
}

// Theme types
export interface ThemeColors {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  danger: string;
  info: string;
  light: string;
  dark: string;
  muted: string;
}

export interface ThemeConfig {
  colors: ThemeColors;
  fonts: {
    sans: string;
    mono: string;
  };
  spacing: Record<string, string>;
  borderRadius: Record<string, string>;
  shadows: Record<string, string>;
  transitions: Record<string, string>;
}

// Event types
export interface ComponentEvent<T = any> {
  detail: T;
  preventDefault?: () => void;
  stopPropagation?: () => void;
}

export interface ClickEvent extends ComponentEvent {
  detail: MouseEvent;
}

export interface ChangeEvent<T = any> extends ComponentEvent {
  detail: {
    value: T;
    name?: string;
  };
}

export interface SelectEvent<T = any> extends ComponentEvent {
  detail: {
    value: T;
    option: SelectOption;
  };
}

export interface FormSubmitEvent extends ComponentEvent {
  detail: {
    values: Record<string, any>;
    isValid: boolean;
  };
}

// Validation types
export interface ValidationRule {
  required?: boolean;
  pattern?: RegExp;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  custom?: (value: any) => string | null;
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

// Animation types
export interface AnimationConfig {
  duration?: number;
  easing?: string;
  delay?: number;
  direction?: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
  fillMode?: 'none' | 'forwards' | 'backwards' | 'both';
  iterationCount?: number | 'infinite';
}

// Responsive types
export interface Breakpoints {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  '2xl': number;
}

export interface ResponsiveValue<T> {
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
}

// Component state types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
  code?: string;
}

export interface DataState<T> {
  data: T | null;
  loading: LoadingState;
  error: ErrorState;
}

// Generic component types
export type ComponentSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type ComponentVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info';
export type ComponentColor = string | ComponentVariant;
export type ComponentPosition = 'top' | 'bottom' | 'left' | 'right';
export type ComponentAlignment = 'left' | 'center' | 'right' | 'justify';

// Utility types
export type WithRequired<T, K extends keyof T> = T & { [P in K]-?: T[P] };
export type WithOptional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type ComponentRef<T extends SvelteComponent> = T;

// Export all component prop types
export type AllComponentProps =
  | ButtonProps
  | InputProps
  | SelectProps
  | TextareaProps
  | ModalProps
  | TableProps
  | IconProps
  | ChartProps
  | BadgeProps
  | AlertProps
  | ProgressProps
  | SpinnerProps
  | DropdownProps
  | TabsProps
  | AccordionProps
  | TooltipProps
  | BreadcrumbProps
  | PaginationProps
  | NavigationProps
  | CardProps
  | FormProps
  | LayoutProps
  | SidebarProps
  | HeaderProps;
