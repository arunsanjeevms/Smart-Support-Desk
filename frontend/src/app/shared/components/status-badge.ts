import { Component, computed, inject, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

import { ConfigService } from '../../core/services/config.service';

/** Coloured status pill. Label, icon and colour come from the backend config. */
@Component({
  selector: 'app-status-badge',
  imports: [MatIconModule],
  template: `
    <span
      class="badge"
      [style.--badge-color]="meta()?.color ?? '#667085'"
      [attr.title]="meta()?.description"
    >
      <mat-icon aria-hidden="true">{{ meta()?.icon ?? 'help' }}</mat-icon>
      {{ meta()?.label ?? status() }}
    </span>
  `,
  styles: `
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      height: 26px;
      padding: 0 10px 0 7px;
      border-radius: 999px;
      font-size: 12.5px;
      font-weight: 600;
      white-space: nowrap;
      color: color-mix(in srgb, var(--badge-color) 82%, black);
      background: color-mix(in srgb, var(--badge-color) 9%, white);
      border: 1px solid color-mix(in srgb, var(--badge-color) 24%, white);
    }
    .mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
    }
  `,
})
export class StatusBadge {
  readonly status = input.required<string>();
  private readonly config = inject(ConfigService);
  protected readonly meta = computed(() => this.config.status(this.status()));
}
