import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { LookupType, LookupValue } from '../models/api.models';
import { ApiService } from './api.service';

export type LookupValuePayload = Partial<
  Pick<
    LookupValue,
    | 'lookup_type'
    | 'code'
    | 'label'
    | 'description'
    | 'icon'
    | 'color'
    | 'sort_order'
    | 'is_active'
    | 'is_default'
  >
>;

/** Configurable lists (categories, priorities, ...) managed by the support team. */
@Injectable({ providedIn: 'root' })
export class LookupService {
  private readonly api = inject(ApiService);
  readonly valuesEndpoint = 'lookups/values/';

  types(): Observable<LookupType[]> {
    return this.api.get<LookupType[]>('lookups/types/');
  }

  create(payload: LookupValuePayload): Observable<LookupValue> {
    return this.api.post<LookupValue>(this.valuesEndpoint, payload);
  }

  update(id: string, payload: LookupValuePayload): Observable<LookupValue> {
    return this.api.patch<LookupValue>(`${this.valuesEndpoint}${id}/`, payload);
  }

  remove(id: string): Observable<void> {
    return this.api.delete(`${this.valuesEndpoint}${id}/`);
  }
}
