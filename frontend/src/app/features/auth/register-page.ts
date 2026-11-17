import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { NotifyService } from '../../core/services/notify.service';
import { applyServerErrors, errorMessage } from '../../core/utils/api-errors';
import { BrandPanel } from './brand-panel';

/** Marks confirm_password invalid when it differs from password. */
function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const password = group.get('password')?.value;
  const confirm = group.get('confirm_password');
  if (!confirm) return null;
  const mismatch = !!confirm.value && password !== confirm.value;
  if (mismatch) {
    confirm.setErrors({ ...(confirm.errors ?? {}), mismatch: true });
  } else if (confirm.hasError('mismatch')) {
    const { mismatch: _removed, ...rest } = confirm.errors ?? {};
    confirm.setErrors(Object.keys(rest).length ? rest : null);
  }
  return null;
}

@Component({
  selector: 'app-register-page',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    BrandPanel,
  ],
  templateUrl: './register-page.html',
  styleUrl: './auth-layout.scss',
})
export class RegisterPage {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly notify = inject(NotifyService);

  protected readonly form = inject(FormBuilder).nonNullable.group(
    {
      first_name: ['', [Validators.required, Validators.maxLength(150)]],
      last_name: ['', [Validators.maxLength(150)]],
      username: ['', [Validators.required, Validators.pattern(/^[\w.@+-]+$/), Validators.maxLength(150)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', Validators.required],
    },
    { validators: passwordsMatch },
  );
  protected readonly hidePassword = signal(true);
  protected readonly submitting = signal(false);
  protected readonly error = signal<string | null>(null);

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.auth.register(this.form.getRawValue()).subscribe({
      next: ({ user }) => {
        this.notify.success(`Welcome, ${user.first_name || user.username}! Your account is ready.`);
        void this.router.navigate(['/dashboard']);
      },
      error: (error: unknown) => {
        this.submitting.set(false);
        const unmatched = applyServerErrors(this.form, error);
        this.error.set(unmatched[0] ?? errorMessage(error));
      },
    });
  }
}
