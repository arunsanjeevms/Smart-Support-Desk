import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

/** Page title with icon, description and an actions slot on the right. */
@Component({
  selector: 'app-page-header',
  imports: [MatIconModule],
  template: `
    <header class="page-header">
      @if (icon()) {
        <span class="icon" aria-hidden="true"><mat-icon>{{ icon() }}</mat-icon></span>
      }
      <div class="titles">
        <ng-content select="[headerEyebrow]" />
        <h1>{{ title() }}</h1>
        @if (description()) {
          <p>{{ description() }}</p>
        }
      </div>
      <div class="actions"><ng-content /></div>
    </header>
  `,
  styles: `
    .page-header {
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .icon {
      display: grid;
      place-items: center;
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: var(--app-surface);
      border: 1px solid var(--app-border);
      box-shadow: var(--app-shadow-xs);
      color: var(--app-primary);
    }
    .titles {
      flex: 1 1 280px;
      min-width: 0;
    }
    h1 {
      font-size: 22px;
      line-height: 1.3;
    }
    p {
      color: var(--app-text-muted);
      margin-top: 2px;
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .actions:empty {
      display: none;
    }
  `,
})
export class PageHeader {
  readonly title = input.required<string>();
  readonly description = input('');
  readonly icon = input('');
}
