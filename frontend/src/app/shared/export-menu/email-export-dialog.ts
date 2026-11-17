import { COMMA, ENTER, SEMICOLON, SPACE } from '@angular/cdk/keycodes';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipInputEvent, MatChipsModule } from '@angular/material/chips';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';

import { ExportFileType } from '../../core/models/api.models';
import { QueryParams } from '../../core/services/api.service';
import { ConfigService } from '../../core/services/config.service';
import { ExportService } from '../../core/services/export.service';
import { applyServerErrors, errorMessage } from '../../core/utils/api-errors';

export interface EmailExportDialogData {
  endpoint: string;
  params: QueryParams;
  title: string;
  defaultRecipient?: string;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_RECIPIENTS = 10;

@Component({
  selector: 'app-email-export-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatRadioModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <h2 mat-dialog-title class="dialog-title">
      <span class="title-icon"><mat-icon>forward_to_inbox</mat-icon></span>
      Email {{ data.title.toLowerCase() }}
    </h2>

    <form [formGroup]="form" (ngSubmit)="send()" novalidate>
      <mat-dialog-content class="content">
        <p class="muted intro">
          The report is generated on the server with your current search, filters and sorting, and
          sent as an attachment.
        </p>

        @if (error()) {
          <div class="alert error" role="alert"><mat-icon>error</mat-icon>{{ error() }}</div>
        }

        <mat-form-field appearance="outline">
          <mat-label>Recipients</mat-label>
          <mat-chip-grid #chipGrid aria-label="Recipient email addresses">
            @for (email of recipients(); track email) {
              <mat-chip-row (removed)="removeRecipient(email)">
                {{ email }}
                <button matChipRemove [attr.aria-label]="'Remove ' + email">
                  <mat-icon>cancel</mat-icon>
                </button>
              </mat-chip-row>
            }
            <input
              placeholder="name@company.com"
              [matChipInputFor]="chipGrid"
              [matChipInputSeparatorKeyCodes]="separators"
              [matChipInputAddOnBlur]="true"
              (matChipInputTokenEnd)="addRecipient($event)"
            />
          </mat-chip-grid>
          <mat-icon matPrefix>alternate_email</mat-icon>
          <mat-hint>Press Enter or comma after each address (up to {{ maxRecipients }}).</mat-hint>
        </mat-form-field>
        @if (recipientError()) {
          <p class="field-error" role="alert">{{ recipientError() }}</p>
        }

        <div class="format">
          <span class="format-label">Attachment format</span>
          <mat-radio-group formControlName="file_type" aria-label="Attachment format">
            @for (format of config.exportFormats(); track format.value) {
              <mat-radio-button [value]="format.value">
                <span class="option-with-icon">
                  <mat-icon>{{ format.value === 'pdf' ? 'picture_as_pdf' : 'table_view' }}</mat-icon>
                  {{ format.label }}
                </span>
              </mat-radio-button>
            }
          </mat-radio-group>
        </div>

        <mat-form-field appearance="outline">
          <mat-label>Subject (optional)</mat-label>
          <input matInput formControlName="subject" maxlength="150" />
          <mat-icon matPrefix>subject</mat-icon>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Message (optional)</mat-label>
          <textarea matInput formControlName="message" rows="3" maxlength="2000"></textarea>
        </mat-form-field>
      </mat-dialog-content>

      <mat-dialog-actions align="end">
        <button mat-button type="button" mat-dialog-close [disabled]="sending()">Cancel</button>
        <button mat-flat-button type="submit" [disabled]="sending()">
          @if (sending()) {
            <mat-progress-spinner diameter="18" mode="indeterminate" />
          } @else {
            <mat-icon>send</mat-icon>
          }
          Send report
        </button>
      </mat-dialog-actions>
    </form>
  `,
  styles: `
    .dialog-title {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .title-icon {
      display: grid;
      place-items: center;
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: var(--app-primary-soft);
      color: var(--app-primary);
    }
    .content {
      display: flex;
      flex-direction: column;
      gap: 6px;
      min-width: min(480px, 80vw);
    }
    .intro {
      margin-bottom: 8px;
    }
    .format {
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      margin: 8px 0 16px;
    }
    .format-label {
      font-weight: 500;
      color: var(--app-text-secondary);
    }
    .field-error {
      color: var(--app-danger);
      font-size: 12px;
      margin: -4px 0 8px 16px;
    }
    mat-progress-spinner {
      margin-right: 8px;
    }
  `,
})
export class EmailExportDialog {
  protected readonly data = inject<EmailExportDialogData>(MAT_DIALOG_DATA);
  protected readonly config = inject(ConfigService);
  private readonly exports = inject(ExportService);
  private readonly dialogRef = inject(MatDialogRef<EmailExportDialog, string>);

  protected readonly separators = [ENTER, COMMA, SEMICOLON, SPACE];
  protected readonly maxRecipients = MAX_RECIPIENTS;
  protected readonly recipients = signal<string[]>(
    this.data.defaultRecipient ? [this.data.defaultRecipient] : [],
  );
  protected readonly recipientError = signal<string | null>(null);
  protected readonly sending = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly form = inject(FormBuilder).nonNullable.group({
    file_type: ['pdf' as ExportFileType, Validators.required],
    subject: [''],
    message: [''],
  });

  addRecipient(event: MatChipInputEvent): void {
    const email = event.value.trim();
    event.chipInput.clear();
    if (!email) return;
    if (!EMAIL_PATTERN.test(email)) {
      this.recipientError.set(`"${email}" doesn't look like a valid email address.`);
      return;
    }
    if (this.recipients().length >= MAX_RECIPIENTS) {
      this.recipientError.set(`You can send to at most ${MAX_RECIPIENTS} people at once.`);
      return;
    }
    if (!this.recipients().some((r) => r.toLowerCase() === email.toLowerCase())) {
      this.recipients.update((list) => [...list, email]);
    }
    this.recipientError.set(null);
  }

  removeRecipient(email: string): void {
    this.recipients.update((list) => list.filter((r) => r !== email));
  }

  send(): void {
    if (this.recipients().length === 0) {
      this.recipientError.set('Add at least one recipient email address.');
      return;
    }
    this.sending.set(true);
    this.error.set(null);
    const { file_type, subject, message } = this.form.getRawValue();
    this.exports
      .email(this.data.endpoint, this.data.params, {
        file_type,
        recipients: this.recipients(),
        subject: subject.trim() || undefined,
        message: message.trim() || undefined,
      })
      .subscribe({
        next: (response) => this.dialogRef.close(response.message),
        error: (error: unknown) => {
          this.sending.set(false);
          const unmatched = applyServerErrors(this.form, error);
          this.error.set(unmatched[0] ?? errorMessage(error, 'The report could not be sent.'));
        },
      });
  }
}
