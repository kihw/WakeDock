/**
 * Component Composition Patterns
 * Advanced patterns for combining design system components
 */

import { variants, colors } from './tokens';

// Pattern 1: Form Layouts
export const formPatterns = {
  // Inline form with consistent spacing
  inline: {
    container: 'flex items-end gap-4',
    field: 'flex-1',
    action: 'flex-shrink-0'
  },
  
  // Stacked form with sections
  stacked: {
    container: 'space-y-6',
    section: 'space-y-4',
    fieldGroup: 'grid grid-cols-1 md:grid-cols-2 gap-4',
    actions: 'flex justify-end gap-3 pt-6 border-t border-secondary-200'
  },
  
  // Card-based form
  card: {
    container: variants.card.elevated + ' p-6 space-y-6',
    header: 'pb-4 border-b border-secondary-200',
    body: 'space-y-4',
    footer: 'pt-4 border-t border-secondary-200 flex justify-between'
  }
};

// Pattern 2: Data Display Layouts
export const dataPatterns = {
  // Master-detail layout
  masterDetail: {
    container: 'grid grid-cols-1 lg:grid-cols-3 gap-6',
    master: 'lg:col-span-1',
    detail: 'lg:col-span-2',
    masterItem: variants.card.base + ' p-4 cursor-pointer hover:' + variants.card.elevated,
    detailCard: variants.card.elevated + ' p-6'
  },
  
  // Dashboard grid
  dashboard: {
    container: 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6',
    widget: variants.card.base + ' p-6',
    widgetHeader: 'flex items-center justify-between mb-4',
    widgetTitle: 'text-lg font-semibold text-secondary-900',
    widgetValue: 'text-3xl font-bold text-primary-600'
  },
  
  // List with actions
  actionList: {
    container: variants.card.base + ' divide-y divide-secondary-200',
    item: 'flex items-center justify-between p-4 hover:bg-secondary-50',
    content: 'flex-1 min-w-0',
    actions: 'flex items-center gap-2 ml-4'
  }
};

// Pattern 3: Navigation Patterns
export const navigationPatterns = {
  // Sidebar navigation
  sidebar: {
    container: 'w-64 bg-secondary-800 text-white h-full',
    header: 'p-6 border-b border-secondary-700',
    nav: 'p-4 space-y-2',
    item: 'flex items-center gap-3 px-3 py-2 rounded-md hover:bg-secondary-700',
    activeItem: 'flex items-center gap-3 px-3 py-2 rounded-md bg-primary-600 text-white'
  },
  
  // Tab navigation
  tabs: {
    container: 'border-b border-secondary-200',
    list: 'flex space-x-8',
    tab: 'py-2 px-1 border-b-2 border-transparent text-secondary-500 hover:text-secondary-700',
    activeTab: 'py-2 px-1 border-b-2 border-primary-500 text-primary-600 font-medium'
  },
  
  // Breadcrumb navigation
  breadcrumb: {
    container: 'flex items-center space-x-2 text-sm',
    item: 'text-secondary-500 hover:text-secondary-700',
    separator: 'text-secondary-400',
    current: 'text-secondary-900 font-medium'
  }
};

// Pattern 4: Modal and Overlay Patterns
export const overlayPatterns = {
  // Confirmation modal
  confirmation: {
    backdrop: variants.modal.backdrop,
    container: variants.modal.container + ' max-w-md',
    header: 'flex items-center gap-3 p-6 ' + variants.modal.header,
    icon: 'w-12 h-12 rounded-full flex items-center justify-center',
    dangerIcon: 'bg-error-100 text-error-600',
    warningIcon: 'bg-warning-100 text-warning-600',
    infoIcon: 'bg-primary-100 text-primary-600',
    body: 'p-6 space-y-4',
    footer: 'p-6 ' + variants.modal.footer + ' flex justify-end gap-3'
  },
  
  // Drawer overlay
  drawer: {
    backdrop: variants.modal.backdrop,
    container: 'fixed inset-y-0 right-0 w-96 bg-white shadow-xl transform transition-transform',
    header: 'p-6 ' + variants.modal.header + ' flex items-center justify-between',
    body: 'flex-1 overflow-y-auto p-6',
    footer: 'p-6 ' + variants.modal.footer
  },
  
  // Notification toast
  toast: {
    container: 'fixed top-4 right-4 z-50 space-y-2',
    item: 'flex items-center gap-3 p-4 rounded-lg shadow-lg max-w-sm',
    success: variants.toast.success,
    error: variants.toast.error,
    warning: variants.toast.warning,
    info: variants.toast.info
  }
};

// Pattern 5: Content Layouts
export const contentPatterns = {
  // Article layout
  article: {
    container: 'max-w-4xl mx-auto px-6 py-8',
    header: 'mb-8 pb-8 border-b border-secondary-200',
    title: 'text-3xl font-bold text-secondary-900 mb-4',
    meta: 'text-secondary-600 text-sm',
    content: 'prose prose-secondary max-w-none',
    sidebar: 'lg:col-span-1 space-y-6'
  },
  
  // Gallery layout
  gallery: {
    container: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
    item: variants.card.base + ' overflow-hidden hover:' + variants.card.elevated + ' transition-shadow',
    image: 'w-full h-48 object-cover',
    content: 'p-4',
    title: 'font-medium text-secondary-900 mb-2',
    description: 'text-sm text-secondary-600'
  },
  
  // Split layout
  split: {
    container: 'grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-screen',
    left: 'flex flex-col justify-center p-8',
    right: 'bg-secondary-50 flex items-center justify-center p-8',
    content: 'max-w-md mx-auto w-full'
  }
};

// Utility functions for applying patterns
export function applyPattern(pattern: Record<string, string>, element: string): string {
  return pattern[element] || '';
}

export function combinePatterns(...patterns: string[]): string {
  return patterns.filter(Boolean).join(' ');
}

// Advanced composition helpers
export const compositionHelpers = {
  // Responsive spacing
  responsiveSpacing: {
    xs: 'space-y-2 md:space-y-3',
    sm: 'space-y-3 md:space-y-4',
    md: 'space-y-4 md:space-y-6',
    lg: 'space-y-6 md:space-y-8',
    xl: 'space-y-8 md:space-y-12'
  },
  
  // Responsive grids
  responsiveGrid: {
    auto: 'grid grid-cols-1 md:grid-cols-auto gap-4 md:gap-6',
    two: 'grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6',
    three: 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6',
    four: 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-6'
  },
  
  // Focus management
  focusRing: 'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
  
  // Interaction states
  interactive: 'transition-colors duration-200 cursor-pointer hover:bg-secondary-50 focus:bg-secondary-50',
  
  // Disabled states
  disabled: 'opacity-50 cursor-not-allowed pointer-events-none'
};

// Export all patterns
export const patterns = {
  form: formPatterns,
  data: dataPatterns,
  navigation: navigationPatterns,
  overlay: overlayPatterns,
  content: contentPatterns,
  helpers: compositionHelpers
};

export default patterns;