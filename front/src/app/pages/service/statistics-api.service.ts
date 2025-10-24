import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  StatisticsResponse,
  StatisticsFilter,
  OverallStats,
  TimeSeriesDataPoint,
  DomainStats,
  AliasStats
} from '../../core/interfaces/statistics.interface';
import { ApiResponse } from '../../core/interfaces/common.interface';

@Injectable({
  providedIn: 'root'
})
export class StatisticsApiService {
  private apiUrl = `${environment.apiUrl}/statistics`;

  constructor(private http: HttpClient) {}

  /**
   * Get complete statistics with all data
   */
  getStatistics(filter?: StatisticsFilter): Observable<ApiResponse<StatisticsResponse>> {
    let httpParams = new HttpParams();

    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }
    if (filter?.domain_id) {
      httpParams = httpParams.set('domain_id', filter.domain_id.toString());
    }
    if (filter?.granularity) {
      httpParams = httpParams.set('granularity', filter.granularity);
    }

    return this.http.get<ApiResponse<StatisticsResponse>>(this.apiUrl, { params: httpParams });
  }

  /**
   * Get overall statistics summary
   */
  getOverallStats(filter?: Pick<StatisticsFilter, 'date_from' | 'date_to'>): Observable<ApiResponse<OverallStats>> {
    let httpParams = new HttpParams();

    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }

    return this.http.get<ApiResponse<OverallStats>>(`${this.apiUrl}/overall`, { params: httpParams });
  }

  /**
   * Get time series data
   */
  getTimeSeries(filter?: StatisticsFilter): Observable<ApiResponse<TimeSeriesDataPoint[]>> {
    let httpParams = new HttpParams();

    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }
    if (filter?.domain_id) {
      httpParams = httpParams.set('domain_id', filter.domain_id.toString());
    }
    if (filter?.granularity) {
      httpParams = httpParams.set('granularity', filter.granularity);
    }

    return this.http.get<ApiResponse<TimeSeriesDataPoint[]>>(`${this.apiUrl}/time-series`, { params: httpParams });
  }

  /**
   * Get domain breakdown
   */
  getDomainStats(filter?: Pick<StatisticsFilter, 'date_from' | 'date_to'>): Observable<ApiResponse<DomainStats[]>> {
    let httpParams = new HttpParams();

    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }

    return this.http.get<ApiResponse<DomainStats[]>>(`${this.apiUrl}/domains`, { params: httpParams });
  }

  /**
   * Get top aliases
   */
  getTopAliases(
    limit: number = 10,
    filter?: Pick<StatisticsFilter, 'date_from' | 'date_to' | 'domain_id'>
  ): Observable<ApiResponse<AliasStats[]>> {
    let httpParams = new HttpParams().set('limit', limit.toString());

    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }
    if (filter?.domain_id) {
      httpParams = httpParams.set('domain_id', filter.domain_id.toString());
    }

    return this.http.get<ApiResponse<AliasStats[]>>(`${this.apiUrl}/top-aliases`, { params: httpParams });
  }

  /**
   * Export statistics to file
   */
  exportStatistics(
    format: 'csv' | 'json' | 'pdf',
    filter?: StatisticsFilter
  ): Observable<Blob> {
    let httpParams = new HttpParams().set('format', format);

    if (filter?.date_from) {
      httpParams = httpParams.set('date_from', filter.date_from);
    }
    if (filter?.date_to) {
      httpParams = httpParams.set('date_to', filter.date_to);
    }
    if (filter?.domain_id) {
      httpParams = httpParams.set('domain_id', filter.domain_id.toString());
    }
    if (filter?.granularity) {
      httpParams = httpParams.set('granularity', filter.granularity);
    }

    return this.http.get(`${this.apiUrl}/export`, {
      params: httpParams,
      responseType: 'blob'
    });
  }
}
