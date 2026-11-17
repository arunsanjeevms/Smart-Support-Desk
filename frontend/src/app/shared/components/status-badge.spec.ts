import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { ConfigService } from '../../core/services/config.service';
import { StatusBadge } from './status-badge';

describe('StatusBadge', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [StatusBadge],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    // Statuses come from the backend config endpoint.
    TestBed.inject(ConfigService).load().subscribe();
    TestBed.inject(HttpTestingController)
      .expectOne(`${environment.apiUrl}/config/`)
      .flush({
        statuses: [
          {
            value: 'in_progress',
            label: 'In Progress',
            icon: 'autorenew',
            color: '#D97706',
            description: 'A support agent is working on it.',
            transitions: ['open', 'resolved'],
          },
        ],
        categories: [],
        priorities: [],
        activity_types: [],
        roles: [],
        agents: [],
        export_formats: [],
        validation: {},
      });
  });

  it('shows the label and icon configured in the backend', () => {
    const fixture = TestBed.createComponent(StatusBadge);
    fixture.componentRef.setInput('status', 'in_progress');
    fixture.detectChanges();

    const badge: HTMLElement = fixture.nativeElement.querySelector('.badge');
    expect(badge.textContent).toContain('In Progress');
    expect(badge.textContent).toContain('autorenew');
    expect(badge.getAttribute('title')).toBe('A support agent is working on it.');
  });

  it('falls back to the raw value for unknown statuses', () => {
    const fixture = TestBed.createComponent(StatusBadge);
    fixture.componentRef.setInput('status', 'archived');
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('archived');
  });
});
