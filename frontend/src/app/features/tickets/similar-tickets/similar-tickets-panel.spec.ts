import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../../environments/environment';
import { AppConfig, SimilarTicket, SimilarTicketsResponse } from '../../../core/models/api.models';
import { ConfigService } from '../../../core/services/config.service';
import { SimilarTicketsPanel } from './similar-tickets-panel';
import { similarText } from './similar-text';

const SIMILAR_URL = `${environment.apiUrl}/tickets/similar/`;

function suggestion(id: string, score: number, title = `Resolved ticket ${id}`): SimilarTicket {
  return {
    id,
    reference: `SSD-10${id}`,
    title,
    description: 'Clicking download on any invoice does nothing.',
    resolution_note: 'Pop-ups were blocked for the billing site; allowing them fixed the download.',
    category: {
      id: 'cat-billing',
      code: 'billing',
      label: 'Billing',
      description: '',
      icon: 'receipt_long',
      color: '#0f766e',
      sort_order: 1,
      is_default: false,
    },
    resolved_at: '2026-11-01T10:00:00Z',
    resolved_by: { full_name: 'Meera Iyer', initials: 'MI' },
    score,
    match: score >= 0.6 ? 'strong' : 'possible',
  };
}

function reply(results: SimilarTicket[]): SimilarTicketsResponse {
  return { results, engine: 'semantic', model: 'all-MiniLM-L6-v2', compared: 14, min_score: 0.35 };
}

describe('SimilarTicketsPanel', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<SimilarTicketsPanel>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    http = TestBed.inject(HttpTestingController);

    // The feature is switched on in the backend configuration.
    TestBed.inject(ConfigService).load().subscribe();
    http.expectOne(`${environment.apiUrl}/config/`).flush({
      similarity: { enabled: true, max_results: 3, min_length: 10 },
    } as Partial<AppConfig>);
  });

  afterEach(() => http.verify());

  function render(inputs: Record<string, unknown>) {
    fixture = TestBed.createComponent(SimilarTicketsPanel);
    for (const [name, value] of Object.entries(inputs)) {
      fixture.componentRef.setInput(name, value);
    }
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  function findButton(element: HTMLElement): HTMLButtonElement {
    return element.querySelector('button.find') as HTMLButtonElement;
  }

  it('waits for enough text before searching', () => {
    const element = render({ title: 'Help', description: '' });
    expect(findButton(element).disabled).toBe(true);
    expect(element.textContent).toContain('Type a title or a few words of description');
  });

  it('asks the backend and shows at most three advisory suggestions', () => {
    const element = render({ title: 'Invoice download', description: 'The button does nothing', categoryId: 'cat-billing' });
    findButton(element).click();

    const request = http.expectOne(SIMILAR_URL);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      title: 'Invoice download',
      description: 'The button does nothing',
      exclude: null,
    });
    request.flush(reply([suggestion('1', 0.81), suggestion('2', 0.52), suggestion('3', 0.4)]));
    fixture.detectChanges();

    const results = element.querySelectorAll('.result');
    expect(results.length).toBe(3);
    expect(results[0].textContent).toContain('81% similar');
    expect(results[0].textContent).toContain('Same category');
    expect(element.textContent).toContain('Suggestions only.');
    expect(element.textContent).toContain('You can still submit your ticket.');
  });

  it('says so when nothing similar was resolved before', () => {
    const element = render({ title: 'Office coffee machine', description: 'It is leaking water' });
    findButton(element).click();
    http.expectOne(SIMILAR_URL).flush(reply([]));
    fixture.detectChanges();

    expect(element.querySelectorAll('.result').length).toBe(0);
    expect(element.textContent).toContain('No similar resolved tickets found');
  });

  it('offers to search again after the text is edited', () => {
    const element = render({ title: 'Invoice download', description: 'The button does nothing' });
    findButton(element).click();
    http.expectOne(SIMILAR_URL).flush(reply([suggestion('1', 0.7)]));
    fixture.detectChanges();
    expect(element.querySelector('.stale')).toBeNull();

    fixture.componentRef.setInput('description', 'The button does nothing in Chrome or Edge');
    fixture.detectChanges();
    expect(element.querySelector('.stale')?.textContent).toContain('Search again');
  });

  it('searches straight away for an agent on a ticket and lets them reuse a note', () => {
    const element = render({
      mode: 'ticket',
      title: 'Invoice download is broken',
      description: 'The download button does nothing',
      excludeId: 'ticket-42',
    });
    const used: SimilarTicket[] = [];
    fixture.componentInstance.useNote.subscribe((item) => used.push(item));

    const request = http.expectOne(SIMILAR_URL);
    expect(request.request.body.exclude).toBe('ticket-42');
    request.flush(reply([suggestion('1', 0.77)]));
    fixture.detectChanges();

    const useButton = Array.from(element.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Use this note'),
    ) as HTMLButtonElement;
    useButton.click();
    expect(used.map((item) => item.id)).toEqual(['1']);
  });

  it('builds the compared text the same way as the backend', () => {
    expect(similarText('  Invoice   download ', ' does nothing ')).toBe('Invoice download. does nothing');
    expect(similarText('Is it broken?', 'Yes')).toBe('Is it broken? Yes');
    expect(similarText('', 'Only a description')).toBe('Only a description');
  });
});
