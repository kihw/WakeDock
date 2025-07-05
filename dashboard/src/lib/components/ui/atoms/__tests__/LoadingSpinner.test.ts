import { render } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import LoadingSpinner from '../LoadingSpinner.svelte';

describe('LoadingSpinner Component', () => {
    it('renders with default props', () => {
        const { container } = render(LoadingSpinner);
        const spinner = container.querySelector('.animate-spin');
        expect(spinner).toBeInTheDocument();
    });

    it('applies correct size classes', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                size: 'sm'
            }
        });
        const spinner = container.querySelector('.animate-spin');
        expect(spinner).toHaveClass('w-5', 'h-5');
    });

    it('applies large size classes correctly', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                size: 'lg'
            }
        });
        const spinner = container.querySelector('.animate-spin');
        expect(spinner).toHaveClass('w-8', 'h-8');
    });

    it('applies correct variant classes', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                variant: 'error'
            }
        });
        const spinner = container.querySelector('.animate-spin');
        expect(spinner).toHaveClass('text-red-600');
    });

    it('applies test id when provided', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                testId: 'test-spinner'
            }
        });
        const spinnerContainer = container.querySelector('[data-testid="test-spinner"]');
        expect(spinnerContainer).toHaveAttribute('data-testid', 'test-spinner');
    });

    it('displays loading text when provided', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                label: 'Loading...',
                showLabel: true
            }
        });
        const labelElement = container.querySelector('.text-base');
        expect(labelElement).toBeInTheDocument();
        expect(labelElement).toHaveTextContent('Loading...');
    });

    it('applies correct aria attributes', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                label: 'Loading data'
            }
        });
        const spinnerContainer = container.querySelector('[role="status"]');
        expect(spinnerContainer).toHaveAttribute('role', 'status');
        expect(spinnerContainer).toHaveAttribute('aria-label', 'Loading data');
    });

    it('applies fullscreen styles when fullScreen prop is true', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                fullScreen: true
            }
        });
        const wrapper = container.querySelector('.fixed');
        expect(wrapper).toBeInTheDocument();
        expect(wrapper).toHaveClass('inset-0');
    });
});
