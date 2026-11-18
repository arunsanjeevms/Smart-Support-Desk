import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import { AppConfig, CategorySuggestionResponse } from '../../../core/models/api.models';
import { ConfigService } from '../../../core/services/config.service';
import { CategorySuggestionHint, SUGGEST_DEBOUNCE_MS } from './category-suggestion';

const URL = `${environment.apiUrl}/tickets/suggest-category/`;

const billing = {
  id: 'cat-billing',
  code: 'billing',
  label: 'Billing & Payments',
  description: '',
  icon: 'payments',
  color: '#059669',
  sort_order: 2,
  is_default: false,
};

function reply(matches = 3): CategorySuggestionResponse {
  return {
    suggestion: { category: billing, confidence: 0.9, basis: 'similar_tickets', matches },
    engine: 'semantic',
    model: 'all-MiniLM-L6-v2',
  };
}

describe('CategorySuggestionHint', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<CategorySuggestionHint>;

  beforeEach(() => {
    vi.useFakeTimers();
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
    TestBed.inject(ConfigService).load().subscribe();
    http.expectOne(`${environment.apiUrl}/config/`).flush({
      similarity: { enabled: true, max_results: 3, min_length: 10, category_suggestions: true },
    } as Partial<AppConfig>);
    fixture = TestBed.createComponent(CategorySuggestionHint);
  });

  afterEach(() => {
    http.verify();
    vi.useRealTimers();
  });

  function type(title: string, description = '', selectedId: string | null = null) {
    fixture.componentRef.setInput('title', title);
    fixture.componentRef.setInput('description', description);
    fixture.componentRef.setInput('selectedId', selectedId);
    fixture.detectChanges();
  }

  function text(): string {
    fixture.detectChanges();
    return (fixture.nativeElement.textContent as string).replace(/\s+/g, ' ');
  }

  it('asks once the user pauses, and offers the category', () => {
    type('Charged twice for my plan');
    vi.advanceTimersByTime(SUGGEST_DEBOUNCE_MS - 100);
    http.expectNone(URL);

    vi.advanceTimersByTime(100);
    const request = http.expectOne(URL);
    expect(request.request.body).toEqual({ title: 'Charged twice for my plan', description: '' });
    request.flush(reply(3));

    expect(text()).toContain('Suggested category');
    expect(text()).toContain('Billing & Payments');
    expect(text()).toContain('based on 3 similar tickets');

    const applied: string[] = [];
    fixture.componentInstance.apply.subscribe((id) => applied.push(id));
    (fixture.nativeElement.querySelector('button.action') as HTMLButtonElement).click();
    expect(applied).toEqual(['cat-billing']);
  });

  it('only sends the latest text when typing quickly', () => {
    type('Charged twice');
    vi.advanceTimersByTime(200);
    type('Charged twice for my monthly plan');
    vi.advanceTimersByTime(SUGGEST_DEBOUNCE_MS);
    const request = http.expectOne(URL);
    expect(request.request.body.title).toBe('Charged twice for my monthly plan');
    request.flush(reply());
  });

  it('does not ask for very short text', () => {
    type('Help');
    vi.advanceTimersByTime(SUGGEST_DEBOUNCE_MS);
    http.expectNone(URL);
    expect(text().trim()).toBe('');
  });

  it('offers to switch when another category is chosen, and stays quiet when it matches', () => {
    type('Charged twice for my plan', '', 'cat-performance');
    vi.advanceTimersByTime(SUGGEST_DEBOUNCE_MS);
    http.expectOne(URL).flush(reply());
    expect(text()).toContain('This reads like');
    expect(text()).toContain('Switch');

    fixture.componentRef.setInput('selectedId', 'cat-billing');
    expect(text()).toContain('Matches the suggested category');
    expect(fixture.nativeElement.querySelector('button.action')).toBeNull();
  });
});
