/**
 * Unit tests for UnifiedButton component
 * TASK-UI-001: Unification des Composants Button
 */

import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, screen } from '@testing-library/svelte';
import UnifiedButton from './UnifiedButton.svelte';
import type { UnifiedButtonProps } from './UnifiedButton.types';

describe('UnifiedButton', () => {
  // Basic rendering tests
  describe('Basic Rendering', () => {
    it('renders with default props', () => {
      render(UnifiedButton, { props: {} });
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center');
    });

    it('renders slot content', () => {
      render(UnifiedButton, { 
        props: {},
        $$slots: { default: 'Click me' }
      });
      expect(screen.getByText('Click me')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(UnifiedButton, { 
        props: { className: 'custom-class' }
      });
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });

  // Variant tests
  describe('Variants', () => {
    const variants: Array<UnifiedButtonProps['variant']> = [
      'primary', 'secondary', 'success', 'warning', 'error', 'ghost'
    ];

    variants.forEach(variant => {
      it(`renders ${variant} variant correctly`, () => {
        render(UnifiedButton, { 
          props: { variant, testId: `button-${variant}` }
        });
        const button = screen.getByTestId(`button-${variant}`);
        expect(button).toBeInTheDocument();
        // Variant-specific class assertions would go here
      });
    });
  });

  // Size tests
  describe('Sizes', () => {
    const sizes: Array<UnifiedButtonProps['size']> = [
      'xs', 'sm', 'md', 'lg', 'xl'
    ];

    sizes.forEach(size => {
      it(`renders ${size} size correctly`, () => {
        render(UnifiedButton, { 
          props: { size, testId: `button-${size}` }
        });
        const button = screen.getByTestId(`button-${size}`);
        expect(button).toBeInTheDocument();
        // Size-specific class assertions would go here
      });
    });
  });

  // State tests
  describe('States', () => {
    it('handles disabled state', () => {
      render(UnifiedButton, { 
        props: { disabled: true, testId: 'disabled-button' }
      });
      const button = screen.getByTestId('disabled-button');
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });

    it('handles loading state', () => {
      render(UnifiedButton, { 
        props: { loading: true, testId: 'loading-button' }
      });
      const button = screen.getByTestId('loading-button');
      expect(button).toBeDisabled();
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('prevents click when disabled', async () => {
      const handleClick = vi.fn();
      render(UnifiedButton, { 
        props: { disabled: true, testId: 'disabled-button' }
      });
      
      const button = screen.getByTestId('disabled-button');
      button.addEventListener('click', handleClick);
      
      await fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('prevents click when loading', async () => {
      const handleClick = vi.fn();
      render(UnifiedButton, { 
        props: { loading: true, testId: 'loading-button' }
      });
      
      const button = screen.getByTestId('loading-button');
      button.addEventListener('click', handleClick);
      
      await fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  // Link behavior tests
  describe('Link Behavior', () => {
    it('renders as link when href is provided', () => {
      render(UnifiedButton, { 
        props: { 
          href: 'https://example.com',
          testId: 'link-button'
        }
      });
      const link = screen.getByTestId('link-button');
      expect(link.tagName).toBe('A');
      expect(link).toHaveAttribute('href', 'https://example.com');
    });

    it('applies target and rel attributes for links', () => {
      render(UnifiedButton, { 
        props: { 
          href: 'https://example.com',
          target: '_blank',
          rel: 'noopener',
          testId: 'external-link'
        }
      });
      const link = screen.getByTestId('external-link');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener');
    });

    it('applies correct role for links', () => {
      render(UnifiedButton, { 
        props: { 
          href: 'https://example.com',
          testId: 'link-button'
        }
      });
      const link = screen.getByTestId('link-button');
      expect(link).toHaveAttribute('role', 'button');
    });
  });

  // Layout tests
  describe('Layout Options', () => {
    it('applies fullWidth class', () => {
      render(UnifiedButton, { 
        props: { fullWidth: true, testId: 'full-width-button' }
      });
      const button = screen.getByTestId('full-width-button');
      expect(button).toHaveClass('w-full');
    });

    it('handles iconOnly layout', () => {
      render(UnifiedButton, { 
        props: { 
          iconOnly: true,
          icon: 'star',
          testId: 'icon-only-button'
        }
      });
      const button = screen.getByTestId('icon-only-button');
      expect(button).toBeInTheDocument();
      // Icon-specific assertions would go here
    });

    it('applies outlined variant', () => {
      render(UnifiedButton, { 
        props: { 
          outlined: true,
          variant: 'primary',
          testId: 'outlined-button'
        }
      });
      const button = screen.getByTestId('outlined-button');
      expect(button).toBeInTheDocument();
      // Outlined-specific class assertions would go here
    });
  });

  // Event handling tests
  describe('Event Handling', () => {
    it('dispatches click event', async () => {
      const handleClick = vi.fn();
      const { component } = render(UnifiedButton, { 
        props: { testId: 'clickable-button' }
      });
      
      component.$on('click', handleClick);
      const button = screen.getByTestId('clickable-button');
      
      await fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not dispatch click when disabled', async () => {
      const handleClick = vi.fn();
      const { component } = render(UnifiedButton, { 
        props: { disabled: true, testId: 'disabled-button' }
      });
      
      component.$on('click', handleClick);
      const button = screen.getByTestId('disabled-button');
      
      await fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  // Accessibility tests
  describe('Accessibility', () => {
    it('applies aria-label', () => {
      render(UnifiedButton, { 
        props: { 
          ariaLabel: 'Custom button label',
          testId: 'labeled-button'
        }
      });
      const button = screen.getByTestId('labeled-button');
      expect(button).toHaveAttribute('aria-label', 'Custom button label');
    });

    it('applies test ID', () => {
      render(UnifiedButton, { 
        props: { testId: 'test-button' }
      });
      expect(screen.getByTestId('test-button')).toBeInTheDocument();
    });

    it('has proper tabindex when disabled', () => {
      render(UnifiedButton, { 
        props: { 
          disabled: true,
          href: 'https://example.com',
          testId: 'disabled-link'
        }
      });
      const link = screen.getByTestId('disabled-link');
      expect(link).toHaveAttribute('tabindex', '-1');
    });

    it('includes screen reader text for loading state', () => {
      render(UnifiedButton, { 
        props: { loading: true }
      });
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  // Icon tests
  describe('Icon Support', () => {
    it('renders icon on the left by default', () => {
      render(UnifiedButton, { 
        props: { 
          icon: 'star',
          testId: 'icon-button'
        },
        $$slots: { default: 'Button text' }
      });
      const button = screen.getByTestId('icon-button');
      expect(button).toBeInTheDocument();
      // Icon position assertions would go here
    });

    it('renders icon on the right when specified', () => {
      render(UnifiedButton, { 
        props: { 
          icon: 'arrow-right',
          iconPosition: 'right',
          testId: 'right-icon-button'
        },
        $$slots: { default: 'Next' }
      });
      const button = screen.getByTestId('right-icon-button');
      expect(button).toBeInTheDocument();
      // Right icon position assertions would go here
    });
  });

  // Type validation tests
  describe('Type Support', () => {
    it('applies button type attribute', () => {
      render(UnifiedButton, { 
        props: { 
          type: 'submit',
          testId: 'submit-button'
        }
      });
      const button = screen.getByTestId('submit-button');
      expect(button).toHaveAttribute('type', 'submit');
    });
  });

  // Integration tests
  describe('Integration', () => {
    it('combines multiple props correctly', () => {
      render(UnifiedButton, { 
        props: {
          variant: 'success',
          size: 'lg',
          disabled: false,
          loading: false,
          fullWidth: true,
          outlined: true,
          icon: 'check',
          iconPosition: 'left',
          ariaLabel: 'Save document',
          testId: 'complex-button',
          className: 'custom-save-button'
        }
      });
      
      const button = screen.getByTestId('complex-button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-label', 'Save document');
      expect(button).toHaveClass('w-full', 'custom-save-button');
    });
  });

  // Regression tests for migration
  describe('Migration Compatibility', () => {
    it('maintains backward compatibility with existing PrimaryButton usage', () => {
      render(UnifiedButton, { 
        props: {
          variant: 'primary',
          size: 'md',
          fullWidth: false,
          testId: 'legacy-primary'
        }
      });
      
      const button = screen.getByTestId('legacy-primary');
      expect(button).toBeInTheDocument();
      // Legacy compatibility assertions would go here
    });

    it('maintains backward compatibility with existing SecondaryButton usage', () => {
      render(UnifiedButton, { 
        props: {
          variant: 'secondary',
          size: 'sm',
          testId: 'legacy-secondary'
        }
      });
      
      const button = screen.getByTestId('legacy-secondary');
      expect(button).toBeInTheDocument();
      // Legacy compatibility assertions would go here
    });

    it('maintains backward compatibility with existing IconButton usage', () => {
      render(UnifiedButton, { 
        props: {
          variant: 'ghost',
          iconOnly: true,
          size: 'md',
          testId: 'legacy-icon'
        }
      });
      
      const button = screen.getByTestId('legacy-icon');
      expect(button).toBeInTheDocument();
      // Legacy compatibility assertions would go here
    });
  });
});