import { render, fireEvent } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import SearchInput from '../../molecules/SearchInput.svelte';

describe('SearchInput Component', () => {
    it('renders with default props', () => {
        const { container } = render(SearchInput);
        const input = container.querySelector('input[type="search"]');
        expect(input).toBeInTheDocument();
    });

    it('applies placeholder text correctly', () => {
        const { container } = render(SearchInput, {
            props: {
                placeholder: 'Search items...'
            }
        });
        const input = container.querySelector('input');
        expect(input).toHaveAttribute('placeholder', 'Search items...');
    });

    it('applies value correctly', () => {
        const { container } = render(SearchInput, {
            props: {
                value: 'test search'
            }
        });
        const input = container.querySelector('input');
        expect(input).toHaveValue('test search');
    });

    it('applies disabled state correctly', () => {
        const { container } = render(SearchInput, {
            props: {
                disabled: true
            }
        });
        const input = container.querySelector('input');
        expect(input).toBeDisabled();
    });

    it('shows loading state correctly', () => {
        const { container } = render(SearchInput, {
            props: {
                loading: true
            }
        });
        const spinner = container.querySelector('.animate-spin');
        expect(spinner).toBeInTheDocument();
    });

    it('shows search icon when not loading', () => {
        const { container } = render(SearchInput, {
            props: {
                loading: false
            }
        });
        const searchIcon = container.querySelector('i.fas.fa-search');
        expect(searchIcon).toBeInTheDocument();
    });

    it('shows clear button when value is present and clearable', () => {
        const { container } = render(SearchInput, {
            props: {
                value: 'test',
                clearable: true
            }
        });
        const clearButton = container.querySelector('button[aria-label="Clear search"]');
        expect(clearButton).toBeInTheDocument();
    });

    it('handles input changes correctly', async () => {
        const { container } = render(SearchInput);
        const input = container.querySelector('input');

        if (input) {
            await fireEvent.input(input, { target: { value: 'new search' } });
            expect(input).toHaveValue('new search');
        }
    });

    it('handles clear button click', async () => {
        const { container } = render(SearchInput, {
            props: {
                value: 'test',
                clearable: true
            }
        });

        const clearButton = container.querySelector('[aria-label="Clear search"]');
        if (clearButton) {
            await fireEvent.click(clearButton);

            const input = container.querySelector('input');
            expect(input).toHaveValue('');
        }
    });

    it('applies test id when provided', () => {
        const { container } = render(SearchInput, {
            props: {
                testId: 'test-search-input'
            }
        });
        const input = container.querySelector('input');
        expect(input).toHaveAttribute('data-testid', 'test-search-input');
    });
});
