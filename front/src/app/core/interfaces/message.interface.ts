export enum MessageStatus {
    PENDING = 'pending',
    DELIVERED = 'delivered',
    FAILED = 'failed',
    BOUNCED = 'bounced'
}

export interface MessageResponse {
    id: number;
    message_id: string;
    thread_id?: string;

    // Domain relationship
    domain_id: number;

    // Email addresses
    sender_email: string;
    recipient_email: string;
    forwarded_to?: string;

    // Message content
    subject?: string;
    body_preview?: string;

    // Processing status
    status: MessageStatus;
    error_message?: string;

    // Message size and attachments
    size_bytes?: number;
    has_attachments: boolean;

    // Timestamps
    created_at: string;
    updated_at: string;
}

export interface MessageList {
    id: number;
    message_id: string;
    sender_email: string;
    recipient_email: string;
    subject?: string;
    status: MessageStatus;
    size_bytes?: number;
    has_attachments: boolean;
    created_at: string;
    updated_at: string;
}

export interface MessageStats {
    total_messages: number;
    delivered_messages: number;
    failed_messages: number;
    pending_messages: number;
    total_size_bytes: number;
    delivery_rate: number;
}

export interface MessageFilter {
    domain_id?: number;
    status?: MessageStatus;
    sender_email?: string;
    recipient_email?: string;
    has_attachments?: boolean;
    date_from?: string;
    date_to?: string;
}
