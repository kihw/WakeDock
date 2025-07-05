import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { expect, describe, it, vi } from 'vitest';
import Input from '../Input.svelte';

describe('Input Component', () => {
    it('renders with default props', () => {
        const { container } = render(Input, {});
        const input = container.querySelector('input');
        expect(input).toBeInTheDocument();
        expect(input).toHaveAttribute('type', 'text');
    });

    it('applies correct input type', () => {
        const { container } = render(Input, {
            props: {
                type: 'email'
            }
        });
        const input = container.querySelector('input');
        expect(input).toHaveAttribute('type', 'email');
    });

    it('handles value binding', async () => {
        const { container, component } = render(Input, {
            props: {
                value: 'initial value'
            }
        });

        const input = container.querySelector('input') as HTMLInputElement;
        expect(input.value).toBe('initial value');

        // Test two-way binding
        await fireEvent.input(input, { target: { value: 'new value' } });
        expect(input.value).toBe('new value');
    });

    it('renders label when provided', () => {
        const { container } = render(Input, {
            props: {
                label: 'Test Label',
                id: 'test-input'
            }
        });

        const label = container.querySelector('label');
        expect(label).toBeInTheDocument();
        expect(label).toHaveTextContent('Test Label');
        expect(label).toHaveAttribute('for', 'test-input');
    });

    it('shows required indicator', () => {
        const { container } = render(Input, {
            props: {
                label: 'Required Field',
                required: true
            }
        });

        const requiredIndicator = container.querySelector('.text-red-500');
        expect(requiredIndicator).toBeInTheDocument();
        expect(requiredIndicator).toHaveTextContent('*');
    });

    it('displays helper text', () => {
        const { container } = render(Input, {
            props: {
                helperText: 'This is helper text'
            }
        });

        const helperText = container.querySelector('.text-gray-600');
        expect(helperText).toBeInTheDocument();
        expect(helperText).toHaveTextContent('This is helper text');
    });

    it('displays error text', () => {
        const { container } = render(Input, {
            props: {
                errorText: 'This is an error',
                variant: 'error'
            }
        });

        const errorText = container.querySelector('.text-red-600');
        expect(errorText).toBeInTheDocument();
        expect(errorText).toHaveTextContent('This is an error');
    });

    it('applies disabled state', () => {
        const { container } = render(Input, {
            props: {
                disabled: true
            }
        });

        const input = container.querySelector('input');
        expect(input).toBeDisabled();
        expect(input).toHaveClass('disabled:cursor-not-allowed');
    });

    it('applies readonly state', () => {
        const { container } = render(Input, {
            props: {
                readonly: true
            }
        });

        const input = container.querySelector('input');
        expect(input).toHaveAttribute('readonly');
    });

    it('shows clear button when clearable and has value', () => {
        const { container } = render(Input, {
            props: {
                clearable: true,
                value: 'some text'
            }
        });

        const clearButton = container.querySelector('button[aria-label="Clear input"]');
        expect(clearButton).toBeInTheDocument();
    });

    it('clears value when clear button is clicked', async () => {
        const { container, component } = render(Input, {
            props: {
                clearable: true,
                value: 'some text'
            }
        });

        const clearButton = container.querySelector('button[aria-label="Clear input"]');
        const input = container.querySelector('input') as HTMLInputElement;

        expect(input.value).toBe('some text');

        await fireEvent.click(clearButton!);
        expect(input.value).toBe('');
    });

    it('shows password toggle for password input', () => {
        const { container } = render(Input, {
            props: {
                type: 'password',
                showPasswordToggle: true,
                value: 'password'
            }
        });

        const toggleButton = container.querySelector('button[aria-label*="password"]');
        expect(toggleButton).toBeInTheDocument();
    });

    it('toggles password visibility', async () => {
        const { container } = render(Input, {
            props: {
                type: 'password',
                showPasswordToggle: true,
                value: 'password'
            }
        });

        let input = container.querySelector('input');
        const toggleButton = container.querySelector('button[aria-label*="password"]');

        expect(input).toHaveAttribute('type', 'password');

        await fireEvent.click(toggleButton!);
        input = container.querySelector('input'); // Re-query after toggle
        expect(input).toHaveAttribute('type', 'text');

        await fireEvent.click(toggleButton!);
        input = container.querySelector('input'); // Re-query after toggle
        expect(input).toHaveAttribute('type', 'password');
    });

    it('applies variant styles', () => {
        const { container } = render(Input, {
            props: {
                variant: 'error'
            }
        });

        const input = container.querySelector('input');
        expect(input).toHaveClass('border-red-500');
    });

    it('applies size styles', () => {
        const { container } = render(Input, {
            props: {
                size: 'lg'
            }
        });

        const input = container.querySelector('input');
        expect(input).toHaveClass('px-4', 'py-3', 'text-base');
    });

    it('supports full width', () => {
        const { container } = render(Input, {
            props: {
                fullWidth: true
            }
        });

        const wrapper = container.querySelector('.relative');
        expect(wrapper).toHaveClass('w-full');
    });

    it('dispatches input events', async () => {
        const handleInput = vi.fn();
        const { container, component } = render(Input, {});

        component.$on('input', handleInput);

        const input = container.querySelector('input');
        await fireEvent.input(input!, { target: { value: 'test' } });

        expect(handleInput).toHaveBeenCalled();
    });

    it('dispatches focus and blur events', async () => {
        const handleFocus = vi.fn();
        const handleBlur = vi.fn();
        const { container, component } = render(Input, {});

        component.$on('focus', handleFocus);
        component.$on('blur', handleBlur);

        const input = container.querySelector('input');

        await fireEvent.focus(input!);
        expect(handleFocus).toHaveBeenCalled();

        await fireEvent.blur(input!);
        expect(handleBlur).toHaveBeenCalled();
    });

    it('applies accessibility attributes', () => {
        const { container } = render(Input, {
            props: {
                ariaLabel: 'Custom label',
                ariaDescribedBy: 'helper-text',
                id: 'test-input'
            }
        });

        const input = container.querySelector('input');
        expect(input).toHaveAttribute('aria-label', 'Custom label');
        expect(input?.getAttribute('aria-describedby')).toContain('helper-text');
        expect(input).toHaveAttribute('id', 'test-input');
    });
});
