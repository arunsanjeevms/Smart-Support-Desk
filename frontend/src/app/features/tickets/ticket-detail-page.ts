import { DatePipe } from '@angular/common';
import {
  Component,
  ElementRef,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import {
  LookupOption,
  SimilarTicket,
  TicketActivity,
  TicketDetail,
  TicketStatus,
  TicketUpdatePayload,
} from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { ConfigService } from '../../core/services/config.service';
import { NotifyService } from '../../core/services/notify.service';
import { TicketService } from '../../core/services/ticket.service';
import { applyServerErrors, errorMessage } from '../../core/utils/api-errors';
import { LookupBadge } from '../../shared/components/lookup-badge';
import { StatusBadge } from '../../shared/components/status-badge';
import { UserAvatar } from '../../shared/components/user-avatar';
import { RelativeTimePipe } from '../../shared/pipes/relative-time.pipe';
import { SimilarTicketsPanel } from './similar-tickets/similar-tickets-panel';

@Component({
  selector: 'app-ticket-detail-page',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    RouterLink,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatTooltipModule,
    StatusBadge,
    LookupBadge,
    UserAvatar,
    RelativeTimePipe,
    SimilarTicketsPanel,
  ],
  templateUrl: './ticket-detail-page.html',
  styleUrl: './ticket-detail-page.scss',
})
export class TicketDetailPage {
  /** Route parameter :id (bound by withComponentInputBinding). */
  readonly id = input.required<string>();

  protected readonly auth = inject(AuthService);
  protected readonly config = inject(ConfigService);
  private readonly tickets = inject(TicketService);
  private readonly notify = inject(NotifyService);
  private readonly fb = inject(FormBuilder);

  protected readonly ticket = signal<TicketDetail | null>(null);
  protected readonly activities = signal<TicketActivity[]>([]);
  protected readonly loading = signal(true);
  protected readonly loadError = signal<string | null>(null);
  protected readonly saving = signal(false);
  protected readonly saveError = signal<string | null>(null);
  protected readonly posting = signal(false);

  protected readonly rules = this.config.validation();

  /** Agent panel. */
  protected readonly manageForm = this.fb.nonNullable.group({
    status: ['' as TicketStatus | ''],
    resolution_note: [''],
    assigned_to: [''],
    priority: [''],
    category: [''],
  });
  protected readonly commentForm = this.fb.nonNullable.group({
    message: ['', [Validators.required, Validators.maxLength(2000)]],
  });

  private readonly noteField = viewChild<ElementRef<HTMLTextAreaElement>>('noteField');

  private readonly manageValues = toSignal(this.manageForm.valueChanges, {
    initialValue: this.manageForm.getRawValue(),
  });

  protected readonly statusOptions = computed(() => {
    const ticket = this.ticket();
    if (!ticket) return [];
    const allowed = new Set([ticket.status, ...ticket.allowed_statuses.map((s) => s.value)]);
    return this.config.statuses().filter((s) => allowed.has(s.value));
  });

  protected readonly resolving = computed(() => this.manageValues().status === 'resolved');

  protected readonly isDirty = computed(() => {
    const ticket = this.ticket();
    const value = this.manageValues();
    if (!ticket) return false;
    return (
      value.status !== ticket.status ||
      (value.resolution_note ?? '').trim() !== ticket.resolution_note ||
      (value.assigned_to ?? '') !== (ticket.assigned_to?.id ?? '') ||
      (value.priority ?? '') !== (ticket.priority?.id ?? '') ||
      (value.category ?? '') !== ticket.category.id
    );
  });

  /** Active categories plus the ticket's current one (it may have been deactivated). */
  protected readonly categoryOptions = computed(() => {
    const ticket = this.ticket();
    const options = this.config.categories();
    if (ticket && !options.some((c) => c.id === ticket.category.id)) {
      return [ticket.category, ...options];
    }
    return options;
  });

  constructor() {
    effect(() => {
      const id = this.id();
      untracked(() => this.load(id));
    });
  }

  protected load(id = this.id()): void {
    this.loading.set(true);
    this.loadError.set(null);
    forkJoin({ ticket: this.tickets.get(id), activities: this.tickets.activities(id) }).subscribe({
      next: ({ ticket, activities }) => {
        this.setTicket(ticket);
        this.activities.set(activities);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.loadError.set(errorMessage(error, 'This ticket could not be loaded.'));
      },
    });
  }

  private setTicket(ticket: TicketDetail): void {
    this.ticket.set(ticket);
    this.manageForm.reset({
      status: ticket.status,
      resolution_note: ticket.resolution_note,
      assigned_to: ticket.assigned_to?.id ?? '',
      priority: ticket.priority?.id ?? '',
      category: ticket.category.id,
    });
    this.saveError.set(null);
  }

  private refreshActivities(): void {
    this.tickets.activities(this.id()).subscribe((activities) => this.activities.set(activities));
  }

  // ---------------------------------------------------------------- agent actions
  /**
   * Copy a similar ticket's resolution note into the Manage form. Nothing is
   * saved - the agent reviews and edits it, then decides whether to resolve.
   */
  protected useSimilarNote(similar: SimilarTicket): void {
    const control = this.manageForm.controls.resolution_note;
    const current = control.value.trim();
    control.setValue(current ? `${current}\n\n${similar.resolution_note}` : similar.resolution_note);
    control.markAsDirty();
    this.notify.info(`Copied the resolution note from ${similar.reference}. Review it, then save.`);
    const field = this.noteField()?.nativeElement;
    if (field) {
      field.scrollIntoView({ block: 'center', behavior: 'smooth' });
      field.focus({ preventScroll: true });
    }
  }

  protected save(): void {
    const ticket = this.ticket();
    if (!ticket) return;
    const value = this.manageForm.getRawValue();
    const note = value.resolution_note.trim();

    if (value.status === 'resolved' && note.length < this.rules.resolution_min) {
      const control = this.manageForm.controls.resolution_note;
      control.setErrors({ resolutionRequired: true });
      control.markAsTouched();
      this.saveError.set('Add a resolution note before marking the ticket as resolved.');
      return;
    }

    const payload: TicketUpdatePayload = {};
    if (value.status && value.status !== ticket.status) payload.status = value.status;
    if (note !== ticket.resolution_note) payload.resolution_note = note;
    if (value.assigned_to !== (ticket.assigned_to?.id ?? '')) payload.assigned_to = value.assigned_to || null;
    if (value.priority !== (ticket.priority?.id ?? '')) payload.priority = value.priority || null;
    if (value.category !== ticket.category.id) payload.category = value.category;
    this.update(payload, 'Ticket updated.');
  }

  protected assignToMe(): void {
    const me = this.auth.user();
    if (me) this.update({ assigned_to: me.id }, 'The ticket is now assigned to you.');
  }

  protected startProgress(): void {
    this.update({ status: 'in_progress' }, 'Marked as in progress.');
  }

  protected discard(): void {
    const ticket = this.ticket();
    if (ticket) this.setTicket(ticket);
  }

  private update(payload: TicketUpdatePayload, successMessage: string): void {
    const ticket = this.ticket();
    if (!ticket || Object.keys(payload).length === 0) return;
    this.saving.set(true);
    this.saveError.set(null);
    this.tickets.update(ticket.id, payload).subscribe({
      next: (updated) => {
        this.saving.set(false);
        this.setTicket(updated);
        this.refreshActivities();
        this.notify.success(successMessage);
      },
      error: (error: unknown) => {
        this.saving.set(false);
        const unmatched = applyServerErrors(this.manageForm, error);
        this.saveError.set(unmatched[0] ?? errorMessage(error, 'The ticket could not be updated.'));
      },
    });
  }

  // ---------------------------------------------------------------- comments
  protected postComment(): void {
    const ticket = this.ticket();
    const message = this.commentForm.getRawValue().message.trim();
    if (!ticket || !message) {
      this.commentForm.markAllAsTouched();
      return;
    }
    this.posting.set(true);
    this.tickets.comment(ticket.id, message).subscribe({
      next: (entry) => {
        this.posting.set(false);
        this.commentForm.reset();
        this.activities.update((list) => [...list, entry]);
      },
      error: (error: unknown) => {
        this.posting.set(false);
        this.notify.error(errorMessage(error, 'Your comment could not be posted.'));
      },
    });
  }

  protected agentName(id: string): string {
    if (!id) return 'Unassigned';
    const agent = this.config.agents().find((a) => a.id === id);
    return agent ? agent.full_name + (agent.id === this.auth.user()?.id ? ' (me)' : '') : 'Unknown agent';
  }

  protected optionLabel(options: LookupOption[], id: string): string {
    return options.find((option) => option.id === id)?.label ?? '';
  }
}
