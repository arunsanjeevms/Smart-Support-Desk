import { HttpClient, HttpEventType, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, filter, map } from 'rxjs';

import { Attachment } from '../models/api.models';
import { saveBlob } from '../utils/files';
import { ApiService } from './api.service';

/** Progress of an upload; `attachments` is set once the server has stored the files. */
export interface UploadProgress {
  percent: number;
  attachments?: Attachment[];
}

/**
 * Ticket attachments: upload (with progress), download and remove.
 *
 * Downloads go through HttpClient (not a plain link) so the sign-in token is
 * sent with the request.
 */
@Injectable({ providedIn: 'root' })
export class AttachmentService {
  private readonly http = inject(HttpClient);
  private readonly api = inject(ApiService);

  list(ticketId: string): Observable<Attachment[]> {
    return this.api.get<Attachment[]>(`tickets/${ticketId}/attachments/`);
  }

  upload(ticketId: string, files: File[]): Observable<UploadProgress> {
    const body = new FormData();
    files.forEach((file) => body.append('files', file, file.name));
    return this.http
      .post<Attachment[]>(this.api.url(`tickets/${ticketId}/attachments/`), body, {
        reportProgress: true,
        observe: 'events',
      })
      .pipe(
        filter(
          (event) => event.type === HttpEventType.UploadProgress || event.type === HttpEventType.Response,
        ),
        map((event): UploadProgress => {
          if (event.type === HttpEventType.UploadProgress) {
            return { percent: event.total ? Math.round((100 * event.loaded) / event.total) : 0 };
          }
          return { percent: 100, attachments: (event as HttpResponse<Attachment[]>).body ?? [] };
        }),
      );
  }

  /** The file contents (used for image previews). */
  blob(attachment: Attachment): Observable<Blob> {
    return this.http.get(this.api.url(attachment.download_url), { responseType: 'blob' });
  }

  download(attachment: Attachment): Observable<void> {
    return this.blob(attachment).pipe(map((blob) => saveBlob(blob, attachment.file_name)));
  }

  remove(attachment: Attachment): Observable<void> {
    return this.api.delete<void>(`attachments/${attachment.id}/`);
  }
}
