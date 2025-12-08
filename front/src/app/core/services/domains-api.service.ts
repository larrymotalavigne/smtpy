import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  DomainResponse,
  DomainList,
  DomainCreate,
  DomainUpdate,
  DomainVerificationResponse,
  DNSRecords,
  DKIMRegenerationResponse
} from '../../core/interfaces/domain.interface';
import {
  PaginatedResponse,
  PaginationParams
} from '../../core/interfaces/common.interface';

@Injectable({
  providedIn: 'root'
})
export class DomainsApiService {
  private apiUrl = `${environment.apiUrl}/domains`;

  constructor(private http: HttpClient) {}

  /**
   * Create a new domain
   */
  createDomain(domain: DomainCreate): Observable<DomainResponse> {
    return this.http.post<DomainResponse>(this.apiUrl, domain);
  }

  /**
   * Get paginated list of domains
   */
  getDomains(params?: PaginationParams): Observable<PaginatedResponse<DomainList>> {
    let httpParams = new HttpParams();

    if (params?.page) {
      httpParams = httpParams.set('page', params.page.toString());
    }
    if (params?.size) {
      httpParams = httpParams.set('size', params.size.toString());
    }
    if (params?.sort) {
      httpParams = httpParams.set('sort', params.sort);
    }
    if (params?.order) {
      httpParams = httpParams.set('order', params.order);
    }

    return this.http.get<PaginatedResponse<DomainList>>(this.apiUrl, { params: httpParams });
  }

  /**
   * Get a specific domain by ID
   */
  getDomain(id: number): Observable<DomainResponse> {
    return this.http.get<DomainResponse>(`${this.apiUrl}/${id}`);
  }

  /**
   * Update a domain
   */
  updateDomain(id: number, update: DomainUpdate): Observable<DomainResponse> {
    return this.http.patch<DomainResponse>(`${this.apiUrl}/${id}`, update);
  }

  /**
   * Delete a domain
   */
  deleteDomain(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  /**
   * Verify domain DNS records
   */
  verifyDomain(id: number): Observable<DomainVerificationResponse> {
    return this.http.post<DomainVerificationResponse>(`${this.apiUrl}/${id}/verify`, {});
  }

  /**
   * Get DNS records for a domain
   */
  getDNSRecords(id: number): Observable<DNSRecords> {
    return this.http.get<DNSRecords>(`${this.apiUrl}/${id}/dns-records`);
  }

  /**
   * Get domains with active status only
   */
  getActiveDomains(): Observable<DomainList[]> {
    const params = new HttpParams().set('active_only', 'true');
    return this.http.get<DomainList[]>(this.apiUrl, { params });
  }

  /**
   * Check domain availability (before creating)
   */
  checkDomainAvailability(domainName: string): Observable<{ available: boolean; reason?: string }> {
    const params = new HttpParams().set('name', domainName);
    return this.http.get<{ available: boolean; reason?: string }>(`${this.apiUrl}/check-availability`, { params });
  }

  /**
   * Get domain statistics
   */
  getDomainStats(id: number): Observable<{
    total_aliases: number;
    active_aliases: number;
    messages_received: number;
    messages_forwarded: number;
    last_message_at?: string;
  }> {
    return this.http.get<any>(`${this.apiUrl}/${id}/stats`);
  }

  /**
   * Regenerate DKIM keys for a domain
   */
  regenerateDKIMKeys(id: number): Observable<DKIMRegenerationResponse> {
    return this.http.post<DKIMRegenerationResponse>(`${this.apiUrl}/${id}/regenerate-dkim-keys`, {});
  }
}
