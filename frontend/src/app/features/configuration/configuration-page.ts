import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';

import { LookupType, LookupValue } from '../../core/models/api.models';
import { ConfigService } from '../../core/services/config.service';
import { LookupService } from '../../core/services/lookup.service';
import { NotifyService } from '../../core/services/notify.service';
import { errorMessage } from '../../core/utils/api-errors';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/components/confirm-dialog';
import { PageHeader } from '../../shared/components/page-header';
import { DataTable } from '../../shared/data-table/data-table';
import { CellTemplate, TableColumn } from '../../shared/data-table/table-column';
import { TableSource } from '../../shared/data-table/table-source';
import { LookupValueDialog, LookupValueDialogData } from './lookup-value-dialog';

/**
 * Manage the backend-configured lists (ticket categories, priorities, ...).
 * The same data is also editable in the Django admin.
 */
@Component({
  selector: 'app-configuration-page',
  imports: [
    MatButtonModule,
    MatButtonToggleModule,
    MatIconModule,
    MatSlideToggleModule,
    MatTooltipModule,
    PageHeader,
    DataTable,
    CellTemplate,
  ],
  templateUrl: './configuration-page.html',
  styleUrl: './configuration-page.scss',
})
export class ConfigurationPage implements OnInit {
  private readonly lookups = inject(LookupService);
  private readonly config = inject(ConfigService);
  private readonly dialog = inject(MatDialog);
  private readonly notify = inject(NotifyService);

  protected readonly types = signal<LookupType[]>([]);
  protected readonly activeType = signal<LookupType | null>(null);
  protected readonly busyId = signal<string | null>(null);

  protected readonly source = new TableSource<LookupValue>('lookups/values/', {
    sort: { active: 'sort_order', direction: 'asc' },
    filters: { type: 'ticket_category', is_active: '' },
    lockedFilters: ['type'],
    pageSize: 25,
  });

  protected readonly columns: TableColumn<LookupValue>[] = [
    { key: 'sort_order', label: 'Order', sortField: 'sort_order', width: '90px' },
    { key: 'label', label: 'Value', sortField: 'label' },
    { key: 'code', label: 'Code', sortField: 'code', hideBelow: 'sm' },
    { key: 'is_default', label: 'Default', width: '90px', hideBelow: 'sm' },
    { key: 'is_active', label: 'Active', sortField: 'is_active', width: '110px' },
    { key: 'updated_at', label: 'Updated', sortField: 'updated_at', hideBelow: 'sm', value: (v) => new Date(v.updated_at).toLocaleDateString() },
    { key: 'actions', label: '', width: '110px', align: 'end' },
  ];

  /** Lists whose values are built into the app (e-mail events): rename / switch on-off only. */
  protected readonly isBuiltIn = computed(() => this.activeType()?.code === 'notification_event');

  protected typeIcon(code: string): string {
    const icons: Record<string, string> = { ticket_priority: 'flag', notification_event: 'notifications' };
    return icons[code] ?? 'category';
  }

  ngOnInit(): void {
    this.lookups.types().subscribe({
      next: (types) => {
        this.types.set(types);
        this.activeType.set(types.find((t) => t.code === 'ticket_category') ?? types[0] ?? null);
      },
      error: (error: unknown) => this.notify.error(errorMessage(error)),
    });
  }

  protected selectType(code: string): void {
    const type = this.types().find((t) => t.code === code) ?? null;
    this.activeType.set(type);
    this.source.setFilter('type', code);
  }

  protected openDialog(value?: LookupValue): void {
    const type = this.activeType();
    if (!type) return;
    this.dialog
      .open<LookupValueDialog, LookupValueDialogData, LookupValue>(LookupValueDialog, {
        data: { type, value },
        width: '640px',
        maxWidth: '95vw',
      })
      .afterClosed()
      .subscribe((saved) => {
        if (!saved) return;
        this.notify.success(`"${saved.label}" ${value ? 'updated' : 'added'}.`);
        this.afterChange();
      });
  }

  protected toggleActive(value: LookupValue, active: boolean): void {
    this.busyId.set(value.id);
    this.lookups.update(value.id, { is_active: active }).subscribe({
      next: () => {
        this.busyId.set(null);
        this.notify.success(`"${value.label}" is now ${active ? 'active' : 'hidden from new tickets'}.`);
        this.afterChange();
      },
      error: (error: unknown) => {
        this.busyId.set(null);
        this.notify.error(errorMessage(error));
        this.source.load();
      },
    });
  }

  protected remove(value: LookupValue): void {
    const data: ConfirmDialogData = {
      title: `Delete "${value.label}"?`,
      message:
        'This permanently removes the value. Values that are used by tickets cannot be deleted - deactivate them instead.',
      confirmLabel: 'Delete',
      icon: 'delete',
      danger: true,
    };
    this.dialog
      .open<ConfirmDialog, ConfirmDialogData, boolean>(ConfirmDialog, { data, width: '440px' })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.lookups.remove(value.id).subscribe({
          next: () => {
            this.notify.success(`"${value.label}" deleted.`);
            this.afterChange();
          },
          error: (error: unknown) => this.notify.error(errorMessage(error)),
        });
      });
  }

  /** Reload the table and the app-wide config so forms pick up the change. */
  private afterChange(): void {
    this.source.load();
    this.config.load().subscribe();
    this.lookups.types().subscribe((types) => this.types.set(types));
  }
}
