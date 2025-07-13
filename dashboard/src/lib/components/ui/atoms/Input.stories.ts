import type { Meta, StoryObj } from '@storybook/svelte';
import Input from '../atoms/Input.svelte';

const meta: Meta<Input> = {
  title: 'Design System/Atoms/Input',
  component: Input,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A flexible input component supporting various types, validation states, and accessibility features. Part of the WakeDock Design System.'
      }
    }
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: { type: 'select' },
      options: ['text', 'email', 'password', 'number', 'search', 'url', 'tel'],
      description: 'HTML input type',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'text' }
      }
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
      description: 'Size of the input field',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'md' }
      }
    },
    variant: {
      control: { type: 'select' },
      options: ['default', 'filled', 'outline'],
      description: 'Visual variant of the input',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' }
      }
    },
    disabled: {
      control: { type: 'boolean' },
      description: 'Whether the input is disabled',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' }
      }
    },
    invalid: {
      control: { type: 'boolean' },
      description: 'Whether the input is in error state',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' }
      }
    },
    placeholder: {
      control: { type: 'text' },
      description: 'Placeholder text',
      table: {
        type: { summary: 'string' }
      }
    }
  }
};

export default meta;
type Story = StoryObj<typeof meta>;

// Default story
export const Default: Story = {
  args: {
    placeholder: 'Enter text...'
  }
};

// Different types
export const TextInput: Story = {
  args: {
    type: 'text',
    placeholder: 'Enter your name'
  }
};

export const EmailInput: Story = {
  args: {
    type: 'email',
    placeholder: 'user@example.com'
  }
};

export const PasswordInput: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter password'
  }
};

export const SearchInput: Story = {
  args: {
    type: 'search',
    placeholder: 'Search...'
  }
};

// Sizes
export const Sizes: Story = {
  render: () => ({
    Component: Input,
    props: {}
  }),
  parameters: {
    docs: {
      source: {
        code: `
<Input size="sm" placeholder="Small input" />
<Input size="md" placeholder="Medium input" />
<Input size="lg" placeholder="Large input" />
        `
      }
    }
  }
};

// Variants
export const Variants: Story = {
  render: () => ({
    Component: Input,
    props: {}
  }),
  parameters: {
    docs: {
      source: {
        code: `
<Input variant="default" placeholder="Default variant" />
<Input variant="filled" placeholder="Filled variant" />
<Input variant="outline" placeholder="Outline variant" />
        `
      }
    }
  }
};

// States
export const InvalidState: Story = {
  args: {
    invalid: true,
    placeholder: 'Invalid input'
  }
};

export const DisabledState: Story = {
  args: {
    disabled: true,
    placeholder: 'Disabled input',
    value: 'Cannot edit'
  }
};

// With label and help text
export const WithLabelAndHelp: Story = {
  render: () => ({
    Component: Input,
    props: {}
  }),
  parameters: {
    docs: {
      source: {
        code: `
<div class="space-y-2">
  <label for="email" class="block text-sm font-medium text-gray-700">
    Email Address
  </label>
  <Input 
    id="email"
    type="email" 
    placeholder="user@example.com"
    aria-describedby="email-help"
  />
  <p id="email-help" class="text-sm text-gray-500">
    We'll never share your email with anyone else.
  </p>
</div>
        `
      }
    }
  }
};

// Error state with message
export const WithErrorMessage: Story = {
  render: () => ({
    Component: Input,
    props: {}
  }),
  parameters: {
    docs: {
      source: {
        code: `
<div class="space-y-2">
  <label for="password" class="block text-sm font-medium text-gray-700">
    Password
  </label>
  <Input 
    id="password"
    type="password" 
    invalid={true}
    aria-describedby="password-error"
    aria-invalid="true"
  />
  <p id="password-error" class="text-sm text-red-600">
    Password must be at least 8 characters long.
  </p>
</div>
        `
      }
    }
  }
};

// Accessibility features
export const AccessibilityFeatures: Story = {
  render: () => ({
    Component: Input,
    props: {}
  }),
  parameters: {
    docs: {
      description: {
        story: `
The Input component includes comprehensive accessibility features:

### Keyboard Navigation
- **Tab**: Navigate to/from the input
- **Enter**: Submit form (when in form context)
- **Escape**: Clear focus (custom implementation)

### Screen Reader Support
- **Semantic HTML**: Uses proper \`<input>\` elements
- **ARIA attributes**: \`aria-invalid\`, \`aria-describedby\`, \`aria-required\`
- **Labels**: Always associate with proper \`<label>\` elements
- **Error states**: Announced to screen readers

### Visual Accessibility
- **Focus indicators**: Clear, high-contrast focus rings
- **Color contrast**: All variants meet WCAG 2.1 AA standards
- **Size targets**: Touch targets meet minimum 44px requirement

### Best Practices
\`\`\`svelte
<label for="username" class="required">
  Username
</label>
<Input 
  id="username"
  type="text"
  required
  aria-describedby="username-help username-error"
  aria-invalid={hasError}
/>
<div id="username-help">Enter your unique username</div>
{#if hasError}
  <div id="username-error" role="alert">
    Username is required
  </div>
{/if}
\`\`\`
        `
      }
    }
  }
};

// Design tokens
export const DesignTokens: Story = {
  parameters: {
    docs: {
      description: {
        story: `
### Design Tokens Used

#### Colors
- \`--color-gray-50\`: Input background (default)
- \`--color-gray-300\`: Border color (default state)
- \`--color-blue-500\`: Border color (focus state)
- \`--color-red-500\`: Border color (error state)
- \`--color-gray-400\`: Placeholder text color

#### Typography
- \`--font-size-sm\`: Small input text (14px)
- \`--font-size-base\`: Default input text (16px)
- \`--font-size-lg\`: Large input text (18px)
- \`--font-weight-normal\`: Input text weight (400)

#### Spacing
- \`--spacing-2\`: Small padding (8px)
- \`--spacing-3\`: Medium padding (12px)
- \`--spacing-4\`: Large padding (16px)

#### Border Radius
- \`--radius-md\`: Default input radius (6px)
- \`--radius-lg\`: Large input radius (8px)

#### Shadows
- \`--shadow-sm\`: Input focus shadow
- \`--shadow-none\`: Default state (no shadow)
        `
      }
    }
  }
};
