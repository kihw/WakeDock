/**
 * Storybook stories for refactored Input system
 * TASK-UI-002: Refactorisation du Système d'Input
 */

import type { Meta, StoryObj } from '@storybook/svelte';
import BaseInput from './BaseInput.svelte';
import FormInput from '../molecules/FormInput.svelte';
import FieldInput from '../molecules/FieldInput.svelte';

// BaseInput Stories
const baseInputMeta: Meta<BaseInput> = {
  title: 'UI/Atoms/BaseInput',
  component: BaseInput,
  parameters: {
    docs: {
      description: {
        component: `
# BaseInput Component

The atomic foundation of the refactored input system. BaseInput handles only the essential input functionality without any decorative elements or complex validation logic.

## Key Features

- **Atomic Design Compliant**: <150 lines, single responsibility
- **Design Token Integration**: Consistent styling across the application
- **Full Type Support**: All HTML input types supported
- **Accessibility First**: WCAG 2.1 AA compliant
- **Performance Optimized**: Minimal overhead, efficient rendering

## Design Principles

### Responsibilities (✅ What it DOES):
- Render basic input element
- Apply design tokens consistently
- Handle input events and validation
- Provide accessibility attributes
- Support all HTML input types

### Non-Responsibilities (❌ What it does NOT do):
- Labels, help text, or error messages → Use FormInput
- Icons or decorative elements → Use FieldInput  
- Complex validation logic → Use FormInput
- Loading states or clear buttons → Use FieldInput

## Migration from Legacy Input.svelte

The old Input.svelte (722 lines) violated atomic design principles. This refactoring splits functionality:

### Before (Legacy - 722 lines):
\`\`\`svelte
<Input 
  label="Username"
  leftIcon="user"
  clearable
  error="Required field"
  helperText="Enter your username"
/>
\`\`\`

### After (Atomic - <150 lines each):
\`\`\`svelte
<!-- For basic inputs -->
<BaseInput type="text" placeholder="Username" />

<!-- For form inputs with validation -->
<FormInput label="Username" error="Required field" />

<!-- For enhanced inputs with icons -->
<FieldInput label="Username" leftIcon="user" clearable />
\`\`\`
        `
      }
    },
    layout: 'centered'
  },
  argTypes: {
    type: {
      control: { type: 'select' },
      options: ['text', 'email', 'password', 'number', 'tel', 'url', 'search', 'date', 'time', 'color', 'file'],
      description: 'HTML input type'
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
      description: 'Input size variant'
    },
    variant: {
      control: { type: 'select' },
      options: ['default', 'success', 'warning', 'error'],
      description: 'Visual state variant'
    },
    value: {
      control: { type: 'text' },
      description: 'Input value'
    },
    placeholder: {
      control: { type: 'text' },
      description: 'Placeholder text'
    },
    disabled: {
      control: { type: 'boolean' },
      description: 'Disable the input'
    },
    readonly: {
      control: { type: 'boolean' },
      description: 'Make input readonly'
    },
    required: {
      control: { type: 'boolean' },
      description: 'Mark input as required'
    },
    fullWidth: {
      control: { type: 'boolean' },
      description: 'Make input full width'
    }
  },
  args: {
    type: 'text',
    size: 'md',
    variant: 'default',
    placeholder: 'Enter text...',
    disabled: false,
    readonly: false,
    required: false,
    fullWidth: true
  }
};

export default baseInputMeta;
type BaseStory = StoryObj<typeof baseInputMeta>;

// Basic BaseInput examples
export const Default: BaseStory = {
  args: {},
};

export const WithValue: BaseStory = {
  args: {
    value: 'Sample text'
  }
};

export const Placeholder: BaseStory = {
  args: {
    placeholder: 'Type something...'
  }
};

// Input types showcase
export const InputTypes: BaseStory = {
  render: () => ({
    Component: BaseInput,
    template: `
      <div class="grid grid-cols-2 gap-4 w-full max-w-2xl">
        <BaseInput type="text" placeholder="Text input" />
        <BaseInput type="email" placeholder="Email input" />
        <BaseInput type="password" placeholder="Password input" />
        <BaseInput type="number" placeholder="Number input" />
        <BaseInput type="tel" placeholder="Phone number" />
        <BaseInput type="url" placeholder="Website URL" />
        <BaseInput type="search" placeholder="Search..." />
        <BaseInput type="date" />
      </div>
    `
  })
};

// Size variants
export const Sizes: BaseStory = {
  render: () => ({
    Component: BaseInput,
    template: `
      <div class="flex flex-col gap-4 w-full max-w-md">
        <BaseInput size="sm" placeholder="Small input" />
        <BaseInput size="md" placeholder="Medium input" />
        <BaseInput size="lg" placeholder="Large input" />
      </div>
    `
  })
};

// State variants
export const Variants: BaseStory = {
  render: () => ({
    Component: BaseInput,
    template: `
      <div class="flex flex-col gap-4 w-full max-w-md">
        <BaseInput variant="default" placeholder="Default state" />
        <BaseInput variant="success" placeholder="Success state" value="Valid input" />
        <BaseInput variant="warning" placeholder="Warning state" value="Check this" />
        <BaseInput variant="error" placeholder="Error state" value="Invalid input" />
      </div>
    `
  })
};

// States showcase
export const States: BaseStory = {
  render: () => ({
    Component: BaseInput,
    template: `
      <div class="flex flex-col gap-4 w-full max-w-md">
        <BaseInput placeholder="Normal state" />
        <BaseInput disabled placeholder="Disabled state" />
        <BaseInput readonly value="Readonly state" />
        <BaseInput required placeholder="Required field" />
      </div>
    `
  })
};

// FormInput Stories
const formInputMeta: Meta<FormInput> = {
  title: 'UI/Molecules/FormInput',
  component: FormInput,
  parameters: {
    docs: {
      description: {
        component: `
# FormInput Component

Molecular component that wraps BaseInput with form-specific functionality like labels, validation, and help text.

## Features

- **Built on BaseInput**: Inherits all atomic functionality
- **Form Integration**: Labels, validation, error handling
- **Validation Rules**: Built-in validation with custom rules
- **State Management**: Tracks dirty, touched, valid states
- **Accessibility**: Proper ARIA labeling and error association

## When to Use

- Forms that need validation
- Inputs that require labels or help text
- When you need form state management
- Accessibility-compliant form fields

Use FieldInput instead when you need icons, clear buttons, or loading states.
        `
      }
    }
  },
  args: {
    label: 'Username',
    placeholder: 'Enter your username',
    helperText: 'Must be at least 3 characters',
    fullWidth: true
  }
};

type FormStory = StoryObj<typeof formInputMeta>;

export const FormInputDefault: FormStory = {
  args: {}
};

export const FormInputWithValidation: FormStory = {
  args: {
    label: 'Email Address',
    type: 'email',
    required: true,
    validationRules: [
      { type: 'required' },
      { type: 'email' }
    ],
    validateOnInput: true
  }
};

export const FormInputWithError: FormStory = {
  args: {
    label: 'Password',
    type: 'password',
    error: 'Password must be at least 8 characters',
    value: '123'
  }
};

export const FormInputSuccess: FormStory = {
  args: {
    label: 'Username',
    success: 'Username is available!',
    value: 'john_doe'
  }
};

// FieldInput Stories
const fieldInputMeta: Meta<FieldInput> = {
  title: 'UI/Molecules/FieldInput',
  component: FieldInput,
  parameters: {
    docs: {
      description: {
        component: `
# FieldInput Component

Full-featured input component with all enhancements: icons, clear buttons, password toggles, loading states, and more.

## Features

- **All FormInput functionality**: Validation, labels, errors
- **Icon Support**: Left and right icon positioning
- **Interactive Elements**: Clear button, password toggle
- **Loading States**: Built-in spinner for async operations
- **Copy/Paste Actions**: Built-in clipboard integration
- **Debounced Events**: Configurable input debouncing

## When to Use

- Rich input experiences with icons
- Password fields with visibility toggle
- Search inputs with clear functionality
- Forms with loading states
- Any input needing enhanced UX
        `
      }
    }
  },
  args: {
    label: 'Search',
    placeholder: 'Search products...',
    leftIcon: 'search',
    clearable: true,
    fullWidth: true
  }
};

type FieldStory = StoryObj<typeof fieldInputMeta>;

export const FieldInputDefault: FieldStory = {
  args: {}
};

export const FieldInputWithIcons: FieldStory = {
  render: () => ({
    Component: FieldInput,
    template: `
      <div class="flex flex-col gap-4 w-full max-w-md">
        <FieldInput label="Email" type="email" leftIcon="email" placeholder="Enter email" />
        <FieldInput label="Phone" type="tel" leftIcon="phone" placeholder="Enter phone" />
        <FieldInput label="Website" type="url" leftIcon="url" placeholder="Enter URL" />
        <FieldInput label="Search" leftIcon="search" rightIcon="search" placeholder="Search..." />
      </div>
    `
  })
};

export const FieldInputPassword: FieldStory = {
  args: {
    label: 'Password',
    type: 'password',
    showPasswordToggle: true,
    leftIcon: 'password',
    placeholder: 'Enter password'
  }
};

export const FieldInputWithActions: FieldStory = {
  render: () => ({
    Component: FieldInput,
    template: `
      <div class="flex flex-col gap-4 w-full max-w-md">
        <FieldInput 
          label="API Key" 
          value="sk-1234567890abcdef"
          readonly
          copyable
          helperText="Click the copy button to copy to clipboard"
        />
        <FieldInput 
          label="Search" 
          leftIcon="search"
          clearable
          placeholder="Type to search..."
        />
        <FieldInput 
          label="Loading Example" 
          loading
          placeholder="Processing..."
          disabled
        />
      </div>
    `
  })
};

// Comparison showcase
export const ComponentComparison: BaseStory = {
  parameters: {
    docs: {
      description: {
        story: `
This story demonstrates the three-tier architecture of the refactored input system:

1. **BaseInput** (Atomic): Minimal, essential functionality only
2. **FormInput** (Molecular): Adds validation, labels, form integration  
3. **FieldInput** (Enhanced): Full-featured with icons, actions, loading states

Each builds upon the previous while maintaining clear separation of concerns.
        `
      }
    }
  },
  render: () => ({
    Component: BaseInput,
    template: `
      <div class="flex flex-col gap-8 w-full max-w-2xl">
        
        <section>
          <h3 class="text-lg font-semibold mb-4">1. BaseInput (Atomic)</h3>
          <p class="text-sm text-gray-600 mb-4">Essential input functionality only</p>
          <BaseInput placeholder="Just a basic input" />
        </section>

        <section>
          <h3 class="text-lg font-semibold mb-4">2. FormInput (Molecular)</h3>
          <p class="text-sm text-gray-600 mb-4">Adds validation, labels, and form integration</p>
          <FormInput 
            label="Email Address"
            type="email"
            helperText="We'll never share your email"
            required
            placeholder="Enter your email"
          />
        </section>

        <section>
          <h3 class="text-lg font-semibold mb-4">3. FieldInput (Enhanced)</h3>
          <p class="text-sm text-gray-600 mb-4">Full-featured with icons and interactions</p>
          <FieldInput 
            label="Password"
            type="password"
            leftIcon="password"
            showPasswordToggle
            clearable
            helperText="Must be at least 8 characters"
            placeholder="Enter your password"
          />
        </section>

      </div>
    `
  })
};

// Performance showcase
export const PerformanceShowcase: BaseStory = {
  parameters: {
    docs: {
      description: {
        story: `
This story demonstrates the performance benefits of the refactored input system:

- **Reduced Bundle Size**: 722 lines → <150 lines per component
- **Modular Loading**: Only load features you need
- **Efficient Rendering**: Atomic components render faster
- **Better Tree Shaking**: Unused features don't affect bundle size
        `
      }
    }
  },
  render: () => ({
    Component: BaseInput,
    template: `
      <div class="grid grid-cols-4 gap-2">
        {#each Array(20) as _, i}
          <BaseInput 
            placeholder="Input {i + 1}"
            size={['sm', 'md', 'lg'][i % 3]}
            variant={['default', 'success', 'warning', 'error'][i % 4]}
          />
        {/each}
      </div>
    `
  })
};

// Accessibility showcase
export const AccessibilityShowcase: BaseStory = {
  parameters: {
    docs: {
      description: {
        story: `
This story demonstrates the accessibility features of the refactored input system:

- **ARIA Labels**: Proper labeling for screen readers
- **Error Association**: Errors properly linked to inputs
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Management**: Proper focus indicators and flow
- **Screen Reader Support**: Comprehensive screen reader compatibility
        `
      }
    }
  },
  render: () => ({
    Component: BaseInput,
    template: `
      <div class="flex flex-col gap-4 w-full max-w-md">
        <FormInput 
          label="Full Name"
          required
          ariaLabel="Enter your full legal name"
          helperText="First and last name required"
        />
        <FormInput 
          label="Email"
          type="email"
          error="Please enter a valid email address"
          value="invalid-email"
        />
        <FieldInput 
          label="Password"
          type="password"
          showPasswordToggle
          ariaLabel="Create a secure password"
          helperText="Password will be hidden by default"
        />
      </div>
    `
  })
};

// Export meta objects for multi-component story
export { formInputMeta as FormInputMeta, fieldInputMeta as FieldInputMeta };