import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  CategorySuggestionResponse,
  SimilarTicketsQuery,
  SimilarTicketsResponse,
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

  /** A comment, optionally with files (sent as multipart when there are files). */
  comment(id: string, message: string, files: File[] = []): Observable<TicketActivity> {
    if (!files.length) {
      return this.api.post<TicketActivity>(`tickets/${id}/comments/`, { message });
    }
    const body = new FormData();
    body.append('message', message);
    files.forEach((file) => body.append('files', file, file.name));
    return this.api.post<TicketActivity>(`tickets/${id}/comments/`, body);
  }

  /** Up to three resolved tickets that look like this text (advisory only). */
  similar(query: SimilarTicketsQuery): Observable<SimilarTicketsResponse> {
    return this.api.post<SimilarTicketsResponse>('tickets/similar/', query);
  }

  /** The likely category for the text typed so far (advisory). */
  suggestCategory(query: SimilarTicketsQuery): Observable<CategorySuggestionResponse> {
    return this.api.post<CategorySuggestionResponse>('tickets/suggest-category/', query);
  }

  stats(): Observable<TicketStats> {
    return this.api.get<TicketStats>('tickets/stats/');
  }
}
