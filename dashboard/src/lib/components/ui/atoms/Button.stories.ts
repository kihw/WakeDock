import type { Meta, StoryObj } from '@storybook/svelte';
import Button from '../lib/components/ui/atoms/Button.svelte';

// Meta configuration for the Button component
const meta: Meta<Button> = {
  title: 'Design System/Atoms/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile button component with multiple variants, sizes, and states. Supports accessibility features and follows WakeDock design system guidelines.'
      }
    }
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'outline', 'ghost', 'danger'],
      description: 'Visual style variant of the button',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'primary' }
      }
    },
    size: {
      control: { type: 'select' },
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Size of the button',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'md' }
      }
    },
    disabled: {
      control: { type: 'boolean' },
      description: 'Whether the button is disabled',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' }
      }
    },
    loading: {
      control: { type: 'boolean' },
      description: 'Whether the button is in loading state',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' }
      }
    },
    fullWidth: {
      control: { type: 'boolean' },
      description: 'Whether the button should take full width',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' }
      }
    }
  }
};

export default meta;
type Story = StoryObj<typeof meta>;

// Default story
export const Default: Story = {
  args: {
    children: 'Button'
  }
};

// Primary variant
export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button'
  }
};

// Secondary variant
export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button'
  }
};

// Outline variant
export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Outline Button'
  }
};

// Ghost variant
export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Ghost Button'
  }
};

// Danger variant
export const Danger: Story = {
  args: {
    variant: 'danger',
    children: 'Danger Button'
  }
};

// Size variations
export const Sizes: Story = {
  render: () => ({
    Component: Button,
    props: {}
  }),
  parameters: {
    docs: {
      source: {
        code: `
<Button size="xs">Extra Small</Button>
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
<Button size="xl">Extra Large</Button>
        `
      }
    }
  }
};

// Loading state
export const Loading: Story = {
  args: {
    loading: true,
    children: 'Loading...'
  }
};

// Disabled state
export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled Button'
  }
};

// Full width
export const FullWidth: Story = {
  args: {
    fullWidth: true,
    children: 'Full Width Button'
  },
  parameters: {
    layout: 'padded'
  }
};

// With icon
export const WithIcon: Story = {
  render: () => ({
    Component: Button,
    props: {
      children: 'Download'
    }
  }),
  parameters: {
    docs: {
      source: {
        code: `
<script>
  import { Download } from 'lucide-svelte';
</script>

<Button>
  <Download class="w-4 h-4 mr-2" />
  Download
</Button>
        `
      }
    }
  }
};

// Interactive examples
export const InteractiveExamples: Story = {
  render: () => ({
    Component: Button,
    props: {}
  }),
  parameters: {
    docs: {
      source: {
        code: `
<div class="space-y-4">
  <div class="flex gap-2">
    <Button variant="primary">Save</Button>
    <Button variant="outline">Cancel</Button>
  </div>
  
  <div class="flex gap-2">
    <Button variant="danger" size="sm">Delete</Button>
    <Button variant="ghost" size="sm">Archive</Button>
  </div>
  
  <div class="flex gap-2">
    <Button loading>Processing...</Button>
    <Button disabled>Unavailable</Button>
  </div>
</div>
        `
      }
    }
  }
};

// Accessibility demonstration
export const AccessibilityFeatures: Story = {
  render: () => ({
    Component: Button,
    props: {
      children: 'Accessible Button'
    }
  }),
  parameters: {
    docs: {
      description: {
        story: `
The Button component includes several accessibility features:

- **Keyboard Navigation**: Fully navigable with Tab and Enter/Space keys
- **Screen Reader Support**: Proper ARIA labels and roles
- **Focus Management**: Clear focus indicators and proper tab order
- **Reduced Motion**: Respects prefers-reduced-motion setting
- **Color Contrast**: All variants meet WCAG 2.1 AA standards

### ARIA Attributes
- \`role="button"\` when using non-button elements
- \`aria-disabled="true"\` for disabled state
- \`aria-label\` or \`aria-labelledby\` for context
- \`aria-describedby\` for additional information

### Example with ARIA
\`\`\`svelte
<Button 
  aria-label="Delete user account"
  aria-describedby="delete-warning"
  variant="danger"
>
  Delete Account
</Button>
<p id="delete-warning" class="sr-only">
  This action cannot be undone
</p>
\`\`\`
        `
      }
    }
  }
};

// Design tokens showcase
export const DesignTokens: Story = {
  parameters: {
    docs: {
      description: {
        story: `
### Design Tokens Used

The Button component uses the following design tokens from the WakeDock Design System:

#### Colors
- \`--color-primary-500\`: Primary button background
- \`--color-primary-600\`: Primary button hover state
- \`--color-gray-200\`: Secondary button border
- \`--color-red-500\`: Danger button background

#### Spacing
- \`--spacing-2\`: Small padding (8px)
- \`--spacing-3\`: Medium padding (12px)
- \`--spacing-4\`: Large padding (16px)

#### Typography
- \`--font-weight-medium\`: Button text weight (500)
- \`--font-size-sm\`: Small button text (14px)
- \`--font-size-base\`: Default button text (16px)

#### Border Radius
- \`--radius-md\`: Default button radius (6px)
- \`--radius-lg\`: Large button radius (8px)

#### Transitions
- \`--transition-base\`: Default hover/focus transitions
        `
      }
    }
  }
};
