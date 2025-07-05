import { render } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import FormField from '../../molecules/FormField.svelte';

describe('FormField Component', () => {
    it('renders with default props', () => {
        const { container } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field'
            }
        });
        const field = container.querySelector('.form-field');
        expect(field).toBeInTheDocument();
    });

    it('displays label when provided', () => {
        const { getByText } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Label'
            }
        });
        expect(getByText('Test Label')).toBeInTheDocument();
    });

    it('displays error message when errorText prop is provided', () => {
        const { getByText } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field',
                errorText: 'This field is required'
            }
        });
        expect(getByText('This field is required')).toBeInTheDocument();
    });

    it('displays help text when provided', () => {
        const { getByText } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field',
                helpText: 'This is help text'
            }
        });
        expect(getByText('This is help text')).toBeInTheDocument();
    });

    it('shows required indicator when required prop is true', () => {
        const { container } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Required Field',
                required: true
            }
        });
        const requiredIndicator = container.querySelector('.text-red-500');
        expect(requiredIndicator).toBeInTheDocument();
    });

    it('applies error styling when errorText prop is provided', () => {
        const { container } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field',
                errorText: 'Error message'
            }
        });
        const errorElement = container.querySelector('.text-red-600');
        expect(errorElement).toBeInTheDocument();
    });

    it('applies disabled styling when disabled prop is true', () => {
        const { container } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field',
                disabled: true
            }
        });
        const input = container.querySelector('input');
        expect(input).toHaveAttribute('disabled');
        expect(input).toHaveClass('disabled:cursor-not-allowed', 'disabled:bg-gray-50');
    });

    it('applies correct size classes', () => {
        const { container } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field',
                size: 'sm'
            }
        });
        const input = container.querySelector('input');
        expect(input).toHaveClass('text-sm');
    });

    it('applies large size classes correctly', () => {
        const { container } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field',
                size: 'lg'
            }
        });
        const input = container.querySelector('input');
        expect(input).toHaveClass('text-base');
    });

    it('applies test id when provided', () => {
        const { container } = render(FormField, {
            props: {
                name: 'test-field',
                label: 'Test Field',
                testId: 'test-form-field'
            }
        });
        const field = container.querySelector('.form-field');
        expect(field).toHaveAttribute('data-testid', 'test-form-field');
    });
});
