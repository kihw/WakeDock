# WakeDock Design System Style Guide

## Overview

The WakeDock Design System is a comprehensive collection of atomic and molecular components built with Svelte, TypeScript, and Tailwind CSS. It provides a consistent, accessible, and scalable foundation for building user interfaces across the WakeDock application.

## Design Principles

### 1. Atomic Design Methodology
- **Atoms**: Basic building blocks (Button, Input, Badge, etc.)
- **Molecules**: Combinations of atoms (SearchInput, FormField, etc.)
- **Organisms**: Complex components built from molecules and atoms
- **Templates**: Page-level structures
- **Pages**: Specific instances of templates

### 2. Accessibility First
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatibility
- High contrast support
- Focus management

### 3. Consistency
- Unified design tokens
- Consistent spacing and typography
- Standardized color palette
- Coherent interaction patterns

### 4. Scalability
- Modular architecture
- Reusable components
- Extensible design system
- Performance optimized

## Design Tokens

### Colors

#### Primary Colors
- **Primary 500**: `#3b82f6` - Main brand color
- **Primary 600**: `#2563eb` - Hover states
- **Primary 700**: `#1d4ed8` - Active states

#### Semantic Colors
- **Success**: `#10b981` - Positive actions, success states
- **Warning**: `#f59e0b` - Caution, warnings
- **Error**: `#ef4444` - Errors, destructive actions
- **Info**: `#3b82f6` - Information, neutral states

#### Neutral Colors
- **Gray 50**: `#f9fafb` - Background
- **Gray 100**: `#f3f4f6` - Light background
- **Gray 500**: `#6b7280` - Text secondary
- **Gray 900**: `#111827` - Text primary

### Typography

#### Font Family
- **Primary**: Inter, system-ui, sans-serif
- **Monospace**: 'Fira Code', 'Courier New', monospace

#### Font Sizes
- **xs**: 0.75rem (12px)
- **sm**: 0.875rem (14px)
- **base**: 1rem (16px)
- **lg**: 1.125rem (18px)
- **xl**: 1.25rem (20px)
- **2xl**: 1.5rem (24px)
- **3xl**: 1.875rem (30px)

#### Font Weights
- **Normal**: 400
- **Medium**: 500
- **Semibold**: 600
- **Bold**: 700

### Spacing

#### Scale
- **0.5**: 0.125rem (2px)
- **1**: 0.25rem (4px)
- **2**: 0.5rem (8px)
- **3**: 0.75rem (12px)
- **4**: 1rem (16px)
- **6**: 1.5rem (24px)
- **8**: 2rem (32px)
- **12**: 3rem (48px)

### Border Radius
- **sm**: 0.125rem (2px)
- **default**: 0.25rem (4px)
- **md**: 0.375rem (6px)
- **lg**: 0.5rem (8px)
- **xl**: 0.75rem (12px)
- **full**: 9999px

### Shadows
- **sm**: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
- **default**: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
- **md**: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
- **lg**: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)

## Component Library

### Atomic Components

#### Button
Versatile button component with multiple variants and states.

**Variants:**
- `primary` - Main call-to-action
- `secondary` - Secondary actions
- `success` - Positive actions
- `warning` - Caution actions
- `error` - Destructive actions
- `ghost` - Minimal styling

**Sizes:**
- `sm` - Small button
- `md` - Medium button (default)
- `lg` - Large button
- `xl` - Extra large button

**States:**
- `disabled` - Non-interactive state
- `loading` - Loading state with spinner
- `active` - Active/pressed state

#### Input
Flexible input component with validation and accessibility features.

**Types:**
- `text` - Text input
- `email` - Email input
- `password` - Password input
- `number` - Number input
- `tel` - Telephone input
- `url` - URL input
- `search` - Search input

**Variants:**
- `default` - Standard input
- `success` - Success state
- `warning` - Warning state
- `error` - Error state

**Features:**
- Label support
- Helper text
- Error messages
- Icon support
- Clearable
- Password toggle

#### Badge
Small status indicators and labels.

**Variants:**
- `success` - Green badge
- `warning` - Yellow badge
- `error` - Red badge
- `info` - Blue badge
- `neutral` - Gray badge

**Sizes:**
- `sm` - Small badge
- `md` - Medium badge
- `lg` - Large badge

#### Card
Container component for grouping related content.

**Variants:**
- `default` - Standard card
- `elevated` - Card with shadow
- `outlined` - Card with border

**Features:**
- Padding options
- Hover effects
- Click handlers
- Accessibility support

#### LoadingSpinner
Animated loading indicator.

**Sizes:**
- `sm` - Small spinner
- `md` - Medium spinner
- `lg` - Large spinner

**Variants:**
- `default` - Standard spinner
- `primary` - Primary color spinner
- `secondary` - Secondary color spinner

#### Toast
Notification component for user feedback.

**Variants:**
- `success` - Success notifications
- `warning` - Warning notifications
- `error` - Error notifications
- `info` - Info notifications

**Features:**
- Auto-dismiss
- Manual dismiss
- Actions support
- Position control

#### Avatar
User profile image or initials display.

**Sizes:**
- `sm` - Small avatar
- `md` - Medium avatar
- `lg` - Large avatar
- `xl` - Extra large avatar

**Types:**
- Image avatar
- Initials avatar
- Icon avatar

### Molecular Components

#### SearchInput
Enhanced search input with debouncing and clear functionality.

**Features:**
- Debounced search
- Clear button
- Loading state
- Search suggestions
- Keyboard navigation

#### FormField
Complete form field with label, input, and validation.

**Features:**
- Label support
- Required indicators
- Error handling
- Helper text
- Validation states

#### DataTable
Advanced table component with sorting, filtering, and pagination.

**Features:**
- Column sorting
- Search/filter
- Pagination
- Row selection
- Custom cell renderers
- Loading states
- Empty states

## Theme System

### Dark Mode Support
The design system includes comprehensive dark mode support with:
- System preference detection
- Manual theme toggle
- Persistent theme storage
- Smooth transitions
- Consistent dark variants

### Theme Usage
```typescript
import { theme } from '$lib/utils/theme';

// Toggle theme
theme.toggle();

// Set specific theme
theme.setTheme('dark');

// Initialize theme
theme.init();
```

## Animation System

### Principles
- Subtle and purposeful
- Consistent timing
- Reduced motion support
- Performance optimized

### Animation Presets
- **Fade**: Smooth opacity transitions
- **Slide**: Directional movement
- **Scale**: Size transitions
- **Bounce**: Elastic effects
- **Spring**: Natural motion

### Usage
```typescript
import { ANIMATIONS } from '$lib/utils/animations';

// Use in Svelte transitions
<div transition:fade={ANIMATIONS.fadeIn}>
  Content
</div>
```

## Best Practices

### Component Usage
1. Always use semantic HTML elements
2. Provide proper ARIA labels
3. Include focus management
4. Test with keyboard navigation
5. Verify screen reader compatibility

### Styling
1. Use design tokens instead of hard-coded values
2. Maintain consistent spacing
3. Follow color contrast guidelines
4. Use semantic color names
5. Implement proper focus indicators

### Performance
1. Lazy load components when possible
2. Use proper key props for lists
3. Minimize re-renders
4. Optimize images and assets
5. Use CSS-in-JS sparingly

### Accessibility
1. Provide alternative text for images
2. Use proper heading hierarchy
3. Ensure keyboard navigation
4. Maintain color contrast ratios
5. Test with assistive technologies

## Testing Strategy

### Unit Tests
- Component rendering
- Prop validation
- Event handling
- State management
- Accessibility features

### Integration Tests
- Component interactions
- Form submissions
- Navigation flows
- Theme switching
- Responsive behavior

### Visual Tests
- Component screenshots
- Cross-browser compatibility
- Dark mode rendering
- Responsive layouts
- Animation states

## Browser Support

### Supported Browsers
- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

### Features
- CSS Custom Properties
- CSS Grid and Flexbox
- ES2020+ JavaScript
- Web Components
- Service Workers

## Contributing

### Adding New Components
1. Create component in appropriate folder
2. Add TypeScript interfaces
3. Include accessibility features
4. Write unit tests
5. Add Storybook documentation
6. Update style guide

### Modifying Existing Components
1. Maintain backward compatibility
2. Update tests
3. Review accessibility impact
4. Update documentation
5. Test across supported browsers

## Resources

### External Links
- [Svelte Documentation](https://svelte.dev/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Atomic Design Methodology](https://bradfrost.com/blog/post/atomic-web-design/)

### Internal Resources
- Component API Documentation
- Design Token Reference
- Animation Library
- Theme System Guide
- Accessibility Checklist
