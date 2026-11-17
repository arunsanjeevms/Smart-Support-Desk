import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { TableSource } from './table-source';

interface Row {
  id: string;
}

describe('TableSource', () => {
  let http: HttpTestingController;

  function createSource() {
    return TestBed.runInInjectionContext(
      () =>
        new TableSource<Row>('tickets/', {
          sort: { active: 'created_at', direction: 'desc' },
          filters: { type: 'ticket_category', status: '' },
          lockedFilters: ['type'],
        }),
    );
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('builds API params for paging, sorting, search and filters', () => {
    const source = createSource();
    source.search.set(' login ');
    source.filters.update((f) => ({ ...f, status: 'open,in_progress' }));

    expect(source.queryParams()).toEqual({
      type: 'ticket_category',
      status: 'open,in_progress',
      search: 'login',
      ordering: '-created_at',
      page: 1,
      page_size: 10,
    });
  });

  it('loads rows and the total count from the API', () => {
    const source = createSource();
    source.load();

    const request = http.expectOne((req) => req.url === `${environment.apiUrl}/tickets/`);
    expect(request.request.params.get('ordering')).toBe('-created_at');
    expect(request.request.params.has('status')).toBe(false); // empty filters are skipped
    request.flush({ count: 1, page: 1, page_size: 10, total_pages: 1, results: [{ id: 'a' }] });

    expect(source.rows()).toEqual([{ id: 'a' }]);
    expect(source.total()).toBe(1);
    expect(source.loading()).toBe(false);
  });

  it('goes back to the first page when the search changes', () => {
    const source = createSource();
    source.pageIndex.set(3);
    source.setSearch('printer');
    http.expectOne(() => true).flush({ count: 0, page: 1, page_size: 10, total_pages: 0, results: [] });

    expect(source.pageIndex()).toBe(0);
  });

  it('shows a friendly error when the request fails', () => {
    const source = createSource();
    source.load();
    http
      .expectOne(() => true)
      .flush({ message: 'Only the support team can perform this action.', errors: {} }, { status: 403, statusText: 'Forbidden' });

    expect(source.error()).toBe('Only the support team can perform this action.');
  });

  it('keeps locked filters when clearing and does not count them as filtering', () => {
    const source = createSource();
    expect(source.isFiltered()).toBe(false);

    source.setFilter('status', 'open');
    http.expectOne(() => true).flush({ count: 0, page: 1, page_size: 10, total_pages: 0, results: [] });
    expect(source.isFiltered()).toBe(true);

    source.clearFilters();
    http.expectOne(() => true).flush({ count: 0, page: 1, page_size: 10, total_pages: 0, results: [] });
    expect(source.filters()).toEqual({ type: 'ticket_category', status: '' });
    expect(source.isFiltered()).toBe(false);
  });
});
