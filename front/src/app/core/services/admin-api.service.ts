import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../../core/interfaces/common.interface';

interface DatabaseStats {
  users: {
    total: number;
    active: number;
    admins: number;
    recent_signups: number;
  };
  organizations: {
    total: number;
    active: number;
    with_subscription: number;
  };
  domains: {
    total: number;
    verified: number;
    unverified: number;
    active: number;
  };
  aliases: {
    total: number;
    active: number;
    inactive: number;
  };
  messages: {
    total: number;
    today: number;
    this_week: number;
    this_month: number;
    failed: number;
  };
}

interface RecentActivity {
  id: number;
  type: string;
  description: string;
  timestamp: string;
  user?: string;
}

interface SystemHealth {
  database: {
    status: string;
    connections: number;
    size: string;
  };
  redis?: {
    status: string;
    memory_used: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AdminApiService {
  private apiUrl = `${environment.apiUrl}/admin`;

  constructor(private http: HttpClient) {}

  /**
   * Get database statistics
   */
  getDatabaseStats(): Observable<ApiResponse<DatabaseStats>> {
    return this.http.get<ApiResponse<DatabaseStats>>(`${this.apiUrl}/stats`);
  }

  /**
   * Get recent activity across the platform
   */
  getRecentActivity(limit: number = 50): Observable<ApiResponse<RecentActivity[]>> {
    return this.http.get<ApiResponse<RecentActivity[]>>(`${this.apiUrl}/activity?limit=${limit}`);
  }

  /**
   * Get system health status
   */
  getSystemHealth(): Observable<ApiResponse<SystemHealth>> {
    return this.http.get<ApiResponse<SystemHealth>>(`${this.apiUrl}/health`);
  }

  /**
   * Get all users (admin only)
   */
  getAllUsers(page: number = 1, pageSize: number = 50): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/users?page=${page}&page_size=${pageSize}`);
  }

  /**
   * Get all organizations (admin only)
   */
  getAllOrganizations(page: number = 1, pageSize: number = 50): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/organizations?page=${page}&page_size=${pageSize}`);
  }

  /**
   * Get all domains (admin only)
   */
  getAllDomains(page: number = 1, pageSize: number = 50): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/domains?page=${page}&page_size=${pageSize}`);
  }

  /**
   * Get all aliases (admin only)
   */
  getAllAliases(page: number = 1, pageSize: number = 50): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/aliases?page=${page}&page_size=${pageSize}`);
  }

  /**
   * Get all messages (admin only)
   */
  getAllMessages(page: number = 1, pageSize: number = 50): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/messages?page=${page}&page_size=${pageSize}`);
  }
}
