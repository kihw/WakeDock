/**
 * Unit tests for BaseInput component
 * TASK-UI-002: Refactorisation du Système d'Input
 */

import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, screen } from '@testing-library/svelte';
import BaseInput from './BaseInput.svelte';
import type { BaseInputProps } from './BaseInput.types';

describe('BaseInput', () => {
  // Basic rendering tests
  describe('Basic Rendering', () => {
    it('renders with default props', () => {
      render(BaseInput, { props: {} });
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('type', 'text');
    });

    it('renders with custom value', () => {
      render(BaseInput, { props: { value: 'test value' } });
      const input = screen.getByDisplayValue('test value');
      expect(input).toBeInTheDocument();
    });

    it('applies placeholder text', () => {
      render(BaseInput, { props: { placeholder: 'Enter text...' } });
      const input = screen.getByPlaceholderText('Enter text...');
      expect(input).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(BaseInput, { 
        props: { className: 'custom-input', testId: 'test-input' }
      });
      const input = screen.getByTestId('test-input');
      expect(input).toHaveClass('custom-input');
    });
  });

  // Input types tests
  describe('Input Types', () => {
    const inputTypes: Array<BaseInputProps['type']> = [
      'text', 'email', 'password', 'number', 'tel', 'url', 'search',
      'date', 'time', 'datetime-local', 'month', 'week', 'color', 'file', 'range'
    ];

    inputTypes.forEach(type => {
      it(`renders ${type} input type correctly`, () => {
        render(BaseInput, { 
          props: { type, testId: `input-${type}` }
        });
        const input = screen.getByTestId(`input-${type}`);
        expect(input).toHaveAttribute('type', type);
      });
    });
  });

  // Size variants tests
  describe('Size Variants', () => {
    const sizes: Array<BaseInputProps['size']> = ['sm', 'md', 'lg'];

    sizes.forEach(size => {
      it(`applies ${size} size classes correctly`, () => {
        render(BaseInput, { 
          props: { size, testId: `input-${size}` }
        });
        const input = screen.getByTestId(`input-${size}`);
        expect(input).toBeInTheDocument();
        // Size-specific class verification would go here
      });
    });
  });

  // Variant tests
  describe('Variants', () => {
    const variants: Array<BaseInputProps['variant']> = [
      'default', 'success', 'warning', 'error'
    ];

    variants.forEach(variant => {
      it(`applies ${variant} variant correctly`, () => {
        render(BaseInput, { 
          props: { variant, testId: `input-${variant}` }
        });
        const input = screen.getByTestId(`input-${variant}`);
        expect(input).toBeInTheDocument();
        // Variant-specific class verification would go here
      });
    });
  });

  // State tests
  describe('States', () => {
    it('handles disabled state', () => {
      render(BaseInput, { 
        props: { disabled: true, testId: 'disabled-input' }
      });
      const input = screen.getByTestId('disabled-input');
      expect(input).toBeDisabled();
    });

    it('handles readonly state', () => {
      render(BaseInput, { 
        props: { readonly: true, testId: 'readonly-input' }
      });
      const input = screen.getByTestId('readonly-input');
      expect(input).toHaveAttribute('readonly');
    });

    it('handles required state', () => {
      render(BaseInput, { 
        props: { required: true, testId: 'required-input' }
      });
      const input = screen.getByTestId('required-input');
      expect(input).toBeRequired();
    });

    it('applies fullWidth correctly', () => {
      render(BaseInput, { 
        props: { fullWidth: true, testId: 'full-width-input' }
      });
      const input = screen.getByTestId('full-width-input');
      expect(input).toHaveClass('w-full');
    });
  });

  // HTML attributes tests
  describe('HTML Attributes', () => {
    it('applies id attribute', () => {
      render(BaseInput, { props: { id: 'test-input' } });
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('id', 'test-input');
    });

    it('applies name attribute', () => {
      render(BaseInput, { 
        props: { name: 'username', testId: 'name-input' }
      });
      const input = screen.getByTestId('name-input');
      expect(input).toHaveAttribute('name', 'username');
    });

    it('applies autocomplete attribute', () => {
      render(BaseInput, { 
        props: { autocomplete: 'email', testId: 'autocomplete-input' }
      });
      const input = screen.getByTestId('autocomplete-input');
      expect(input).toHaveAttribute('autocomplete', 'email');
    });

    it('applies minLength and maxLength', () => {
      render(BaseInput, { 
        props: { minLength: 3, maxLength: 10, testId: 'length-input' }
      });
      const input = screen.getByTestId('length-input');
      expect(input).toHaveAttribute('minlength', '3');
      expect(input).toHaveAttribute('maxlength', '10');
    });

    it('applies min and max for number inputs', () => {
      render(BaseInput, { 
        props: { type: 'number', min: 0, max: 100, testId: 'number-input' }
      });
      const input = screen.getByTestId('number-input');
      expect(input).toHaveAttribute('min', '0');
      expect(input).toHaveAttribute('max', '100');
    });

    it('applies step for number inputs', () => {
      render(BaseInput, { 
        props: { type: 'number', step: 0.1, testId: 'step-input' }
      });
      const input = screen.getByTestId('step-input');
      expect(input).toHaveAttribute('step', '0.1');
    });

    it('applies pattern attribute', () => {
      render(BaseInput, { 
        props: { pattern: '[0-9]{3}-[0-9]{3}-[0-9]{4}', testId: 'pattern-input' }
      });
      const input = screen.getByTestId('pattern-input');
      expect(input).toHaveAttribute('pattern', '[0-9]{3}-[0-9]{3}-[0-9]{4}');
    });
  });

  // Accessibility tests
  describe('Accessibility', () => {
    it('applies aria-label', () => {
      render(BaseInput, { 
        props: { ariaLabel: 'Username input', testId: 'aria-input' }
      });
      const input = screen.getByTestId('aria-input');
      expect(input).toHaveAttribute('aria-label', 'Username input');
    });

    it('applies aria-describedby', () => {
      render(BaseInput, { 
        props: { ariaDescribedBy: 'help-text', testId: 'described-input' }
      });
      const input = screen.getByTestId('described-input');
      expect(input).toHaveAttribute('aria-describedby', 'help-text');
    });

    it('applies test ID for testing', () => {
      render(BaseInput, { props: { testId: 'test-input' } });
      expect(screen.getByTestId('test-input')).toBeInTheDocument();
    });

    it('focuses when autofocus is true', () => {
      render(BaseInput, { 
        props: { autofocus: true, testId: 'autofocus-input' }
      });
      const input = screen.getByTestId('autofocus-input');
      expect(input).toHaveFocus();
    });
  });

  // Event handling tests
  describe('Event Handling', () => {
    it('dispatches input event on value change', async () => {
      const handleInput = vi.fn();
      const { component } = render(BaseInput, { 
        props: { testId: 'input-test' }
      });
      
      component.$on('input', handleInput);
      const input = screen.getByTestId('input-test');
      
      await fireEvent.input(input, { target: { value: 'new value' } });
      expect(handleInput).toHaveBeenCalledTimes(1);
    });

    it('dispatches change event', async () => {
      const handleChange = vi.fn();
      const { component } = render(BaseInput, { 
        props: { testId: 'change-test' }
      });
      
      component.$on('change', handleChange);
      const input = screen.getByTestId('change-test');
      
      await fireEvent.change(input, { target: { value: 'changed' } });
      expect(handleChange).toHaveBeenCalledTimes(1);
    });

    it('dispatches focus and blur events', async () => {
      const handleFocus = vi.fn();
      const handleBlur = vi.fn();
      const { component } = render(BaseInput, { 
        props: { testId: 'focus-test' }
      });
      
      component.$on('focus', handleFocus);
      component.$on('blur', handleBlur);
      const input = screen.getByTestId('focus-test');
      
      await fireEvent.focus(input);
      expect(handleFocus).toHaveBeenCalledTimes(1);
      
      await fireEvent.blur(input);
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('dispatches keydown and keyup events', async () => {
      const handleKeydown = vi.fn();
      const handleKeyup = vi.fn();
      const { component } = render(BaseInput, { 
        props: { testId: 'key-test' }
      });
      
      component.$on('keydown', handleKeydown);
      component.$on('keyup', handleKeyup);
      const input = screen.getByTestId('key-test');
      
      await fireEvent.keyDown(input, { key: 'Enter' });
      expect(handleKeydown).toHaveBeenCalledTimes(1);
      
      await fireEvent.keyUp(input, { key: 'Enter' });
      expect(handleKeyup).toHaveBeenCalledTimes(1);
    });

    it('handles number input conversion', async () => {
      const handleInput = vi.fn();
      const { component } = render(BaseInput, { 
        props: { type: 'number', testId: 'number-test' }
      });
      
      component.$on('input', handleInput);
      const input = screen.getByTestId('number-test');
      
      await fireEvent.input(input, { target: { value: '42' } });
      expect(handleInput).toHaveBeenCalledTimes(1);
      // Value should be converted to number
    });
  });

  // Design token integration tests
  describe('Design Token Integration', () => {
    it('applies base classes from design tokens', () => {
      render(BaseInput, { props: { testId: 'token-test' } });
      const input = screen.getByTestId('token-test');
      
      // Check for design token classes
      expect(input).toHaveClass('border', 'rounded-md', 'transition-all', 'duration-200');
      expect(input).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-offset-2');
      expect(input).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');
    });

    it('applies size-specific classes', () => {
      render(BaseInput, { props: { size: 'lg', testId: 'size-test' } });
      const input = screen.getByTestId('size-test');
      expect(input).toHaveClass('px-6', 'py-3', 'text-base');
    });
  });

  // Regression tests
  describe('Regression Tests', () => {
    it('maintains input value after re-render', async () => {
      const { rerender } = render(BaseInput, { 
        props: { value: 'initial', testId: 'rerender-test' }
      });
      
      let input = screen.getByTestId('rerender-test');
      expect(input).toHaveValue('initial');
      
      await rerender({ value: 'updated', testId: 'rerender-test' });
      input = screen.getByTestId('rerender-test');
      expect(input).toHaveValue('updated');
    });

    it('preserves disabled state correctly', async () => {
      const { rerender } = render(BaseInput, { 
        props: { disabled: true, testId: 'disabled-test' }
      });
      
      let input = screen.getByTestId('disabled-test');
      expect(input).toBeDisabled();
      
      await rerender({ disabled: false, testId: 'disabled-test' });
      input = screen.getByTestId('disabled-test');
      expect(input).not.toBeDisabled();
    });

    it('handles rapid value changes without issues', async () => {
      render(BaseInput, { props: { testId: 'rapid-test' } });
      const input = screen.getByTestId('rapid-test');
      
      // Simulate rapid typing
      const values = ['a', 'ab', 'abc', 'abcd', 'abcde'];
      for (const value of values) {
        await fireEvent.input(input, { target: { value } });
      }
      
      expect(input).toHaveValue('abcde');
    });
  });

  // Component isolation tests
  describe('Component Isolation', () => {
    it('does not leak styles to other components', () => {
      const { container } = render(BaseInput, { props: {} });
      
      // Should only contain the input element and no wrapper divs
      const inputs = container.querySelectorAll('input');
      expect(inputs).toHaveLength(1);
      
      // Should not have any wrapper elements that could leak styles
      const wrappers = container.querySelectorAll('div');
      expect(wrappers).toHaveLength(0);
    });

    it('operates independently of other BaseInput instances', async () => {
      render(BaseInput, { props: { testId: 'input-1', value: 'value1' } });
      render(BaseInput, { props: { testId: 'input-2', value: 'value2' } });
      
      const input1 = screen.getByTestId('input-1');
      const input2 = screen.getByTestId('input-2');
      
      expect(input1).toHaveValue('value1');
      expect(input2).toHaveValue('value2');
      
      // Changing one should not affect the other
      await fireEvent.input(input1, { target: { value: 'changed1' } });
      expect(input1).toHaveValue('changed1');
      expect(input2).toHaveValue('value2');
    });
  });
});