import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  MessageResponse, 
  MessageList, 
  MessageStats, 
  MessageFilter 
} from '../interfaces/message.interface';
import { 
  PaginatedResponse, 
  PaginationParams, 
  ApiResponse 
} from '../interfaces/common.interface';

@Injectable({
  providedIn: 'root'
})
export class MessagesApiService {
  private apiUrl = `${environment.apiUrl}/messages`;

  constructor(private http: HttpClient) {}

  /**
   * Get paginated list of messages with optional filtering
   */
  getMessages(
    params?: PaginationParams, 
    filter?: MessageFilter
  ): Observable<ApiResponse<PaginatedResponse<MessageList>>> {
    let httpParams = new HttpParams();
    
    // Pagination parameters
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

    // Filter parameters
    if (filter?.domain_id) {
      httpParams = httpParams.set('domain_id', filter.domain_id.toString());
    }
    if (filter?.status) {
      httpParams = httpParams.set('status', filter.status);
    }
    if (filter?.sender_email) {
      httpParams = httpParams.set('sender_email', filter.sender_email);
    }
    if (filter?.recipient_email) {
      httpParams = httpParams.set('recipient_email', filter.recipient_email);
    }
    if (filter?.has_attachments !== undefined) {
      httpParams = httpParams.set('has_attachments', filter.has_attachments.toString());
    }
    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }

    return this.http.get<ApiResponse<PaginatedResponse<MessageList>>>(this.apiUrl, { params: httpParams });
  }

  /**
   * Get a specific message by ID
   */
  getMessage(id: number): Observable<ApiResponse<MessageResponse>> {
    return this.http.get<ApiResponse<MessageResponse>>(`${this.apiUrl}/${id}`);
  }

  /**
   * Delete a message
   */
  deleteMessage(id: number): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.apiUrl}/${id}`);
  }

  /**
   * Delete multiple messages
   */
  deleteMessages(ids: number[]): Observable<ApiResponse<{ deleted_count: number }>> {
    return this.http.post<ApiResponse<{ deleted_count: number }>>(`${this.apiUrl}/bulk-delete`, { ids });
  }

  /**
   * Mark message as read/unread
   */
  markMessage(id: number, read: boolean): Observable<ApiResponse<MessageResponse>> {
    return this.http.patch<ApiResponse<MessageResponse>>(`${this.apiUrl}/${id}`, { is_read: read });
  }

  /**
   * Get message statistics
   */
  getMessageStats(filter?: Pick<MessageFilter, 'domain_id' | 'date_from' | 'date_to'>): Observable<ApiResponse<MessageStats>> {
    let httpParams = new HttpParams();
    
    if (filter?.domain_id) {
      httpParams = httpParams.set('domain_id', filter.domain_id.toString());
    }
    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }

    return this.http.get<ApiResponse<MessageStats>>(`${this.apiUrl}/stats`, { params: httpParams });
  }

  /**
   * Download message attachment
   */
  downloadAttachment(messageId: number, attachmentId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${messageId}/attachments/${attachmentId}`, {
      responseType: 'blob'
    });
  }

  /**
   * Get message raw content
   */
  getMessageRaw(id: number): Observable<string> {
    return this.http.get(`${this.apiUrl}/${id}/raw`, { responseType: 'text' });
  }

  /**
   * Resend/forward a message
   */
  resendMessage(id: number, toEmail: string): Observable<ApiResponse<{ success: boolean; message_id?: string }>> {
    return this.http.post<ApiResponse<{ success: boolean; message_id?: string }>>(
      `${this.apiUrl}/${id}/resend`, 
      { to_email: toEmail }
    );
  }

  /**
   * Get messages by thread ID
   */
  getMessageThread(threadId: string): Observable<ApiResponse<MessageList[]>> {
    const params = new HttpParams().set('thread_id', threadId);
    return this.http.get<ApiResponse<MessageList[]>>(this.apiUrl, { params });
  }

  /**
   * Search messages by content
   */
  searchMessages(
    query: string, 
    params?: PaginationParams, 
    filter?: MessageFilter
  ): Observable<ApiResponse<PaginatedResponse<MessageList>>> {
    let httpParams = new HttpParams().set('q', query);
    
    // Add pagination and filter parameters
    if (params?.page) {
      httpParams = httpParams.set('page', params.page.toString());
    }
    if (params?.size) {
      httpParams = httpParams.set('size', params.size.toString());
    }
    if (filter?.domain_id) {
      httpParams = httpParams.set('domain_id', filter.domain_id.toString());
    }
    if (filter?.status) {
      httpParams = httpParams.set('status', filter.status);
    }

    return this.http.get<ApiResponse<PaginatedResponse<MessageList>>>(`${this.apiUrl}/search`, { params: httpParams });
  }
}