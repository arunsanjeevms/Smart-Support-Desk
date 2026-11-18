import { Component, computed, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { catchError, debounceTime, distinctUntilChanged, map, of, switchMap } from 'rxjs';

import { CategorySuggestion } from '../../../core/models/api.models';
import { ConfigService } from '../../../core/services/config.service';
import { TicketService } from '../../../core/services/ticket.service';
import { LookupBadge } from '../../../shared/components/lookup-badge';
import { similarText } from '../similar-tickets/similar-text';

/** Wait this long after the last keystroke before asking the backend. */
export const SUGGEST_DEBOUNCE_MS = 600;

type HintState = 'none' | 'suggest' | 'differs' | 'match';

/**
 * Suggests the likely category while a new ticket is typed, using the backend's
 * text-similarity model (similar past tickets vote for their category).
 *
 * It only ever *suggests*: the user clicks "Use it" / "Switch" to apply it.
 */
@Component({
  selector: 'app-category-suggestion',
  imports: [MatButtonModule, MatIconModule, LookupBadge],
  template: `
    <div class="slot" role="status" aria-live="polite">
      @if (suggestion(); as s) {
        @switch (state()) {
          @case ('suggest') {
            <div class="hint">
              <mat-icon class="lead-icon">auto_awesome</mat-icon>
              <span class="lead">Suggested category</span>
              <app-lookup-badge [option]="s.category" />
              <span class="basis">{{ basis() }}</span>
              <button mat-button type="button" class="action" (click)="apply.emit(s.category.id)">
                <mat-icon>check</mat-icon>
                Use it
              </button>
            </div>
          }
          @case ('differs') {
            <div class="hint differs">
              <mat-icon class="lead-icon">lightbulb</mat-icon>
              <span class="lead">This reads like</span>
              <app-lookup-badge [option]="s.category" />
              <span class="basis">{{ basis() }}</span>
              <button mat-button type="button" class="action" (click)="apply.emit(s.category.id)">
                <mat-icon>swap_horiz</mat-icon>
                Switch
              </button>
            </div>
          }
          @case ('match') {
            <div class="hint match">
              <mat-icon class="lead-icon">check_circle</mat-icon>
              <span class="lead">Matches the suggested category</span>
              <span class="basis">{{ basis() }}</span>
            </div>
          }
        }
      }
    </div>
  `,
  styles: `
    :host {
      display: block;
    }
    .slot:empty {
      display: none;
    }
    .slot {
      margin: 2px 0 6px;
    }
    .hint {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px 10px;
      padding: 6px 6px 6px 12px;
      border-radius: var(--app-radius);
      border: 1px solid var(--app-primary-border);
      background:
        linear-gradient(90deg, rgba(20, 184, 166, 0.08), transparent 70%),
        var(--app-surface);
      font-size: 13px;
      animation: hint-in 0.3s ease-out both;

      &.differs {
        border-color: #fedf89;
        background:
          linear-gradient(90deg, rgba(245, 158, 11, 0.08), transparent 70%),
          var(--app-surface);

        .lead-icon {
          color: var(--app-warning);
        }
      }
      &.match {
        padding: 2px 0;
        border: 0;
        background: none;

        .lead-icon {
          color: var(--app-success);
        }
        .lead {
          color: var(--app-text-secondary);
          font-weight: 500;
        }
      }
    }
    .lead-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      color: var(--app-primary);
    }
    .lead {
      font-weight: 600;
      color: var(--app-text);
    }
    .basis {
      color: var(--app-text-muted);
      font-size: 12.5px;
    }
    .action {
      margin-left: auto;
    }
    @keyframes hint-in {
      from {
        opacity: 0;
        transform: translateY(-4px);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .hint {
        animation: none;
      }
    }
  `,
})
export class CategorySuggestionHint {
  readonly title = input<string | null | undefined>('');
  readonly description = input<string | null | undefined>('');
  /** The category currently chosen on the form. */
  readonly selectedId = input<string | null | undefined>(null);
  /** The user accepted the suggestion: the id of the category to use. */
  readonly apply = output<string>();

  private readonly config = inject(ConfigService);
  private readonly tickets = inject(TicketService);

  protected readonly suggestion = signal<CategorySuggestion | null>(null);
  private readonly text = computed(() => similarText(this.title(), this.description()));

  protected readonly state = computed<HintState>(() => {
    const suggestion = this.suggestion();
    if (!suggestion) return 'none';
    const selected = this.selectedId();
    if (!selected) return 'suggest';
    return selected === suggestion.category.id ? 'match' : 'differs';
  });

  protected readonly basis = computed(() => {
    const suggestion = this.suggestion();
    if (!suggestion) return '';
    if (suggestion.basis === 'category_description') return 'from the category description';
    return `based on ${suggestion.matches} similar ${suggestion.matches === 1 ? 'ticket' : 'tickets'}`;
  });

  constructor() {
    // Ask while the user types: wait for a pause, skip repeats, drop outdated answers.
    toObservable(this.text)
      .pipe(
        debounceTime(SUGGEST_DEBOUNCE_MS),
        distinctUntilChanged(),
        switchMap((text) => {
          const settings = this.config.similarity();
          if (!settings.enabled || !settings.category_suggestions || text.length < settings.min_length) {
            return of(null);
          }
          return this.tickets
            .suggestCategory({ title: (this.title() ?? '').trim(), description: (this.description() ?? '').trim() })
            .pipe(
              map((response) => response.suggestion),
              catchError(() => of(null)), // a hint is optional - never bother the user with errors
            );
        }),
        takeUntilDestroyed(),
      )
      .subscribe((suggestion) => this.suggestion.set(suggestion));
  }
}
