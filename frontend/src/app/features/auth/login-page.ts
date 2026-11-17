import { Component, OnInit, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router, RouterLink } from '@angular/router';

import { DemoAccount } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { applyServerErrors, errorMessage } from '../../core/utils/api-errors';
import { BrandPanel } from './brand-panel';

@Component({
  selector: 'app-login-page',
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
  templateUrl: './login-page.html',
  styleUrl: './auth-layout.scss',
})
export class LoginPage implements OnInit {
  /** Bound from the query string (?returnUrl=...&expired=1). */
  readonly returnUrl = input<string>();
  readonly expired = input<string>();

  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly form = inject(FormBuilder).nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required],
  });
  protected readonly hidePassword = signal(true);
  protected readonly submitting = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly demoAccounts = signal<DemoAccount[]>([]);

  ngOnInit(): void {
    if (this.expired()) {
      this.error.set('Your session has expired. Please sign in again.');
    }
    this.auth.demoAccounts().subscribe((accounts) => this.demoAccounts.set(accounts));
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { username, password } = this.form.getRawValue();
    this.signIn(username, password);
  }

  protected useDemo(account: DemoAccount): void {
    this.form.setValue({ username: account.username, password: account.password });
    this.signIn(account.username, account.password);
  }

  private signIn(username: string, password: string): void {
    this.submitting.set(true);
    this.error.set(null);
    this.auth.login(username.trim(), password).subscribe({
      next: () => {
        const target = this.returnUrl();
        void this.router.navigateByUrl(target && target.startsWith('/') ? target : '/dashboard');
      },
      error: (error: unknown) => {
        this.submitting.set(false);
        applyServerErrors(this.form, error);
        this.error.set(errorMessage(error, 'Sign in failed. Please try again.'));
      },
    });
  }
}
