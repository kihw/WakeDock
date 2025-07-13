import type { Meta, StoryObj } from '@storybook/svelte';
import Modal from '../organisms/Modal.svelte';

const meta: Meta<Modal> = {
  title: 'Design System/Organisms/Modal',
  component: Modal,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'A flexible modal component with accessibility features, backdrop management, and customizable content. Supports focus trapping and proper ARIA patterns.'
      }
    }
  },
  tags: ['autodocs'],
  argTypes: {
    show: {
      control: { type: 'boolean' },
      description: 'Whether the modal is visible',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' }
      }
    },
    title: {
      control: { type: 'text' },
      description: 'Modal title (optional)',
      table: {
        type: { summary: 'string' }
      }
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg', 'xl', 'full'],
      description: 'Size of the modal',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'md' }
      }
    },
    closable: {
      control: { type: 'boolean' },
      description: 'Whether the modal can be closed',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'true' }
      }
    },
    closeOnEscape: {
      control: { type: 'boolean' },
      description: 'Close modal when Escape key is pressed',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'true' }
      }
    },
    closeOnBackdrop: {
      control: { type: 'boolean' },
      description: 'Close modal when clicking outside',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'true' }
      }
    }
  }
};

export default meta;
type Story = StoryObj<typeof meta>;

// Basic modal
export const Default: Story = {
  args: {
    show: true,
    title: 'Modal Title'
  },
  render: (args) => ({
    Component: Modal,
    props: {
      ...args,
      $$slots: {
        default: 'This is the modal content. You can put any content here.'
      }
    }
  })
};

// Different sizes
export const Small: Story = {
  args: {
    show: true,
    title: 'Small Modal',
    size: 'sm'
  },
  render: (args) => ({
    Component: Modal,
    props: {
      ...args,
      $$slots: {
        default: 'This is a small modal with limited content space.'
      }
    }
  })
};

export const Large: Story = {
  args: {
    show: true,
    title: 'Large Modal',
    size: 'lg'
  },
  render: (args) => ({
    Component: Modal,
    props: {
      ...args,
      $$slots: {
        default: 'This is a large modal with more content space. You can include forms, tables, or other complex content here.'
      }
    }
  })
};

export const FullScreen: Story = {
  args: {
    show: true,
    title: 'Full Screen Modal',
    size: 'full'
  },
  render: (args) => ({
    Component: Modal,
    props: {
      ...args,
      $$slots: {
        default: 'This modal takes up the entire viewport. Useful for complex forms or detailed content.'
      }
    }
  })
};

// Modal with form content
export const WithForm: Story = {
  args: {
    show: true,
    title: 'User Settings'
  },
  render: (args) => ({
    Component: Modal,
    props: {
      ...args,
      $$slots: {
        default: `
          <form class="space-y-4">
            <div>
              <label for="name" class="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input 
                type="text" 
                id="name" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your name"
              />
            </div>
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input 
                type="email" 
                id="email" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="user@example.com"
              />
            </div>
            <div>
              <label for="bio" class="block text-sm font-medium text-gray-700 mb-1">
                Bio
              </label>
              <textarea 
                id="bio" 
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Tell us about yourself..."
              ></textarea>
            </div>
          </form>
        `,
        actions: `
          <Button variant="outline">Cancel</Button>
          <Button variant="primary">Save Changes</Button>
        `
      }
    }
  })
};

// Confirmation modal
export const ConfirmationModal: Story = {
  args: {
    show: true,
    title: 'Confirm Deletion',
    size: 'sm'
  },
  render: (args) => ({
    Component: Modal,
    props: {
      ...args,
      $$slots: {
        default: `
          <div class="text-center">
            <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 15.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">Delete User Account</h3>
            <p class="text-sm text-gray-500">
              Are you sure you want to delete this user account? This action cannot be undone.
            </p>
          </div>
        `,
        actions: `
          <Button variant="outline">Cancel</Button>
          <Button variant="danger">Delete Account</Button>
        `
      }
    }
  })
};

// Non-closable modal
export const NonClosable: Story = {
  args: {
    show: true,
    title: 'Processing...',
    closable: false,
    closeOnEscape: false,
    closeOnBackdrop: false
  },
  render: (args) => ({
    Component: Modal,
    props: {
      ...args,
      $$slots: {
        default: `
          <div class="text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p class="text-gray-600">Please wait while we process your request...</p>
          </div>
        `
      }
    }
  })
};

// Accessibility features
export const AccessibilityFeatures: Story = {
  parameters: {
    docs: {
      description: {
        story: `
The Modal component implements comprehensive accessibility features:

### Focus Management
- **Focus trap**: Focus is trapped within the modal when open
- **Initial focus**: First focusable element receives focus
- **Return focus**: Focus returns to trigger element when closed
- **Tab cycling**: Tab navigation stays within modal content

### Keyboard Navigation
- **Escape key**: Closes modal (unless disabled)
- **Tab/Shift+Tab**: Navigate between focusable elements
- **Enter/Space**: Activate buttons and controls

### Screen Reader Support
- **\`role="dialog"\`**: Identifies modal as dialog
- **\`aria-modal="true"\`**: Indicates modal behavior
- **\`aria-labelledby\`**: References modal title
- **\`aria-describedby\`**: References modal description
- **\`aria-hidden\`**: Hides background content from screen readers

### Implementation Example
\`\`\`svelte
<Modal
  bind:show={showModal}
  title="Accessible Modal"
  aria-describedby="modal-description"
>
  <p id="modal-description">
    This modal demonstrates proper accessibility implementation.
  </p>
  
  <svelte:fragment slot="actions">
    <Button on:click={() => showModal = false}>Close</Button>
  </svelte:fragment>
</Modal>
\`\`\`

### Best Practices
1. **Always provide a title** for screen reader context
2. **Use semantic HTML** within modal content
3. **Test with keyboard only** navigation
4. **Verify screen reader** announcements
5. **Ensure sufficient color contrast** for all content
        `
      }
    }
  }
};

// Design patterns
export const DesignPatterns: Story = {
  parameters: {
    docs: {
      description: {
        story: `
### Common Modal Patterns

#### Information Modal
For displaying read-only information or notifications.

#### Form Modal
For data entry with validation and submission.

#### Confirmation Modal
For confirming destructive or important actions.

#### Loading Modal
For showing progress during asynchronous operations.

### Design Tokens Used

#### Layout
- \`--modal-backdrop\`: Semi-transparent overlay (rgba(0,0,0,0.5))
- \`--modal-border-radius\`: Rounded corners (8px)
- \`--modal-shadow\`: Drop shadow for depth

#### Spacing
- \`--modal-padding\`: Internal content padding (24px)
- \`--modal-gap\`: Gap between elements (16px)

#### Z-Index
- \`--modal-z-index\`: Layer stacking (1000)
- \`--backdrop-z-index\`: Backdrop layer (999)

#### Animation
- **Duration**: 200ms for enter/exit
- **Easing**: \`cubic-bezier(0.4, 0, 0.2, 1)\`
- **Properties**: \`opacity\` and \`transform\` for performance
        `
      }
    }
  }
};
