import { render } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import Badge from '../Badge.svelte';

describe('Badge Component', () => {
    it('renders with default props', () => {
        const { container } = render(Badge);
        const badge = container.querySelector('span');
        expect(badge).toBeInTheDocument();
    });

    it('applies correct variant classes', () => {
        const { container } = render(Badge, {
            props: {
                variant: 'success'
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('applies error variant correctly', () => {
        const { container } = render(Badge, {
            props: {
                variant: 'error'
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('applies warning variant correctly', () => {
        const { container } = render(Badge, {
            props: {
                variant: 'warning'
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('applies size classes correctly', () => {
        const { container } = render(Badge, {
            props: {
                size: 'sm'
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs');
    });

    it('applies rounded classes when rounded prop is true', () => {
        const { container } = render(Badge, {
            props: {
                rounded: true
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('rounded-full');
    });

    it('applies outlined classes when outlined prop is true', () => {
        const { container } = render(Badge, {
            props: {
                outlined: true,
                variant: 'primary'
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('border-2', 'bg-transparent');
    });

    it('applies clickable classes when clickable prop is true', () => {
        const { container } = render(Badge, {
            props: {
                clickable: true
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('cursor-pointer');
    });

    it('renders as anchor when href is provided', () => {
        const { container } = render(Badge, {
            props: {
                href: 'https://example.com'
            }
        });
        const link = container.querySelector('a');
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute('href', 'https://example.com');
    });

    it('applies test id when provided', () => {
        const { container } = render(Badge, {
            props: {
                testId: 'test-badge'
            }
        });
        const badge = container.querySelector('span');
        expect(badge).toHaveAttribute('data-testid', 'test-badge');
    });
});