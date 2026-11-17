import { Directive, inject, input, TemplateRef } from '@angular/core';

/** Describes one column of a DataTable. */
export interface TableColumn<T = unknown> {
  /** Unique key; also used to find a custom cell template. */
  key: string;
  label: string;
  /** API ordering field (e.g. "created_at"). Leave empty for unsortable columns. */
  sortField?: string;
  /** Plain text value when no custom template is provided. */
  value?: (row: T) => string | number | null | undefined;
  width?: string;
  align?: 'start' | 'end' | 'center';
  /** Hide the column when the screen is narrower than this breakpoint (sm < 900px, md < 1200px, lg < 1440px). */
  hideBelow?: 'sm' | 'md' | 'lg';
}

/**
 * Custom cell template:
 *   <ng-template appCell="status" let-row>
 *     <app-status-badge [status]="row.status" />
 *   </ng-template>
 */
@Directive({ selector: 'ng-template[appCell]' })
export class CellTemplate {
  readonly column = input.required<string>({ alias: 'appCell' });
  readonly template = inject<TemplateRef<{ $implicit: unknown }>>(TemplateRef);
}
