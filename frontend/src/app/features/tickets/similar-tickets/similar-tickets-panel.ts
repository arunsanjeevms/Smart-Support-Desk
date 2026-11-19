import {
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  untracked,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';

import { SimilarTicket, SimilarTicketsResponse } from '../../../core/models/api.models';
import { AuthService } from '../../../core/services/auth.service';
import { ConfigService } from '../../../core/services/config.service';
import { TicketService } from '../../../core/services/ticket.service';
import { errorMessage } from '../../../core/utils/api-errors';
import { LookupBadge } from '../../../shared/components/lookup-badge';
import { StatusBadge } from '../../../shared/components/status-badge';
import {
  SimilarTicketDialog,
  SimilarTicketDialogData,
  SimilarTicketDialogResult,
} from './similar-ticket-dialog';
import { similarText, similarityPercent } from './similar-text';

type SearchState = 'idle' | 'loading' | 'done' | 'error';

/**
 * "Similar resolved tickets" - up to three resolved tickets whose text looks like
 * the issue being described, ranked by the backend's text-similarity model.
 *
 * * ``draft`` mode (New ticket form): the user asks for suggestions with a button;
 *   if they edit the text afterwards, the panel offers to search again.
 * * ``ticket`` mode (an agent on an open ticket): searches straight away and lets
 *   the agent copy a resolution note into the Manage form.
 *
 * Suggestions are advisory only - nothing here changes or closes a ticket.
 */
@Component({
  selector: 'app-similar-tickets',
  imports: [MatButtonModule, MatIconModule, MatProgressSpinnerModule, MatTooltipModule, LookupBadge, StatusBadge],
  templateUrl: './similar-tickets-panel.html',
  styleUrl: './similar-tickets-panel.scss',
  host: { '[class.ticket-mode]': "mode() === 'ticket'" },
})
export class SimilarTicketsPanel {
  readonly mode = input<'draft' | 'ticket'>('draft');
  readonly title = input<string | null | undefined>('');
  readonly description = input<string | null | undefined>('');
  /** The category picked on the form, to point out suggestions from the same category. */
  readonly categoryId = input<string | null | undefined>(null);
  /** Ticket to leave out of the results (the one being viewed). */
  readonly excludeId = input<string | null>(null);
  /** The agent chose to reuse a suggestion's resolution note. */
  readonly useNote = output<SimilarTicket>();

  protected readonly config = inject(ConfigService);
  private readonly auth = inject(AuthService);
  private readonly tickets = inject(TicketService);
  private readonly dialog = inject(MatDialog);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly state = signal<SearchState>('idle');
  protected readonly response = signal<SimilarTicketsResponse | null>(null);
  protected readonly error = signal<string | null>(null);
  private readonly searchedKey = signal<string | null>(null);
  private request?: Subscription;

  protected readonly enabled = computed(() => this.config.similarity().enabled);
  protected readonly text = computed(() => similarText(this.title(), this.description()));
  private readonly key = computed(() => `${this.excludeId() ?? ''}|${this.text()}`);
  protected readonly canSearch = computed(() => this.text().length >= this.config.similarity().min_length);
  protected readonly results = computed(() => this.response()?.results ?? []);
  protected readonly usedKeywords = computed(() => this.response()?.engine === 'keyword');
  /** The text was edited after the last search. */
  protected readonly stale = computed(
    () => this.state() === 'done' && this.searchedKey() !== null && this.searchedKey() !== this.key(),
  );
  protected readonly buttonLabel = computed(() => {
    if (this.state() === 'loading') return 'Searching…';
    return this.state() === 'idle' ? 'Find similar tickets' : 'Search again';
  });

  protected readonly percent = similarityPercent;

  constructor() {
    // Ticket mode: look as soon as the ticket is known (and again if another ticket is opened).
    effect(() => {
      const key = this.key();
      if (this.mode() !== 'ticket' || !this.enabled() || !this.canSearch()) return;
      if (untracked(() => this.searchedKey()) !== key) {
        untracked(() => this.search());
      }
    });
  }

  search(): void {
    if (!this.canSearch()) return;
    const key = this.key();
    this.request?.unsubscribe();
    this.state.set('loading');
    this.error.set(null);
    this.searchedKey.set(key);
    this.request = this.tickets
      .similar({
        title: (this.title() ?? '').trim(),
        description: (this.description() ?? '').trim(),
        exclude: this.excludeId(),
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (response) => {
          this.response.set(response);
          this.state.set('done');
        },
        error: (error: unknown) => {
          this.error.set(errorMessage(error, 'Similar tickets could not be loaded.'));
          this.state.set('error');
        },
      });
  }

  protected sameCategory(item: SimilarTicket): boolean {
    return !!this.categoryId() && item.category?.id === this.categoryId();
  }

  protected scoreHint(item: SimilarTicket): string {
    const strength = item.match === 'strong' ? 'Strong match' : 'Possible match';
    return `${strength}: how closely the meaning of the text matches (worked out by a language model)`;
  }

  protected open(item: SimilarTicket): void {
    const ticketMode = this.mode() === 'ticket';
    this.dialog
      .open<SimilarTicketDialog, SimilarTicketDialogData, SimilarTicketDialogResult>(SimilarTicketDialog, {
        data: {
          ticket: item,
          sameCategory: this.sameCategory(item),
          canUseNote: ticketMode,
          canOpenTicket: this.auth.isAgent(),
        },
        maxWidth: '94vw',
        autoFocus: 'dialog',
      })
      .afterClosed()
      .subscribe((result) => {
        if (result === 'use-note') this.useNote.emit(item);
      });
  }
}
