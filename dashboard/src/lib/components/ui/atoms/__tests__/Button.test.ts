import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { expect, describe, it, vi } from 'vitest';
import Button from '../Button.svelte';

describe('Button Component', () => {
    it('renders with default props', () => {
        const { container } = render(Button, {});
        const button = container.querySelector('button');
        expect(button).toBeInTheDocument();
    });

    it('applies correct variant classes', () => {
        const { container } = render(Button, {
            props: {
                variant: 'primary'
            }
        });
        const button = container.querySelector('button');
        expect(button).toHaveClass('bg-blue-600');
    });

    it('handles click events', async () => {
        const handleClick = vi.fn();
        const { component } = render(Button, {
            props: {}
        });

        component.$on('click', handleClick);

        const button = screen.getByRole('button');
        await fireEvent.click(button);

        expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('renders in disabled state', () => {
        const { container } = render(Button, {
            props: {
                disabled: true
            }
        });

        const button = container.querySelector('button');
        expect(button).toBeDisabled();
    });

    it('renders loading state', () => {
        const { container } = render(Button, {
            props: {
                loading: true
            }
        });

        const button = container.querySelector('button');
        expect(button).toHaveClass('bg-blue-300', 'text-blue-100');
    });

    it('supports different sizes', () => {
        const { container } = render(Button, {
            props: {
                size: 'lg'
            }
        });

        const button = container.querySelector('button');
        expect(button).toHaveClass('px-6', 'py-3', 'text-base');
    });

    it('renders as link when href is provided', () => {
        const { container } = render(Button, {
            props: {
                href: '/test'
            }
        });

        const link = container.querySelector('a');
        expect(link).toHaveAttribute('href', '/test');
    });

    it('supports keyboard navigation', async () => {
        const handleKeyDown = vi.fn();
        const { component, container } = render(Button, {
            props: {}
        });

        component.$on('keydown', handleKeyDown);

        const button = container.querySelector('button');
        button?.focus();

        await fireEvent.keyDown(button!, { key: 'Enter' });
        expect(handleKeyDown).toHaveBeenCalled();
    });

    it('applies custom test id', () => {
        const { container } = render(Button, {
            props: {
                testId: 'custom-button'
            }
        });

        const button = container.querySelector('[data-testid="custom-button"]');
        expect(button).toBeInTheDocument();
    });

    it('supports left icon', () => {
        const { container } = render(Button, {
            props: {
                leftIcon: 'icon-plus'
            }
        });

        const icon = container.querySelector('.icon-plus');
        expect(icon).toBeInTheDocument();
    });

    it('handles full width prop', () => {
        const { container } = render(Button, {
            props: {
                fullWidth: true
            }
        });

        const button = container.querySelector('button');
        expect(button).toHaveClass('w-full');
    });
});
