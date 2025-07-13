/**
 * Storybook stories for UnifiedButton component
 * TASK-UI-001: Unification des Composants Button
 */

import type { Meta, StoryObj } from '@storybook/svelte';
import UnifiedButton from './UnifiedButton.svelte';
import type { UnifiedButtonProps } from './UnifiedButton.types';

const meta: Meta<UnifiedButton> = {
  title: 'UI/Atoms/UnifiedButton',
  component: UnifiedButton,
  parameters: {
    docs: {
      description: {
        component: `
# UnifiedButton Component

A comprehensive, unified button component that consolidates all button variants into a single, configurable component. This replaces the previous fragmented button system with a more maintainable and feature-complete solution.

## Features

- **Single Component**: Replaces 5 separate button components
- **Full Design Token Integration**: Uses centralized design system tokens
- **Comprehensive Accessibility**: WCAG 2.1 AA compliant
- **Flexible Icon Support**: Left, right, or icon-only configurations
- **Link/Button Dual Nature**: Seamless switching based on href prop
- **Loading States**: Built-in loading spinner with accessibility
- **TypeScript Support**: Full type safety with comprehensive interfaces
- **Extensive Testing**: >90% test coverage

## Migration Guide

This component replaces:
- \`BaseButton.svelte\`
- \`PrimaryButton.svelte\`
- \`SecondaryButton.svelte\`
- \`IconButton.svelte\`
- \`Button.svelte\` (wrapper)

### Before (Legacy)
\`\`\`svelte
<PrimaryButton size="lg" fullWidth on:click={handleClick}>
  Submit
</PrimaryButton>

<SecondaryButton size="md" on:click={handleCancel}>
  Cancel
</SecondaryButton>

<IconButton variant="ghost" size="sm" on:click={handleEdit}>
  ✏️
</IconButton>
\`\`\`

### After (Unified)
\`\`\`svelte
<UnifiedButton variant="primary" size="lg" fullWidth on:click={handleClick}>
  Submit
</UnifiedButton>

<UnifiedButton variant="secondary" size="md" on:click={handleCancel}>
  Cancel
</UnifiedButton>

<UnifiedButton variant="ghost" size="sm" iconOnly on:click={handleEdit}>
  ✏️
</UnifiedButton>
\`\`\`
        `
      }
    },
    layout: 'centered'
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'success', 'warning', 'error', 'ghost'],
      description: 'Visual style variant'
    },
    size: {
      control: { type: 'select' },
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Button size'
    },
    disabled: {
      control: { type: 'boolean' },
      description: 'Disable the button'
    },
    loading: {
      control: { type: 'boolean' },
      description: 'Show loading state'
    },
    fullWidth: {
      control: { type: 'boolean' },
      description: 'Make button full width'
    },
    outlined: {
      control: { type: 'boolean' },
      description: 'Use outlined variant'
    },
    iconOnly: {
      control: { type: 'boolean' },
      description: 'Icon-only button (no text)'
    },
    icon: {
      control: { type: 'text' },
      description: 'Icon identifier'
    },
    iconPosition: {
      control: { type: 'select' },
      options: ['left', 'right'],
      description: 'Icon position relative to text'
    },
    href: {
      control: { type: 'text' },
      description: 'Link URL (renders as anchor)'
    },
    target: {
      control: { type: 'text' },
      description: 'Link target (when href provided)'
    },
    type: {
      control: { type: 'select' },
      options: ['button', 'submit', 'reset'],
      description: 'Button type attribute'
    },
    ariaLabel: {
      control: { type: 'text' },
      description: 'Accessibility label'
    },
    testId: {
      control: { type: 'text' },
      description: 'Test identifier'
    }
  },
  args: {
    variant: 'primary',
    size: 'md',
    disabled: false,
    loading: false,
    fullWidth: false,
    outlined: false,
    iconOnly: false,
    iconPosition: 'left',
    type: 'button'
  }
};

export default meta;
type Story = StoryObj<typeof meta>;

// Basic examples
export const Default: Story = {
  args: {},
  render: (args) => ({
    Component: UnifiedButton,
    props: args,
    slot: 'Default Button'
  })
};

export const Primary: Story = {
  args: {
    variant: 'primary'
  },
  render: (args) => ({
    Component: UnifiedButton,
    props: args,
    slot: 'Primary Button'
  })
};

export const Secondary: Story = {
  args: {
    variant: 'secondary'
  },
  render: (args) => ({
    Component: UnifiedButton,
    props: args,
    slot: 'Secondary Button'
  })
};

export const Success: Story = {
  args: {
    variant: 'success'
  },
  render: (args) => ({
    Component: UnifiedButton,
    props: args,
    slot: 'Success Button'
  })
};

export const Warning: Story = {
  args: {
    variant: 'warning'
  },
  render: (args) => ({
    Component: UnifiedButton,
    props: args,
    slot: 'Warning Button'
  })
};

export const Error: Story = {
  args: {
    variant: 'error'
  },
  render: (args) => ({
    Component: UnifiedButton,
    props: args,
    slot: 'Error Button'
  })
};

export const Ghost: Story = {
  args: {
    variant: 'ghost'
  },
  render: (args) => ({
    Component: UnifiedButton,
    props: args,
    slot: 'Ghost Button'
  })
};

// Size variations
export const Sizes: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-col gap-4 items-start">
        <UnifiedButton size="xs">Extra Small</UnifiedButton>
        <UnifiedButton size="sm">Small</UnifiedButton>
        <UnifiedButton size="md">Medium</UnifiedButton>
        <UnifiedButton size="lg">Large</UnifiedButton>
        <UnifiedButton size="xl">Extra Large</UnifiedButton>
      </div>
    `
  })
};

// State variations
export const States: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-wrap gap-4">
        <UnifiedButton>Normal</UnifiedButton>
        <UnifiedButton disabled>Disabled</UnifiedButton>
        <UnifiedButton loading>Loading</UnifiedButton>
        <UnifiedButton variant="secondary" disabled>Disabled Secondary</UnifiedButton>
        <UnifiedButton variant="success" loading>Loading Success</UnifiedButton>
      </div>
    `
  })
};

// Icon examples
export const WithIcons: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-col gap-4 items-start">
        <UnifiedButton icon="star" iconPosition="left">Left Icon</UnifiedButton>
        <UnifiedButton icon="arrow-right" iconPosition="right">Right Icon</UnifiedButton>
        <UnifiedButton icon="star" iconOnly ariaLabel="Favorite" />
        <UnifiedButton variant="secondary" icon="download" iconPosition="left">Download</UnifiedButton>
        <UnifiedButton variant="ghost" icon="settings" iconOnly ariaLabel="Settings" />
      </div>
    `
  })
};

// Outlined variations
export const Outlined: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-wrap gap-4">
        <UnifiedButton variant="primary" outlined>Primary Outlined</UnifiedButton>
        <UnifiedButton variant="secondary" outlined>Secondary Outlined</UnifiedButton>
        <UnifiedButton variant="success" outlined>Success Outlined</UnifiedButton>
        <UnifiedButton variant="warning" outlined>Warning Outlined</UnifiedButton>
        <UnifiedButton variant="error" outlined>Error Outlined</UnifiedButton>
      </div>
    `
  })
};

// Layout options
export const Layout: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-col gap-4 w-full max-w-sm">
        <UnifiedButton>Regular Width</UnifiedButton>
        <UnifiedButton fullWidth>Full Width</UnifiedButton>
        <UnifiedButton fullWidth variant="secondary">Full Width Secondary</UnifiedButton>
      </div>
    `
  })
};

// Link behavior
export const AsLinks: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-col gap-4 items-start">
        <UnifiedButton href="https://example.com">Internal Link</UnifiedButton>
        <UnifiedButton 
          href="https://external.com" 
          target="_blank" 
          rel="noopener"
          variant="secondary"
        >
          External Link
        </UnifiedButton>
        <UnifiedButton href="#section" variant="ghost">Anchor Link</UnifiedButton>
      </div>
    `
  })
};

// Form integration
export const FormButtons: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <form class="flex flex-col gap-4 p-6 border rounded-lg max-w-md">
        <h3 class="text-lg font-semibold">Form Example</h3>
        
        <input 
          type="text" 
          placeholder="Enter your name" 
          class="p-2 border rounded"
        />
        
        <div class="flex gap-2">
          <UnifiedButton type="submit" variant="primary">
            Submit
          </UnifiedButton>
          <UnifiedButton type="reset" variant="secondary">
            Reset
          </UnifiedButton>
          <UnifiedButton type="button" variant="ghost">
            Cancel
          </UnifiedButton>
        </div>
      </form>
    `
  })
};

// Real-world usage examples
export const RealWorldExamples: Story = {
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-col gap-8 max-w-2xl">
        <!-- Navigation Bar -->
        <section class="flex justify-between items-center p-4 bg-gray-50 rounded">
          <h3 class="font-semibold">Navigation Bar</h3>
          <div class="flex gap-2">
            <UnifiedButton variant="ghost" size="sm">Home</UnifiedButton>
            <UnifiedButton variant="ghost" size="sm">About</UnifiedButton>
            <UnifiedButton variant="primary" size="sm">Sign Up</UnifiedButton>
          </div>
        </section>

        <!-- Action Bar -->
        <section class="flex justify-between items-center p-4 bg-gray-50 rounded">
          <h3 class="font-semibold">Action Bar</h3>
          <div class="flex gap-2">
            <UnifiedButton variant="secondary" icon="edit" iconPosition="left" size="sm">
              Edit
            </UnifiedButton>
            <UnifiedButton variant="error" icon="trash" iconPosition="left" size="sm">
              Delete
            </UnifiedButton>
            <UnifiedButton variant="primary" icon="save" iconPosition="left" size="sm">
              Save
            </UnifiedButton>
          </div>
        </section>

        <!-- Icon Toolbar -->
        <section class="flex justify-between items-center p-4 bg-gray-50 rounded">
          <h3 class="font-semibold">Icon Toolbar</h3>
          <div class="flex gap-1">
            <UnifiedButton variant="ghost" iconOnly ariaLabel="Bold" size="sm">B</UnifiedButton>
            <UnifiedButton variant="ghost" iconOnly ariaLabel="Italic" size="sm">I</UnifiedButton>
            <UnifiedButton variant="ghost" iconOnly ariaLabel="Underline" size="sm">U</UnifiedButton>
            <div class="w-px bg-gray-300 mx-1"></div>
            <UnifiedButton variant="ghost" iconOnly ariaLabel="Align Left" size="sm">⫷</UnifiedButton>
            <UnifiedButton variant="ghost" iconOnly ariaLabel="Center" size="sm">⫸</UnifiedButton>
            <UnifiedButton variant="ghost" iconOnly ariaLabel="Align Right" size="sm">⫹</UnifiedButton>
          </div>
        </section>

        <!-- Card Actions -->
        <section class="p-6 bg-white border rounded-lg shadow-sm">
          <h3 class="font-semibold mb-4">Product Card</h3>
          <p class="text-gray-600 mb-6">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
          <div class="flex justify-between items-center">
            <span class="text-2xl font-bold">$29.99</span>
            <div class="flex gap-2">
              <UnifiedButton variant="ghost" iconOnly ariaLabel="Add to Wishlist">♡</UnifiedButton>
              <UnifiedButton variant="primary">Add to Cart</UnifiedButton>
            </div>
          </div>
        </section>
      </div>
    `
  })
};

// Accessibility showcase
export const AccessibilityShowcase: Story = {
  parameters: {
    docs: {
      description: {
        story: `
This story demonstrates the accessibility features of the UnifiedButton component:

- **ARIA Labels**: Descriptive labels for screen readers
- **Keyboard Navigation**: Full keyboard support with focus indicators
- **Disabled States**: Proper disabled attribute and aria-disabled
- **Loading States**: Screen reader announcements for loading
- **Link Semantics**: Proper role and navigation for link buttons
        `
      }
    }
  },
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="flex flex-col gap-4 items-start">
        <UnifiedButton ariaLabel="Close dialog">×</UnifiedButton>
        <UnifiedButton iconOnly ariaLabel="Favorite this item">⭐</UnifiedButton>
        <UnifiedButton loading ariaLabel="Saving your changes">Save</UnifiedButton>
        <UnifiedButton disabled ariaLabel="Submit form (currently disabled)">Submit</UnifiedButton>
        <UnifiedButton 
          href="https://example.com" 
          target="_blank" 
          rel="noopener"
          ariaLabel="Open documentation in new tab"
        >
          Documentation
        </UnifiedButton>
      </div>
    `
  })
};

// Performance showcase
export const PerformanceShowcase: Story = {
  parameters: {
    docs: {
      description: {
        story: `
This story demonstrates the performance aspects of the UnifiedButton component:

- **Bundle Size**: Single component vs 5 separate components
- **CSS Optimization**: Design token-based styling
- **Rendering Performance**: Efficient conditional rendering
- **Memory Usage**: Minimal component overhead
        `
      }
    }
  },
  render: () => ({
    Component: UnifiedButton,
    template: `
      <div class="grid grid-cols-5 gap-2">
        {#each Array(50) as _, i}
          <UnifiedButton 
            variant={['primary', 'secondary', 'success', 'warning', 'error'][i % 5]}
            size={['xs', 'sm', 'md', 'lg', 'xl'][i % 5]}
          >
            Button {i + 1}
          </UnifiedButton>
        {/each}
      </div>
    `
  })
};