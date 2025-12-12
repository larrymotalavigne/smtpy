export interface AliasCreate {
    local_part: string;
    domain_id: number;
    targets: string[];  // Array of email addresses
    expires_at?: string;
}

export interface AliasUpdate {
    targets?: string[];
    expires_at?: string | null;
    is_deleted?: boolean;
}

export interface AliasResponse {
    id: number;
    domain_id: number;
    local_part: string;
    targets: string;  // Comma-separated in backend
    is_deleted: boolean;
    expires_at?: string;
    created_at: string;
    updated_at: string;
    domain_name?: string;
    full_address?: string;
    target_list: string[];
}

export interface AliasListItem {
    id: number;
    local_part: string;
    domain_id: number;
    domain_name?: string;
    full_address?: string;
    target_count: number;
    target_list: string[];
    is_deleted: boolean;
    expires_at?: string;
    created_at: string;
}
