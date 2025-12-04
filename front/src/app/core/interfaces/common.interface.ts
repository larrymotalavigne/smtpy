/**
 * Standard API response wrapper used by auth, billing, and statistics endpoints
 */
export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    message?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface PaginationParams {
    page?: number;
    page_size?: number;
    size?: number;  // Alias for page_size (for backward compatibility)
    sort?: string;
    order?: 'asc' | 'desc';
}

export interface BaseTimestamp {
    created_at: string;
    updated_at: string;
}

export interface SelectOption {
    label: string;
    value: any;
    disabled?: boolean;
}

export interface TableColumn {
    field: string;
    header: string;
    sortable?: boolean;
    width?: string;
    type?: 'text' | 'date' | 'number' | 'boolean' | 'badge' | 'actions';
}

export interface FilterOption {
    field: string;
    operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'startsWith' | 'endsWith';
    value: any;
}
