import { render } from '@testing-library/svelte';
import { expect, describe, it } from 'vitest';
import DataTable from '../../molecules/DataTable.svelte';

describe('DataTable Component', () => {
    const mockColumns = [
        { key: 'name', label: 'Name', sortable: true },
        { key: 'email', label: 'Email', sortable: true },
        { key: 'role', label: 'Role', sortable: false }
    ];

    const mockData = [
        { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'User' },
        { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'Editor' }
    ];

    it('renders with default props', () => {
        const { container } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: mockData
            }
        });
        const table = container.querySelector('table');
        expect(table).toBeInTheDocument();
    });

    it('displays column headers correctly', () => {
        const { getByText } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: mockData
            }
        });

        expect(getByText('Name')).toBeInTheDocument();
        expect(getByText('Email')).toBeInTheDocument();
        expect(getByText('Role')).toBeInTheDocument();
    });

    it('displays data rows correctly', () => {
        const { getByText } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: mockData
            }
        });

        expect(getByText('John Doe')).toBeInTheDocument();
        expect(getByText('john@example.com')).toBeInTheDocument();
        expect(getByText('Admin')).toBeInTheDocument();
    });

    it('shows loading state when loading prop is true', () => {
        const { container } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: [],
                loading: true
            }
        });

        const loadingIndicator = container.querySelector('.animate-spin');
        expect(loadingIndicator).toBeInTheDocument();
    });

    it('shows empty state when no data is provided', () => {
        const { getByText } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: [],
                emptyMessage: 'No data available'
            }
        });

        expect(getByText('No data available')).toBeInTheDocument();
    });

    it('applies striped styling when striped prop is true', () => {
        const { container } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: mockData,
                striped: true
            }
        });

        const rows = container.querySelectorAll('tbody tr');
        expect(rows.length).toBeGreaterThan(1);
        // Check that the second row has striped styling
        expect(rows[1]).toHaveClass('bg-gray-50');
    });

    it('applies hover effect when hoverable prop is true', () => {
        const { container } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: mockData,
                hoverable: true
            }
        });

        const rows = container.querySelectorAll('tbody tr');
        expect(rows.length).toBeGreaterThan(0);
        // Check that rows have hover classes
        expect(rows[0]).toHaveClass('hover:bg-gray-50');
    });

    it('shows sortable indicators for sortable columns', () => {
        const { container } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: mockData
            }
        });

        const sortableHeaders = container.querySelectorAll('[aria-sort]');
        expect(sortableHeaders.length).toBeGreaterThan(0);
    });

    it('applies test id when provided', () => {
        const { container } = render(DataTable, {
            props: {
                columns: mockColumns,
                data: mockData,
                testId: 'test-data-table'
            }
        });

        const dataTable = container.querySelector('[data-testid="test-data-table"]');
        expect(dataTable).toHaveAttribute('data-testid', 'test-data-table');
    });
});
