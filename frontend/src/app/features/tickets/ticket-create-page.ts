import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ConfigService } from '../../core/services/config.service';
import { NotifyService } from '../../core/services/notify.service';
import { TicketService } from '../../core/services/ticket.service';
import { applyServerErrors, errorMessage } from '../../core/utils/api-errors';
import { PageHeader } from '../../shared/components/page-header';

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
    MatProgressSpinnerModule,
    MatSelectModule,
    PageHeader,
  ],
  templateUrl: './ticket-create-page.html',
  styleUrl: './ticket-create-page.scss',
})
export class TicketCreatePage {
  protected readonly config = inject(ConfigService);
  protected readonly auth = inject(AuthService);
  private readonly tickets = inject(TicketService);
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
  protected readonly error = signal<string | null>(null);

  private readonly values = toSignal(this.form.valueChanges, { initialValue: this.form.getRawValue() });
  protected readonly titleLength = computed(() => this.values().title?.length ?? 0);
  protected readonly descriptionLength = computed(() => this.values().description?.length ?? 0);
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
        next: (ticket) => {
          this.notify.success(`Ticket ${ticket.reference} created. We'll keep you posted.`);
          void this.router.navigate(['/tickets', ticket.id]);
        },
        error: (error: unknown) => {
          this.submitting.set(false);
          const unmatched = applyServerErrors(this.form, error);
          this.error.set(unmatched[0] ?? errorMessage(error, 'The ticket could not be created.'));
        },
      });
  }

  protected reset(): void {
    this.form.reset({ priority: this.config.defaultPriority()?.id ?? '' });
    this.error.set(null);
  }
}
