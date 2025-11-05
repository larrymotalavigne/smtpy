import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  CheckoutSessionRequest,
  CheckoutSessionResponse,
  CustomerPortalResponse,
  SubscriptionResponse,
  SubscriptionUpdateRequest,
  BillingStats,
  PlanInfo,
  OrganizationBilling
} from '../../core/interfaces/billing.interface';
import { ApiResponse } from '../../core/interfaces/common.interface';

@Injectable({
  providedIn: 'root'
})
export class BillingApiService {
  private apiUrl = `${environment.apiUrl}/billing`;

  constructor(private http: HttpClient) {}

  /**
   * Create a Stripe checkout session
   */
  createCheckoutSession(request: CheckoutSessionRequest): Observable<ApiResponse<CheckoutSessionResponse>> {
    return this.http.post<ApiResponse<CheckoutSessionResponse>>(`${this.apiUrl}/checkout-session`, request);
  }

  /**
   * Create a customer portal session
   */
  createCustomerPortal(returnUrl?: string): Observable<ApiResponse<CustomerPortalResponse>> {
    const body = returnUrl ? { return_url: returnUrl } : {};
    return this.http.get<ApiResponse<CustomerPortalResponse>>(`${this.apiUrl}/customer-portal`);
  }

  /**
   * Get current subscription information
   */
  getSubscription(): Observable<ApiResponse<SubscriptionResponse>> {
    return this.http.get<ApiResponse<SubscriptionResponse>>(`${this.apiUrl}/subscription`);
  }

  /**
   * Update subscription settings
   */
  updateSubscription(update: SubscriptionUpdateRequest): Observable<ApiResponse<SubscriptionResponse>> {
    return this.http.patch<ApiResponse<SubscriptionResponse>>(`${this.apiUrl}/subscription`, update);
  }

  /**
   * Cancel subscription (set to cancel at period end)
   */
  cancelSubscription(): Observable<ApiResponse<SubscriptionResponse>> {
    return this.http.post<ApiResponse<SubscriptionResponse>>(`${this.apiUrl}/subscription/cancel`, {});
  }

  /**
   * Reactivate subscription (remove cancel at period end)
   */
  reactivateSubscription(): Observable<ApiResponse<SubscriptionResponse>> {
    return this.http.post<ApiResponse<SubscriptionResponse>>(`${this.apiUrl}/subscription/reactivate`, {});
  }

  /**
   * Get available plans
   */
  getPlans(): Observable<ApiResponse<PlanInfo[]>> {
    return this.http.get<ApiResponse<PlanInfo[]>>(`${this.apiUrl}/plans`);
  }

  /**
   * Get a specific plan by price ID
   */
  getPlan(priceId: string): Observable<ApiResponse<PlanInfo>> {
    const params = new HttpParams().set('price_id', priceId);
    return this.http.get<ApiResponse<PlanInfo>>(`${this.apiUrl}/plan`, { params });
  }

  /**
   * Get organization billing information
   */
  getOrganizationBilling(): Observable<ApiResponse<OrganizationBilling>> {
    return this.http.get<ApiResponse<OrganizationBilling>>(`${this.apiUrl}/organization`);
  }

  /**
   * Update organization billing email
   */
  updateBillingEmail(email: string): Observable<ApiResponse<OrganizationBilling>> {
    return this.http.patch<ApiResponse<OrganizationBilling>>(`${this.apiUrl}/organization`, { 
      billing_email: email 
    });
  }

  /**
   * Get billing statistics (admin only)
   */
  getBillingStats(): Observable<ApiResponse<BillingStats>> {
    return this.http.get<ApiResponse<BillingStats>>(`${this.apiUrl}/stats`);
  }

  /**
   * Handle successful payment callback
   */
  handlePaymentSuccess(sessionId: string): Observable<ApiResponse<{ success: boolean; subscription?: SubscriptionResponse }>> {
    return this.http.post<ApiResponse<{ success: boolean; subscription?: SubscriptionResponse }>>(
      `${this.apiUrl}/payment-success`, 
      { session_id: sessionId }
    );
  }

  /**
   * Get invoice history
   */
  getInvoices(): Observable<ApiResponse<{
    id: string;
    number: string;
    status: string;
    amount_paid: number;
    currency: string;
    created: number;
    invoice_pdf?: string;
    hosted_invoice_url?: string;
  }[]>> {
    return this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/invoices`);
  }

  /**
   * Download invoice PDF
   */
  downloadInvoice(invoiceId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/invoices/${invoiceId}/pdf`, {
      responseType: 'blob'
    });
  }

  /**
   * Check if organization is approaching limits
   */
  checkUsageLimits(): Observable<ApiResponse<{
    domains_usage: { current: number; limit?: number; percentage?: number };
    messages_usage: { current: number; limit?: number; percentage?: number };
    approaching_limits: boolean;
    needs_upgrade: boolean;
  }>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/usage-limits`);
  }

  /**
   * Get recommended plan based on usage
   */
  getRecommendedPlan(): Observable<ApiResponse<{
    current_plan?: PlanInfo;
    recommended_plan?: PlanInfo;
    reason?: string;
    savings?: number;
  }>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/recommended-plan`);
  }

  /**
   * Validate promo code
   */
  validatePromoCode(code: string): Observable<ApiResponse<{
    valid: boolean;
    discount_percentage?: number;
    discount_amount?: number;
    expires_at?: string;
    description?: string;
  }>> {
    const params = new HttpParams().set('code', code);
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/validate-promo-code`, { params });
  }
}