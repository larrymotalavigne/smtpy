export enum SubscriptionStatus {
    ACTIVE = 'active',
    CANCELED = 'canceled',
    INCOMPLETE = 'incomplete',
    INCOMPLETE_EXPIRED = 'incomplete_expired',
    PAST_DUE = 'past_due',
    TRIALING = 'trialing',
    UNPAID = 'unpaid'
}

export interface CheckoutSessionRequest {
    price_id: string;
    success_url?: string;
    cancel_url?: string;
}

export interface CheckoutSessionResponse {
    url: string;
    session_id: string;
}

export interface CustomerPortalResponse {
    url: string;
}

export interface SubscriptionResponse {
    id?: string;
    status?: SubscriptionStatus;
    current_period_end?: string;
    plan_price_id?: string;
    cancel_at_period_end: boolean;

    // Computed fields
    is_active: boolean;
    days_until_renewal?: number;
    is_trial: boolean;
    needs_payment: boolean;
}

export interface SubscriptionUpdateRequest {
    cancel_at_period_end?: boolean;
}

export interface BillingStats {
    total_revenue: number;
    active_subscriptions: number;
    trial_subscriptions: number;
    canceled_subscriptions: number;
    mrr: number;
}

export interface PlanInfo {
    price_id: string;
    name: string;
    description?: string;
    amount: number;
    currency: string;
    interval: string;
    features: string[];
}

export interface OrganizationBilling {
    organization_id: number;
    stripe_customer_id?: string;
    subscription?: SubscriptionResponse;
    billing_email: string;

    // Usage information
    domains_count: number;
    messages_count: number;

    // Plan limits
    plan_domain_limit?: number;
    plan_message_limit?: number;
    approaching_limits: boolean;
}
