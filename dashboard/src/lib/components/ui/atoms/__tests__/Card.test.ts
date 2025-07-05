import { render } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import Card from '../Card.svelte';

describe('Card Component', () => {
    it('renders with default props', () => {
        const { container } = render(Card);
        const card = container.querySelector('div');
        expect(card).toBeInTheDocument();
    });

    it('applies correct variant classes', () => {
        const { container } = render(Card, {
            props: {
                variant: 'elevated'
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('shadow-lg');
    });

    it('applies outlined variant correctly', () => {
        const { container } = render(Card, {
            props: {
                variant: 'outlined'
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('border-2', 'border-gray-300');
    });

    it('applies size classes correctly', () => {
        const { container } = render(Card, {
            props: {
                size: 'sm'
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('text-sm');
    });

    it('applies large size classes correctly', () => {
        const { container } = render(Card, {
            props: {
                size: 'lg'
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('text-lg');
    });

    it('applies rounded classes when rounded prop is true', () => {
        const { container } = render(Card, {
            props: {
                rounded: true
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('rounded-2xl');
    });

    it('applies hover effect when hoverable prop is true', () => {
        const { container } = render(Card, {
            props: {
                hoverable: true,
                interactive: true
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('hover:shadow-md');
    });

    it('applies clickable classes when interactive prop is true', () => {
        const { container } = render(Card, {
            props: {
                interactive: true
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('cursor-pointer');
    });

    it('applies test id when provided', () => {
        const { container } = render(Card, {
            props: {
                testId: 'test-card'
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveAttribute('data-testid', 'test-card');
    });

    it('applies full width when fullWidth prop is true', () => {
        const { container } = render(Card, {
            props: {
                fullWidth: true
            }
        });
        const card = container.querySelector('div');
        expect(card).toHaveClass('w-full');
    });
});
