import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';
import {AliasCreate, AliasListItem, AliasResponse, AliasUpdate} from '../../core/interfaces/alias.interface';
import {PaginatedResponse} from '../../core/interfaces/paginated-response.interface';

@Injectable({
    providedIn: 'root'
})
export class AliasesApiService {
    private apiUrl = `${environment.apiUrl}/aliases`;

    constructor(private http: HttpClient) {
    }

    createAlias(aliasData: AliasCreate): Observable<AliasResponse> {
        return this.http.post<AliasResponse>(this.apiUrl, aliasData, {withCredentials: true});
    }

    getAliases(page: number = 1, pageSize: number = 20, domainId?: number): Observable<PaginatedResponse<AliasListItem>> {
        let params = new HttpParams()
            .set('page', page.toString())
            .set('page_size', pageSize.toString());

        if (domainId) {
            params = params.set('domain_id', domainId.toString());
        }

        return this.http.get<PaginatedResponse<AliasListItem>>(this.apiUrl, {params, withCredentials: true});
    }

    getAlias(aliasId: number): Observable<AliasResponse> {
        return this.http.get<AliasResponse>(`${this.apiUrl}/${aliasId}`, {withCredentials: true});
    }

    updateAlias(aliasId: number, aliasUpdate: AliasUpdate): Observable<AliasResponse> {
        return this.http.patch<AliasResponse>(`${this.apiUrl}/${aliasId}`, aliasUpdate, {withCredentials: true});
    }

    deleteAlias(aliasId: number, hardDelete: boolean = false): Observable<void> {
        const params = new HttpParams().set('hard_delete', hardDelete.toString());
        return this.http.delete<void>(`${this.apiUrl}/${aliasId}`, {params, withCredentials: true});
    }
}
