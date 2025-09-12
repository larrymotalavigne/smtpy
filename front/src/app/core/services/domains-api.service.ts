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
  DNSRecords 
} from '../interfaces/domain.interface';
import { 
  PaginatedResponse, 
  PaginationParams, 
  ApiResponse 
} from '../interfaces/common.interface';

@Injectable({
  providedIn: 'root'
})
export class DomainsApiService {
  private apiUrl = `${environment.apiUrl}/domains`;

  constructor(private http: HttpClient) {}

  /**
   * Create a new domain
   */
  createDomain(domain: DomainCreate): Observable<ApiResponse<DomainResponse>> {
    return this.http.post<ApiResponse<DomainResponse>>(this.apiUrl, domain);
  }

  /**
   * Get paginated list of domains
   */
  getDomains(params?: PaginationParams): Observable<ApiResponse<PaginatedResponse<DomainList>>> {
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

    return this.http.get<ApiResponse<PaginatedResponse<DomainList>>>(this.apiUrl, { params: httpParams });
  }

  /**
   * Get a specific domain by ID
   */
  getDomain(id: number): Observable<ApiResponse<DomainResponse>> {
    return this.http.get<ApiResponse<DomainResponse>>(`${this.apiUrl}/${id}`);
  }

  /**
   * Update a domain
   */
  updateDomain(id: number, update: DomainUpdate): Observable<ApiResponse<DomainResponse>> {
    return this.http.patch<ApiResponse<DomainResponse>>(`${this.apiUrl}/${id}`, update);
  }

  /**
   * Delete a domain
   */
  deleteDomain(id: number): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.apiUrl}/${id}`);
  }

  /**
   * Verify domain DNS records
   */
  verifyDomain(id: number): Observable<ApiResponse<DomainVerificationResponse>> {
    return this.http.post<ApiResponse<DomainVerificationResponse>>(`${this.apiUrl}/${id}/verify`, {});
  }

  /**
   * Get DNS records for a domain
   */
  getDNSRecords(id: number): Observable<ApiResponse<DNSRecords>> {
    return this.http.get<ApiResponse<DNSRecords>>(`${this.apiUrl}/${id}/dns-records`);
  }

  /**
   * Get domains with active status only
   */
  getActiveDomains(): Observable<ApiResponse<DomainList[]>> {
    const params = new HttpParams().set('active_only', 'true');
    return this.http.get<ApiResponse<DomainList[]>>(this.apiUrl, { params });
  }

  /**
   * Check domain availability (before creating)
   */
  checkDomainAvailability(domainName: string): Observable<ApiResponse<{ available: boolean; reason?: string }>> {
    const params = new HttpParams().set('name', domainName);
    return this.http.get<ApiResponse<{ available: boolean; reason?: string }>>(`${this.apiUrl}/check-availability`, { params });
  }

  /**
   * Get domain statistics
   */
  getDomainStats(id: number): Observable<ApiResponse<{
    total_aliases: number;
    active_aliases: number;
    messages_received: number;
    messages_forwarded: number;
    last_message_at?: string;
  }>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/${id}/stats`);
  }
}