import { Component, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ExportFileType } from '../../core/models/api.models';
import { QueryParams } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { ExportService } from '../../core/services/export.service';
import { NotifyService } from '../../core/services/notify.service';
import { errorMessage } from '../../core/utils/api-errors';
import { EmailExportDialog, EmailExportDialogData } from './email-export-dialog';

/** "Export" button with Download PDF / Download Excel / Email options. */
@Component({
  selector: 'app-export-menu',
  imports: [
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  template: `
    <button
      mat-stroked-button
      type="button"
      class="export-button"
      [matMenuTriggerFor]="menu"
      [disabled]="busy()"
      matTooltip="Download or email this table"
    >
      @if (busy()) {
        <mat-progress-spinner diameter="16" mode="indeterminate" />
      } @else {
        <mat-icon>ios_share</mat-icon>
      }
      Export
    </button>

    <mat-menu #menu="matMenu" xPosition="before">
      <button mat-menu-item (click)="download('pdf')">
        <mat-icon class="pdf">picture_as_pdf</mat-icon>
        <span>Download PDF</span>
      </button>
      <button mat-menu-item (click)="download('xlsx')">
        <mat-icon class="xlsx">table_view</mat-icon>
        <span>Download Excel</span>
      </button>
      <mat-divider />
      <button mat-menu-item (click)="openEmail()">
        <mat-icon>forward_to_inbox</mat-icon>
        <span>Email report…</span>
      </button>
    </mat-menu>
  `,
  styles: `
    .export-button mat-progress-spinner {
      margin-right: 8px;
    }
    .pdf {
      color: #b42318;
    }
    .xlsx {
      color: #15803d;
    }
  `,
})
export class ExportMenu {
  /** API endpoint of the table, e.g. "tickets/". */
  readonly endpoint = input.required<string>();
  /** Current search/sort/filter params of the table. */
  readonly params = input<QueryParams>({});
  /** Human title used in the dialog, e.g. "Tickets". */
  readonly title = input('Report');

  private readonly exports = inject(ExportService);
  private readonly notify = inject(NotifyService);
  private readonly dialog = inject(MatDialog);
  private readonly auth = inject(AuthService);
  protected readonly busy = signal(false);

  download(fileType: ExportFileType): void {
    this.busy.set(true);
    this.exports.download(this.endpoint(), fileType, this.params()).subscribe({
      next: (filename) => {
        this.busy.set(false);
        this.notify.success(`Downloaded ${filename}`);
      },
      error: (error: unknown) => {
        this.busy.set(false);
        this.notify.error(errorMessage(error, 'The export could not be generated.'));
      },
    });
  }

  openEmail(): void {
    const data: EmailExportDialogData = {
      endpoint: this.endpoint(),
      params: this.params(),
      title: this.title(),
      defaultRecipient: this.auth.user()?.email,
    };
    this.dialog
      .open<EmailExportDialog, EmailExportDialogData, string>(EmailExportDialog, {
        data,
        width: '560px',
        maxWidth: '95vw',
        autoFocus: 'first-tabbable',
      })
      .afterClosed()
      .subscribe((message) => {
        if (message) this.notify.success(message);
      });
  }
}
