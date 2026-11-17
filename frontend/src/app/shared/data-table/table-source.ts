import { DestroyRef, WritableSignal, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, catchError, of, switchMap, tap } from 'rxjs';

import { ApiService, QueryParams } from '../../core/services/api.service';
import { errorMessage } from '../../core/utils/api-errors';
import { AUTO_REFRESH_MS, autoRefresh } from '../../core/utils/auto-refresh';

export type SortDirection = 'asc' | 'desc' | '';

export interface TableSort {
  active: string;
  direction: SortDirection;
}

export interface TableSourceOptions {
  sort?: TableSort;
  pageSize?: number;
  filters?: Record<string, string>;
  /** Filters that define the table itself (e.g. which list) - never cleared or counted as "filtered". */
  lockedFilters?: string[];
  /** Background refresh interval in milliseconds; 0 turns it off. Defaults to 30 seconds. */
  autoRefreshMs?: number;
}

/**
 * State + loading logic for one server-side table.
 *
 * Searching, sorting, filtering and paging all happen in the Django API
 * (``?search=``, ``?ordering=``, ``?page=``, ...). This class just keeps the
 * current state in signals and re-fetches whenever it changes.
 *
 * Create it as a component field so it is tied to the component lifecycle:
 *   readonly source = new TableSource<Ticket>('tickets/', { sort: {...} });
 */
export class TableSource<T> {
  private readonly api = inject(ApiService);
  /** Emits `true` for a silent (background) reload, `false` for a normal one. */
  private readonly reload$ = new Subject<boolean>();

  readonly rows = signal<T[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly loadedOnce = signal(false);
  /** When the rows were last loaded successfully. */
  readonly lastUpdated = signal<Date | null>(null);

  readonly pageIndex = signal(0);
  readonly pageSize: WritableSignal<number>;
  readonly sort: WritableSignal<TableSort>;
  readonly search = signal('');
  readonly filters: WritableSignal<Record<string, string>>;

  /** True when search or any filter is active (used for empty states). */
  readonly isFiltered = computed(
    () =>
      !!this.search() ||
      Object.entries(this.filters()).some(
        ([key, value]) => !!value && !this.lockedFilters.includes(key),
      ),
  );
  private readonly lockedFilters: string[];

  constructor(
    readonly endpoint: string,
    options: TableSourceOptions = {},
  ) {
    this.pageSize = signal(options.pageSize ?? 10);
    this.sort = signal<TableSort>(options.sort ?? { active: '', direction: '' });
    this.filters = signal<Record<string, string>>({ ...(options.filters ?? {}) });
    this.lockedFilters = options.lockedFilters ?? [];

    this.reload$
      .pipe(
        tap((silent) => {
          if (silent) return; // background refresh: no spinner, keep what is on screen
          this.loading.set(true);
          this.error.set(null);
        }),
        switchMap((silent) =>
          this.api.getPage<T>(this.endpoint, this.queryParams()).pipe(
            catchError((error: unknown) => {
              // A failed background refresh keeps the current rows and stays quiet.
              if (!silent) this.error.set(errorMessage(error, 'Could not load the data.'));
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(inject(DestroyRef)),
      )
      .subscribe((page) => {
        this.loading.set(false);
        this.loadedOnce.set(true);
        if (!page) return;
        // If a filter shrank the result set, jump back to the last page.
        const lastPage = Math.max(0, Math.ceil(page.count / this.pageSize()) - 1);
        if (this.pageIndex() > lastPage && page.count > 0) {
          this.pageIndex.set(lastPage);
          this.load();
          return;
        }
        this.rows.set(page.results);
        this.total.set(page.count);
        this.lastUpdated.set(new Date());
      });

    // Keep the table fresh without anyone pressing a button.
    autoRefresh(() => {
      if (this.loadedOnce() && !this.loading()) this.refresh();
    }, options.autoRefreshMs ?? AUTO_REFRESH_MS);
  }

  /** Search / sort / filter params - shared by the list and the export endpoints. */
  filterParams(): QueryParams {
    const { active, direction } = this.sort();
    return {
      ...this.filters(),
      search: this.search().trim(),
      ordering: active && direction ? `${direction === 'desc' ? '-' : ''}${active}` : '',
    };
  }

  queryParams(): QueryParams {
    return { ...this.filterParams(), page: this.pageIndex() + 1, page_size: this.pageSize() };
  }

  load(): void {
    this.reload$.next(false);
  }

  /** Reload in the background: no loading state, and errors do not replace the rows. */
  refresh(): void {
    this.reload$.next(true);
  }

  setSearch(term: string): void {
    if (term === this.search()) return;
    this.search.set(term);
    this.pageIndex.set(0);
    this.load();
  }

  setSort(sort: TableSort): void {
    this.sort.set(sort);
    this.pageIndex.set(0);
    this.load();
  }

  setPage(pageIndex: number, pageSize: number): void {
    this.pageIndex.set(pageSize === this.pageSize() ? pageIndex : 0);
    this.pageSize.set(pageSize);
    this.load();
  }

  setFilter(name: string, value: string | null | undefined): void {
    this.filters.update((current) => ({ ...current, [name]: value ?? '' }));
    this.pageIndex.set(0);
    this.load();
  }

  setFilters(filters: Record<string, string>): void {
    this.filters.set({ ...filters });
    this.pageIndex.set(0);
    this.load();
  }

  clearFilters(): void {
    const cleared = Object.fromEntries(
      Object.entries(this.filters()).map(([key, value]) => [
        key,
        this.lockedFilters.includes(key) ? value : '',
      ]),
    );
    this.filters.set(cleared);
    this.search.set('');
    this.pageIndex.set(0);
    this.load();
  }
}
