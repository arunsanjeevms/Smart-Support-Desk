import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { Attachment } from '../../core/models/api.models';
import { AttachmentList } from './attachment-list';

function attachment(overrides: Partial<Attachment>): Attachment {
  return {
    id: 'a1',
    file_name: 'error.log',
    extension: 'log',
    content_type: 'text/plain',
    size: 3 * 1024,
    is_image: false,
    uploaded_by: null,
    created_at: new Date().toISOString(),
    download_url: 'attachments/a1/download/',
    can_delete: false,
    ...overrides,
  };
}

describe('AttachmentList', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    // jsdom has no blob URLs.
    URL.createObjectURL = vi.fn(() => 'blob:thumbnail');
    URL.revokeObjectURL = vi.fn();
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lists files with their size and only offers Remove when allowed', () => {
    const fixture = TestBed.createComponent(AttachmentList);
    fixture.componentRef.setInput('attachments', [
      attachment({ id: 'a1', file_name: 'error.log', can_delete: false }),
      attachment({ id: 'a2', file_name: 'notes.txt', size: 2 * 1024 * 1024, can_delete: true }),
    ]);
    fixture.detectChanges();

    const items = fixture.nativeElement.querySelectorAll('.file') as NodeListOf<HTMLElement>;
    expect(items.length).toBe(2);
    expect(items[0].textContent).toContain('error.log');
    expect(items[0].textContent).toContain('3 KB');
    expect(items[0].querySelector('.delete')).toBeNull();
    expect(items[1].textContent).toContain('2.0 MB');
    expect(items[1].querySelector('.delete')).not.toBeNull();
  });

  it('loads a thumbnail for images', () => {
    const fixture = TestBed.createComponent(AttachmentList);
    fixture.componentRef.setInput('attachments', [
      attachment({ id: 'img', file_name: 'shot.png', extension: 'png', is_image: true, download_url: 'attachments/img/download/' }),
    ]);
    fixture.detectChanges();

    http.expectOne(`${environment.apiUrl}/attachments/img/download/`).flush(new Blob(['png']));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('img')?.getAttribute('src')).toBe('blob:thumbnail');
  });
});
