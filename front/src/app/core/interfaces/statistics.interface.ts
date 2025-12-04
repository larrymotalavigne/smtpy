/**
 * Statistics interfaces for the SMTPy application
 */

/**
 * Overall usage statistics
 */
export interface OverallStats {
    total_emails: number;
    emails_sent: number;
    emails_failed: number;
    active_domains: number;
    active_aliases: number;
    success_rate: number;
    total_size_mb: number;
}

/**
 * Time series data point
 */
export interface TimeSeriesDataPoint {
    date: string;
    emails_sent: number;
    emails_failed: number;
    success_rate: number;
}

/**
 * Domain statistics
 */
export interface DomainStats {
    domain_id: number;
    domain_name: string;
    email_count: number;
    success_count: number;
    failure_count: number;
    success_rate: number;
    percentage_of_total: number;
}

/**
 * Alias statistics
 */
export interface AliasStats {
    alias_id: number;
    alias_email: string;
    domain_name: string;
    email_count: number;
    last_used: string;
}

/**
 * Statistics filter parameters
 */
export interface StatisticsFilter {
    date_from?: string;
    date_to?: string;
    domain_id?: number;
    granularity?: 'day' | 'week' | 'month';
}

/**
 * Complete statistics response
 */
export interface StatisticsResponse {
    overall: OverallStats;
    time_series: TimeSeriesDataPoint[];
    top_domains: DomainStats[];
    top_aliases: AliasStats[];
    period: {
        start: string;
        end: string;
    };
}

/**
 * Statistics export request
 */
export interface StatisticsExportRequest {
    format: 'csv' | 'json' | 'pdf';
    filter?: StatisticsFilter;
    include_charts?: boolean;
}
