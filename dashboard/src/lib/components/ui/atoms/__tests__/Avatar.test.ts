import { render } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import Avatar from '../Avatar.svelte';

describe('Avatar Component', () => {
    it('renders with default props', () => {
        const { container } = render(Avatar);
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toBeInTheDocument();
    });

    it('displays image when src is provided', () => {
        const { container } = render(Avatar, {
            props: {
                src: 'https://example.com/avatar.jpg',
                alt: 'User Avatar'
            }
        });
        const image = container.querySelector('img');
        expect(image).toBeInTheDocument();
        expect(image).toHaveAttribute('src', 'https://example.com/avatar.jpg');
        expect(image).toHaveAttribute('alt', 'User Avatar');
    });

    it('displays initials when name is provided and no src', () => {
        const { getByText } = render(Avatar, {
            props: {
                name: 'John Doe'
            }
        });
        expect(getByText('JD')).toBeInTheDocument();
    });

    it('applies correct size classes', () => {
        const { container } = render(Avatar, {
            props: {
                size: 'sm'
            }
        });
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toHaveClass('w-8', 'h-8');
    });

    it('applies large size classes correctly', () => {
        const { container } = render(Avatar, {
            props: {
                size: 'lg'
            }
        });
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toHaveClass('w-12', 'h-12');
    });

    it('applies square variant when variant is square', () => {
        const { container } = render(Avatar, {
            props: {
                variant: 'square'
            }
        });
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toHaveClass('rounded-none');
    });

    it('applies circular variant by default', () => {
        const { container } = render(Avatar, {
            props: {
                variant: 'circle'
            }
        });
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toHaveClass('rounded-full');
    });

    it('shows status indicator when status is provided', () => {
        const { container } = render(Avatar, {
            props: {
                status: 'online'
            }
        });
        const statusIndicator = container.querySelector('[class*="bg-green-400"]');
        expect(statusIndicator).toBeInTheDocument();
        expect(statusIndicator).toHaveClass('bg-green-400');
    });

    it('applies clickable styles when clickable prop is true', () => {
        const { container } = render(Avatar, {
            props: {
                clickable: true
            }
        });
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toHaveClass('cursor-pointer');
    });

    it('applies test id when provided', () => {
        const { container } = render(Avatar, {
            props: {
                testId: 'test-avatar'
            }
        });
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toHaveAttribute('data-testid', 'test-avatar');
    });

    it('shows fallback icon when no src or name provided', () => {
        const { container } = render(Avatar);
        const fallbackIcon = container.querySelector('svg');
        expect(fallbackIcon).toBeInTheDocument();
    });

    it('applies border when border prop is true', () => {
        const { container } = render(Avatar, {
            props: {
                border: true
            }
        });
        const avatar = container.querySelector('.relative.inline-flex');
        expect(avatar).toHaveClass('border-2');
    });
});
