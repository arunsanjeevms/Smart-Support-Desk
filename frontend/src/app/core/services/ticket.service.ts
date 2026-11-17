import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  TicketActivity,
  TicketCreatePayload,
  TicketDetail,
  TicketStats,
  TicketUpdatePayload,
} from '../models/api.models';
import { ApiService } from './api.service';

/** Ticket endpoints. Listing goes through the generic TableSource. */
@Injectable({ providedIn: 'root' })
export class TicketService {
  private readonly api = inject(ApiService);
  readonly endpoint = 'tickets/';

  get(id: string): Observable<TicketDetail> {
    return this.api.get<TicketDetail>(`tickets/${id}/`);
  }

  create(payload: TicketCreatePayload): Observable<TicketDetail> {
    return this.api.post<TicketDetail>('tickets/', payload);
  }

  update(id: string, payload: TicketUpdatePayload): Observable<TicketDetail> {
    return this.api.patch<TicketDetail>(`tickets/${id}/`, payload);
  }

  activities(id: string): Observable<TicketActivity[]> {
    return this.api.get<TicketActivity[]>(`tickets/${id}/activities/`);
  }

  comment(id: string, message: string): Observable<TicketActivity> {
    return this.api.post<TicketActivity>(`tickets/${id}/comments/`, { message });
  }

  stats(): Observable<TicketStats> {
    return this.api.get<TicketStats>('tickets/stats/');
  }
}
