import { NgTemplateOutlet } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, contentChildren, inject, input } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged } from 'rxjs';

import { LiveIndicator } from '../components/live-indicator';
import { ExportMenu } from '../export-menu/export-menu';
import { CellTemplate, TableColumn } from './table-column';
import { TableSource } from './table-source';

/**
 * Reusable server-side data table: search, sort, paging, filters slot,
 * loading / empty / error states and PDF / Excel / email export.
 *
 * Usage:
 *   <app-data-table [source]="source" [columns]="columns" exportTitle="Tickets">
 *     <ng-container tableFilters> ...mat-selects... </ng-container>
 *     <ng-template appCell="status" let-row> ... </ng-template>
 *   </app-data-table>
 */
@Component({
  selector: 'app-data-table',
  imports: [
    NgTemplateOutlet,
    ReactiveFormsModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatSortModule,
    MatTableModule,
    MatTooltipModule,
    ExportMenu,
    LiveIndicator,
  ],
  templateUrl: './data-table.html',
  styleUrl: './data-table.scss',
})
export class DataTable<T extends object> implements OnInit {
  readonly source = input.required<TableSource<T>>();
  readonly columns = input.required<TableColumn<T>[]>();
  readonly exportTitle = input('Report');
  readonly showExport = input(true);
  readonly searchPlaceholder = input('Search…');
  /** When set, clicking a row navigates to the returned route. */
  readonly rowLink = input<((row: T) => unknown[]) | null>(null);
  readonly emptyIcon = input('inbox');
  readonly emptyTitle = input('Nothing here yet');
  readonly emptyMessage = input('');
  readonly pageSizeOptions = input([10, 25, 50]);

  private readonly cellTemplates = contentChildren(CellTemplate);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly searchControl = new FormControl('', { nonNullable: true });

  protected readonly templates = computed(
    () => new Map(this.cellTemplates().map((cell) => [cell.column(), cell.template])),
  );
  protected readonly displayedColumns = computed(() => this.columns().map((column) => column.key));
  protected readonly exportParams = computed(() => {
    // Re-evaluate whenever search / sort / filters change.
    const source = this.source();
    source.search();
    source.sort();
    source.filters();
    return source.filterParams();
  });

  ngOnInit(): void {
    const source = this.source();
    this.searchControl.setValue(source.search(), { emitEvent: false });
    this.searchControl.valueChanges
      .pipe(debounceTime(350), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe((term) => source.setSearch(term.trim()));
    source.load();
  }

  protected onSort(sort: Sort): void {
    const column = this.columns().find((c) => c.key === sort.active);
    this.source().setSort({
      active: sort.direction ? (column?.sortField ?? sort.active) : '',
      direction: sort.direction,
    });
  }

  protected onPage(event: PageEvent): void {
    this.source().setPage(event.pageIndex, event.pageSize);
  }

  protected sortKey(): string {
    const { active } = this.source().sort();
    return this.columns().find((c) => c.sortField === active)?.key ?? '';
  }

  protected clearSearch(): void {
    this.searchControl.setValue('');
  }

  protected clearAll(): void {
    this.searchControl.setValue('', { emitEvent: false });
    this.source().clearFilters();
  }

  protected openRow(row: T, event?: Event): void {
    const link = this.rowLink();
    if (!link) return;
    // Let real links / buttons inside the row do their own thing.
    if ((event?.target as HTMLElement | null)?.closest('a, button')) return;
    void this.router.navigate(link(row));
  }

  protected cellText(column: TableColumn<T>, row: T): string {
    const value = column.value ? column.value(row) : (row as Record<string, unknown>)[column.key];
    return value === null || value === undefined || value === '' ? '—' : String(value);
  }
}
