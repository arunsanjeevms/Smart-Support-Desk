import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Paginated } from '../models/api.models';

export type QueryParams = Record<string, string | number | boolean | null | undefined>;

/** Converts a plain object into HttpParams, skipping empty values. */
export function toHttpParams(params: QueryParams = {}): HttpParams {
  let httpParams = new HttpParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      httpParams = httpParams.set(key, String(value));
    }
  }
  return httpParams;
}

/**
 * Thin wrapper around HttpClient that prefixes the API base URL.
 * Feature services use this instead of building URLs themselves.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  readonly baseUrl = environment.apiUrl;

  url(path: string): string {
    return `${this.baseUrl}/${path.replace(/^\//, '')}`;
  }

  get<T>(path: string, params?: QueryParams): Observable<T> {
    return this.http.get<T>(this.url(path), { params: toHttpParams(params) });
  }

  getPage<T>(path: string, params?: QueryParams): Observable<Paginated<T>> {
    return this.get<Paginated<T>>(path, params);
  }

  post<T>(path: string, body: unknown, params?: QueryParams): Observable<T> {
    return this.http.post<T>(this.url(path), body, { params: toHttpParams(params) });
  }

  patch<T>(path: string, body: unknown): Observable<T> {
    return this.http.patch<T>(this.url(path), body);
  }

  delete<T = void>(path: string): Observable<T> {
    return this.http.delete<T>(this.url(path));
  }
}
