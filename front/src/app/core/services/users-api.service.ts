import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface UpdateProfileRequest {
  email: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface UserPreferences {
  email_on_new_message: boolean;
  email_on_domain_verified: boolean;
  email_on_quota_warning: boolean;
  email_weekly_summary: boolean;
}

export interface ApiKey {
  id: string;
  name: string;
  key: string;
  created_at: string;
  last_used: string | null;
}

export interface Session {
  id: string;
  device: string;
  location: string;
  ip_address: string;
  last_active: string;
  is_current: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}

@Injectable({
  providedIn: 'root'
})
export class UsersApiService {
  private apiUrl = `${environment.apiUrl}/users`;

  constructor(private http: HttpClient) {}

  // Profile Management
  updateProfile(data: UpdateProfileRequest): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(`${this.apiUrl}/profile`, data);
  }

  changePassword(data: ChangePasswordRequest): Observable<ApiResponse<null>> {
    return this.http.post<ApiResponse<null>>(`${this.apiUrl}/change-password`, data);
  }

  // Preferences
  getPreferences(): Observable<ApiResponse<UserPreferences>> {
    return this.http.get<ApiResponse<UserPreferences>>(`${this.apiUrl}/preferences`);
  }

  updatePreferences(preferences: UserPreferences): Observable<ApiResponse<UserPreferences>> {
    return this.http.put<ApiResponse<UserPreferences>>(`${this.apiUrl}/preferences`, preferences);
  }

  // API Keys
  listApiKeys(): Observable<ApiResponse<ApiKey[]>> {
    return this.http.get<ApiResponse<ApiKey[]>>(`${this.apiUrl}/api-keys`);
  }

  generateApiKey(name: string): Observable<ApiResponse<{ key: string; created_at: string }>> {
    return this.http.post<ApiResponse<{ key: string; created_at: string }>>(
      `${this.apiUrl}/api-keys`,
      { name }
    );
  }

  revokeApiKey(keyId: string): Observable<ApiResponse<null>> {
    return this.http.delete<ApiResponse<null>>(`${this.apiUrl}/api-keys/${keyId}`);
  }

  // Sessions
  listSessions(): Observable<ApiResponse<Session[]>> {
    return this.http.get<ApiResponse<Session[]>>(`${this.apiUrl}/sessions`);
  }

  revokeSession(sessionId: string): Observable<ApiResponse<null>> {
    return this.http.delete<ApiResponse<null>>(`${this.apiUrl}/sessions/${sessionId}`);
  }

  revokeAllSessions(): Observable<ApiResponse<null>> {
    return this.http.delete<ApiResponse<null>>(`${this.apiUrl}/sessions`);
  }

  // Account Management
  deleteAccount(): Observable<ApiResponse<null>> {
    return this.http.delete<ApiResponse<null>>(`${this.apiUrl}/account`);
  }
}
