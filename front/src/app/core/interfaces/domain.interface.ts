export enum DomainStatus {
    PENDING = 'pending',
    VERIFIED = 'verified',
    FAILED = 'failed'
}

export interface DomainCreate {
    name: string;
}

export interface DomainUpdate {
    is_active?: boolean;
}

export interface DNSVerificationStatus {
    mx_record_verified: boolean;
    spf_record_verified: boolean;
    dkim_record_verified: boolean;
    dmarc_record_verified: boolean;
    is_fully_verified: boolean;
}

export interface DomainResponse {
    id: number;
    name: string;
    organization_id: number;
    status: DomainStatus;
    is_active: boolean;
    success: boolean;

    // DNS verification status
    mx_record_verified: boolean;
    spf_record_verified: boolean;
    dkim_record_verified: boolean;
    dmarc_record_verified: boolean;

    // DNS record values
    dkim_public_key?: string;
    verification_token?: string;

    // Timestamps
    created_at: string;
    updated_at: string;

    // Computed property
    is_fully_verified: boolean;
}

export interface DomainList {
    id: number;
    name: string;
    status: DomainStatus;
    is_active: boolean;
    is_fully_verified: boolean;
    created_at: string;
    updated_at: string;
}

export interface DomainVerificationResponse {
    success: boolean;
    message: string;
    dns_status: DNSVerificationStatus;
}

export interface DNSRecords {
    mx_record: string;
    spf_record: string;
    dkim_record: string;
    dmarc_record: string;
    verification_record?: string;
}

export interface DKIMRegenerationResponse {
    success: boolean;
    message: string;
    dkim_public_key: string;
    dkim_selector: string;
    dkim_dns_hostname: string;
    dkim_dns_value: string;
}
