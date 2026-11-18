import { HttpEventType, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { Attachment } from '../models/api.models';
import { AttachmentService, UploadProgress } from './attachment.service';

const stored: Attachment = {
  id: 'a1',
  file_name: 'screenshot.png',
  extension: 'png',
  content_type: 'image/png',
  size: 2048,
  is_image: true,
  uploaded_by: null,
  created_at: '2026-11-18T10:00:00Z',
  download_url: 'attachments/a1/download/',
  can_delete: true,
};

describe('AttachmentService', () => {
  let service: AttachmentService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(AttachmentService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('uploads the files as multipart and reports progress', () => {
    const updates: UploadProgress[] = [];
    const files = [new File(['png'], 'screenshot.png'), new File(['log'], 'error.log')];
    service.upload('t1', files).subscribe((update) => updates.push(update));

    const request = http.expectOne(`${environment.apiUrl}/tickets/t1/attachments/`);
    expect(request.request.method).toBe('POST');
    const body = request.request.body as FormData;
    expect((body.getAll('files') as File[]).map((f) => f.name)).toEqual(['screenshot.png', 'error.log']);

    request.event({ type: HttpEventType.UploadProgress, loaded: 50, total: 200 });
    request.flush([stored]);

    expect(updates[0]).toEqual({ percent: 25 });
    expect(updates[1]).toEqual({ percent: 100, attachments: [stored] });
  });

  it('downloads through the API so the sign-in token is sent', () => {
    service.blob(stored).subscribe();
    const request = http.expectOne(`${environment.apiUrl}/attachments/a1/download/`);
    expect(request.request.responseType).toBe('blob');
    request.flush(new Blob(['png']));
  });

  it('removes a file', () => {
    service.remove(stored).subscribe();
    const request = http.expectOne(`${environment.apiUrl}/attachments/a1/`);
    expect(request.request.method).toBe('DELETE');
    request.flush(null);
  });
});
