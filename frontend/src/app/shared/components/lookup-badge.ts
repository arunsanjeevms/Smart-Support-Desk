import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

import { LookupOption } from '../../core/models/api.models';

/** Category / priority label with its configured icon and colour. */
@Component({
  selector: 'app-lookup-badge',
  imports: [MatIconModule],
  template: `
    @if (option(); as item) {
      <span class="lookup" [class.plain]="plain()" [style.--lookup-color]="item.color || '#667085'">
        <mat-icon aria-hidden="true">{{ item.icon || 'label' }}</mat-icon>
        {{ item.label }}
      </span>
    } @else {
      <span class="muted">—</span>
    }
  `,
  styles: `
    .lookup {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 9px 3px 6px;
      border-radius: 6px;
      font-size: 12.5px;
      font-weight: 500;
      white-space: nowrap;
      color: var(--app-text-secondary);
      background: var(--app-surface-muted);
      border: 1px solid var(--app-border);
    }
    .lookup.plain {
      padding: 0;
      background: none;
      border: 0;
    }
    .mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
      color: var(--lookup-color);
    }
  `,
})
export class LookupBadge {
  readonly option = input<LookupOption | null | undefined>(null);
  /** Render without the pill background. */
  readonly plain = input(false);
}
