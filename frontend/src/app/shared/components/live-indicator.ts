import { DatePipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AUTO_REFRESH_MS } from '../../core/utils/auto-refresh';

/** Small pulsing dot + "Updated 10:42:05 AM" so people know the data refreshes itself. */
@Component({
  selector: 'app-live-indicator',
  imports: [DatePipe, MatTooltipModule],
  template: `
    <span class="live" [matTooltip]="'Refreshes automatically every ' + seconds + ' seconds'">
      <span class="dot" aria-hidden="true"></span>
      @if (updatedAt(); as time) {
        Updated {{ time | date: 'h:mm:ss a' }}
      } @else {
        Live
      }
    </span>
  `,
  styles: `
    .live {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      border: 1px solid #bfe8cf;
      background: #ecf9f0;
      color: #166534;
      font-size: 12.5px;
      font-weight: 500;
      white-space: nowrap;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #16a34a;
      animation: pulse 2s ease-out infinite;
    }
    @keyframes pulse {
      0% {
        box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.5);
      }
      70%,
      100% {
        box-shadow: 0 0 0 7px rgba(22, 163, 74, 0);
      }
    }
  `,
})
export class LiveIndicator {
  /** When the data was last loaded; shows "Live" until the first load finishes. */
  readonly updatedAt = input<Date | null>(null);
  protected readonly seconds = AUTO_REFRESH_MS / 1000;
}
