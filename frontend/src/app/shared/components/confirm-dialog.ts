import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

export interface ConfirmDialogData {
  title: string;
  message: string;
  confirmLabel?: string;
  icon?: string;
  danger?: boolean;
}

/** Generic confirmation dialog. Closes with `true` when confirmed. */
@Component({
  selector: 'app-confirm-dialog',
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <h2 mat-dialog-title class="title">
      <span class="icon" [class.danger]="data.danger">
        <mat-icon>{{ data.icon ?? 'help' }}</mat-icon>
      </span>
      {{ data.title }}
    </h2>
    <mat-dialog-content>
      <p>{{ data.message }}</p>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button [mat-dialog-close]="false">Cancel</button>
      <button
        mat-flat-button
        [class.danger-button]="data.danger"
        [mat-dialog-close]="true"
        cdkFocusInitial
      >
        {{ data.confirmLabel ?? 'Confirm' }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    .title {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .icon {
      display: grid;
      place-items: center;
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: var(--app-primary-soft);
      color: var(--app-primary);
    }
    .icon.danger {
      background: var(--app-danger-soft);
      color: var(--app-danger);
    }
    .danger-button {
      --mat-button-filled-container-color: #b42318;
    }
  `,
})
export class ConfirmDialog {
  protected readonly data = inject<ConfirmDialogData>(MAT_DIALOG_DATA);
}
