import { DatePipe } from '@angular/common';
import { Component, computed, effect, inject, untracked } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ActivatedRoute, ParamMap, Router, RouterLink } from '@angular/router';
import { skip } from 'rxjs';

import { LookupOption, Ticket } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { ConfigService } from '../../core/services/config.service';
import { LiveIndicator } from '../../shared/components/live-indicator';
import { LookupBadge } from '../../shared/components/lookup-badge';
import { PageHeader } from '../../shared/components/page-header';
import { StatusBadge } from '../../shared/components/status-badge';
import { UserAvatar } from '../../shared/components/user-avatar';
import { DataTable } from '../../shared/data-table/data-table';
import { CellTemplate, TableColumn } from '../../shared/data-table/table-column';
import { ExportMenu } from '../../shared/export-menu/export-menu';
import { TableSource } from '../../shared/data-table/table-source';
import { RelativeTimePipe } from '../../shared/pipes/relative-time.pipe';

const FILTER_KEYS = ['status', 'category', 'priority', 'assigned_to', 'created_from', 'created_to'];

function filtersFrom(params: ParamMap): Record<string, string> {
  return Object.fromEntries(FILTER_KEYS.map((key) => [key, params.get(key) ?? '']));
}

function isoDate(date: Date | null): string {
  if (!date) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

@Component({
  selector: 'app-ticket-list-page',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    RouterLink,
    MatButtonModule,
    MatDatepickerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatTooltipModule,
    PageHeader,
    DataTable,
    CellTemplate,
    StatusBadge,
    LookupBadge,
    UserAvatar,
    LiveIndicator,
    ExportMenu,
    RelativeTimePipe,
  ],
  templateUrl: './ticket-list-page.html',
  styleUrl: './ticket-list-page.scss',
})
export class TicketListPage {
  protected readonly auth = inject(AuthService);
  protected readonly config = inject(ConfigService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  /** The URL query string is the single source of truth for filters. */
  protected readonly source = new TableSource<Ticket>('tickets/', {
    sort: { active: 'created_at', direction: 'desc' },
    filters: filtersFrom(this.route.snapshot.queryParamMap),
  });

  /** Search / sort / filters for the Export menu in the page header (same as the table). */
  protected readonly exportParams = computed(() => this.source.filterParams());

  protected readonly statusFilter = computed(() =>
    (this.source.filters()['status'] ?? '').split(',').filter(Boolean),
  );
  protected readonly range = new FormGroup({
    start: new FormControl<Date | null>(null),
    end: new FormControl<Date | null>(null),
  });

  protected readonly columns = computed<TableColumn<Ticket>[]>(() => {
    const agent = this.auth.isAgent();
    return [
      { key: 'reference', label: 'Ref', sortField: 'reference', width: '104px' },
      { key: 'title', label: 'Title', sortField: 'title' },
      { key: 'category', label: 'Category', sortField: 'category__label', hideBelow: 'sm' },
      { key: 'priority', label: 'Priority', sortField: 'priority__sort_order', hideBelow: 'lg' },
      { key: 'status', label: 'Status', sortField: 'status', width: '130px' },
      ...(agent
        ? ([
            { key: 'created_by', label: 'Raised by', sortField: 'created_by__first_name', hideBelow: 'md' },
            { key: 'assigned_to', label: 'Assignee', sortField: 'assigned_to__first_name', hideBelow: 'md' },
          ] satisfies TableColumn<Ticket>[])
        : ([{ key: 'assigned_to', label: 'Handled by', hideBelow: 'md' }] satisfies TableColumn<Ticket>[])),
      { key: 'created_at', label: 'Created', sortField: 'created_at', width: '120px' },
    ];
  });

  protected readonly rowLink = (ticket: Ticket) => ['/tickets', ticket.id];

  constructor() {
    // URL -> table: links from the dashboard, the user menu or the back button.
    this.route.queryParamMap.pipe(skip(1), takeUntilDestroyed()).subscribe((params) => {
      const next = filtersFrom(params);
      if (JSON.stringify(next) !== JSON.stringify(this.source.filters())) {
        this.source.setFilters(next);
      }
    });

    // Table -> URL (and the date range inputs), so filtered views can be bookmarked.
    effect(() => {
      const filters = this.source.filters();
      untracked(() => {
        this.range.setValue(
          { start: toDate(filters['created_from']), end: toDate(filters['created_to']) },
          { emitEvent: false },
        );
        const current = filtersFrom(this.route.snapshot.queryParamMap);
        const next = { ...current, ...filters };
        if (JSON.stringify(next) !== JSON.stringify(current)) {
          const queryParams = Object.fromEntries(
            Object.entries(next).map(([key, value]) => [key, value || null]),
          );
          void this.router.navigate([], {
            relativeTo: this.route,
            queryParams,
            queryParamsHandling: 'merge',
            replaceUrl: true,
          });
        }
      });
    });
  }

  protected setFilter(key: string, value: string | string[] | null | undefined): void {
    this.source.setFilter(key, Array.isArray(value) ? value.join(',') : (value ?? ''));
  }

  protected applyDateRange(): void {
    const { start, end } = this.range.getRawValue();
    this.source.setFilters({
      ...this.source.filters(),
      created_from: isoDate(start),
      created_to: isoDate(end),
    });
  }

  protected statusSummary(): string {
    const selected = this.statusFilter();
    if (selected.length === 0) return 'Any status';
    return selected.map((value) => this.config.status(value)?.label ?? value).join(', ');
  }

  protected optionLabel(options: LookupOption[], id: string | undefined, fallback: string): string {
    return options.find((option) => option.id === id)?.label ?? fallback;
  }

  protected assigneeLabel(): string {
    const value = this.source.filters()['assigned_to'];
    if (!value) return 'Anyone';
    if (value === 'me') return 'Assigned to me';
    if (value === 'unassigned') return 'Unassigned';
    return this.config.agents().find((agent) => agent.id === value)?.full_name ?? 'Agent';
  }

  protected title(): string {
    const assigned = this.source.filters()['assigned_to'];
    if (!this.auth.isAgent()) return 'My tickets';
    return assigned === 'me' ? 'Assigned to me' : assigned === 'unassigned' ? 'Unassigned tickets' : 'All tickets';
  }
}

function toDate(value: string | undefined): Date | null {
  if (!value) return null;
  const [y, m, d] = value.split('-').map(Number);
  return y && m && d ? new Date(y, m - 1, d) : null;
}
