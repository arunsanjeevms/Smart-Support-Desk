import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { Router, RouterLink } from '@angular/router';

import { TicketDetail } from '../../core/models/api.models';
import { AttachmentService } from '../../core/services/attachment.service';
import { AuthService } from '../../core/services/auth.service';
import { ConfigService } from '../../core/services/config.service';
import { NotifyService } from '../../core/services/notify.service';
import { TicketService } from '../../core/services/ticket.service';
import { applyServerErrors, errorMessage, fileErrorMessage } from '../../core/utils/api-errors';
import { FilePicker } from '../../shared/attachments/file-picker';
import { PageHeader } from '../../shared/components/page-header';
import { SimilarTicketsPanel } from './similar-tickets/similar-tickets-panel';

/** Rejects values that are only whitespace. */
function notBlank(control: { value: string }) {
  return control.value && !control.value.trim() ? { required: true } : null;
}

@Component({
  selector: 'app-ticket-create-page',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    FilePicker,
    MatSelectModule,
    PageHeader,
    SimilarTicketsPanel,
  ],
  templateUrl: './ticket-create-page.html',
  styleUrl: './ticket-create-page.scss',
})
export class TicketCreatePage {
  protected readonly config = inject(ConfigService);
  protected readonly auth = inject(AuthService);
  private readonly tickets = inject(TicketService);
  private readonly attachments = inject(AttachmentService);
  private readonly notify = inject(NotifyService);
  private readonly router = inject(Router);

  protected readonly rules = this.config.validation();

  protected readonly form = inject(FormBuilder).nonNullable.group({
    title: [
      '',
      [
        Validators.required,
        notBlank,
        Validators.minLength(this.rules.title_min),
        Validators.maxLength(this.rules.title_max),
      ],
    ],
    category: ['', Validators.required],
    priority: [this.config.defaultPriority()?.id ?? ''],
    description: [
      '',
      [
        Validators.required,
        notBlank,
        Validators.minLength(this.rules.description_min),
        Validators.maxLength(this.rules.description_max),
      ],
    ],
  });

  protected readonly submitting = signal(false);
  /** Files chosen in the Attachments picker (uploaded right after the ticket is created). */
  protected readonly files = signal<File[]>([]);
  /** Upload progress in percent while the files are being sent, otherwise null. */
  protected readonly uploadPercent = signal<number | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly values = toSignal(this.form.valueChanges, { initialValue: this.form.getRawValue() });
  protected readonly titleLength = computed(() => this.values().title?.length ?? 0);
  protected readonly descriptionLength = computed(() => this.values().description?.length ?? 0);
  protected readonly selectedPriority = computed(() =>
    this.config.priorities().find((p) => p.id === this.values().priority),
  );
  protected readonly selectedCategory = computed(() =>
    this.config.categories().find((c) => c.id === this.values().category),
  );

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.error.set('Please fix the highlighted fields before submitting.');
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    const { title, description, category, priority } = this.form.getRawValue();
    this.tickets
      .create({ title: title.trim(), description: description.trim(), category, priority: priority || null })
      .subscribe({
        next: (ticket) => this.uploadFiles(ticket),
        error: (error: unknown) => {
          this.submitting.set(false);
          const unmatched = applyServerErrors(this.form, error);
          this.error.set(unmatched[0] ?? errorMessage(error, 'The ticket could not be created.'));
        },
      });
  }

  protected reset(): void {
    this.form.reset({ priority: this.config.defaultPriority()?.id ?? '' });
    this.files.set([]);
    this.error.set(null);
  }

  /** Sends the chosen files once the ticket exists, then opens the ticket. */
  private uploadFiles(ticket: TicketDetail): void {
    const files = this.files();
    if (!files.length) {
      this.finish(ticket, 0);
      return;
    }
    this.uploadPercent.set(0);
    this.attachments.upload(ticket.id, files).subscribe({
      next: (progress) => {
        this.uploadPercent.set(progress.percent);
        if (progress.attachments) this.finish(ticket, progress.attachments.length);
      },
      error: (error: unknown) => {
        // The ticket itself was created - say so, and let the user add the files on the ticket page.
        this.notify.error(
          `Ticket ${ticket.reference} was created, but the files were not attached: ` +
            `${fileErrorMessage(error, 'the upload failed.')} You can add them on the ticket page.`,
        );
        void this.router.navigate(['/tickets', ticket.id]);
      },
    });
  }

  private finish(ticket: TicketDetail, fileCount: number): void {
    const files = fileCount ? ` with ${fileCount} ${fileCount === 1 ? 'file' : 'files'}` : '';
    this.notify.success(`Ticket ${ticket.reference} created${files}. We'll keep you posted.`);
    void this.router.navigate(['/tickets', ticket.id]);
  }
}
