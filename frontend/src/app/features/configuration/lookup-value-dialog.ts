import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';

import { LookupType, LookupValue } from '../../core/models/api.models';
import { LookupService } from '../../core/services/lookup.service';
import { applyServerErrors, errorMessage } from '../../core/utils/api-errors';

export interface LookupValueDialogData {
  type: LookupType;
  value?: LookupValue;
}

const SUGGESTED_ICONS = [
  'bug_report', 'lock_person', 'payments', 'speed', 'hub', 'manage_accounts', 'analytics',
  'lightbulb', 'devices', 'cloud', 'mail', 'security', 'shopping_cart', 'help',
  'priority_high', 'keyboard_double_arrow_up', 'drag_handle', 'keyboard_double_arrow_down',
];

const SUGGESTED_COLORS = ['#1F4FBF', '#0891B2', '#0D9488', '#15803D', '#CA8A04', '#EA580C', '#DC2626', '#7C3AED', '#64748B'];

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 50);
}

@Component({
  selector: 'app-lookup-value-dialog',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCheckboxModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatTooltipModule,
  ],
  templateUrl: './lookup-value-dialog.html',
  styleUrl: './lookup-value-dialog.scss',
})
export class LookupValueDialog {
  protected readonly data = inject<LookupValueDialogData>(MAT_DIALOG_DATA);
  private readonly lookups = inject(LookupService);
  private readonly dialogRef = inject(MatDialogRef<LookupValueDialog, LookupValue>);

  protected readonly isEdit = !!this.data.value;
  protected readonly icons = SUGGESTED_ICONS;
  protected readonly colors = SUGGESTED_COLORS;
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  private codeTouchedByUser = this.isEdit;

  protected readonly form = inject(FormBuilder).nonNullable.group({
    label: [this.data.value?.label ?? '', [Validators.required, Validators.maxLength(100)]],
    code: [
      this.data.value?.code ?? '',
      [Validators.required, Validators.maxLength(50), Validators.pattern(/^[a-z0-9_]+$/)],
    ],
    description: [this.data.value?.description ?? '', Validators.maxLength(255)],
    icon: [this.data.value?.icon ?? 'label', Validators.maxLength(50)],
    color: [this.data.value?.color || '#1F4FBF', Validators.pattern(/^#[0-9A-Fa-f]{6}$/)],
    sort_order: [this.data.value?.sort_order ?? 100, [Validators.required, Validators.min(0)]],
    is_active: [this.data.value?.is_active ?? true],
    is_default: [this.data.value?.is_default ?? false],
  });

  protected readonly preview = toSignal(this.form.valueChanges, { initialValue: this.form.getRawValue() });

  constructor() {
    // Suggest a code from the label while creating, until the user edits the code.
    this.form.controls.label.valueChanges.subscribe((label) => {
      if (!this.codeTouchedByUser) {
        this.form.controls.code.setValue(slugify(label), { emitEvent: true });
      }
    });
  }

  protected markCodeEdited(): void {
    this.codeTouchedByUser = true;
  }

  protected pickIcon(icon: string): void {
    this.form.controls.icon.setValue(icon);
  }

  protected pickColor(color: string): void {
    this.form.controls.color.setValue(color);
  }

  protected save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    const value = this.form.getRawValue();
    const payload = { ...value, color: value.color.toUpperCase(), lookup_type: this.data.type.id };
    const request = this.data.value
      ? this.lookups.update(this.data.value.id, payload)
      : this.lookups.create(payload);

    request.subscribe({
      next: (saved) => this.dialogRef.close(saved),
      error: (error: unknown) => {
        this.saving.set(false);
        const unmatched = applyServerErrors(this.form, error);
        this.error.set(unmatched[0] ?? errorMessage(error, 'The value could not be saved.'));
      },
    });
  }
}
