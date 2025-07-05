import { render } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import Toast from '../Toast.svelte';

describe('Toast Component', () => {
    it('renders with default props', () => {
        const { container } = render(Toast);
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toBeInTheDocument();
    });

    it('applies correct variant classes', () => {
        const { container } = render(Toast, {
            props: {
                variant: 'success'
            }
        });
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toHaveClass('bg-green-50', 'border-green-200');
    });

    it('applies error variant correctly', () => {
        const { container } = render(Toast, {
            props: {
                variant: 'error'
            }
        });
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toHaveClass('bg-red-50', 'border-red-200');
    });

    it('applies warning variant correctly', () => {
        const { container } = render(Toast, {
            props: {
                variant: 'warning'
            }
        });
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toHaveClass('bg-yellow-50', 'border-yellow-200');
    });

    it('applies info variant correctly', () => {
        const { container } = render(Toast, {
            props: {
                variant: 'info'
            }
        });
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toHaveClass('bg-blue-50', 'border-blue-200');
    });

    it('displays title when provided', () => {
        const { getByText } = render(Toast, {
            props: {
                title: 'Test Title'
            }
        });
        expect(getByText('Test Title')).toBeInTheDocument();
    });

    it('displays message when provided', () => {
        const { getByText } = render(Toast, {
            props: {
                message: 'Test message'
            }
        });
        expect(getByText('Test message')).toBeInTheDocument();
    });

    it('shows close button when dismissible is true', () => {
        const { container } = render(Toast, {
            props: {
                dismissible: true
            }
        });
        const closeButton = container.querySelector('[aria-label="Dismiss"]');
        expect(closeButton).toBeInTheDocument();
    });

    it('applies test id when provided', () => {
        const { container } = render(Toast, {
            props: {
                testId: 'test-toast'
            }
        });
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toHaveAttribute('data-testid', 'test-toast');
    });

    it('applies correct aria attributes', () => {
        const { container } = render(Toast, {
            props: {
                variant: 'error'
            }
        });
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toHaveAttribute('role', 'alert');
        expect(toast).toHaveAttribute('aria-live', 'assertive');
    });

    it('applies auto-dismiss behavior when autoDismiss prop is true', () => {
        const { container } = render(Toast, {
            props: {
                autoDismiss: true,
                duration: 1000
            }
        });
        const toast = container.querySelector('.fixed.z-50');
        expect(toast).toBeInTheDocument();
        // Auto-dismiss behavior would need to be tested with timers
    });
});
