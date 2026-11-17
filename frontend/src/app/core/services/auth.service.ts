import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, firstValueFrom, of, tap } from 'rxjs';

import { AuthResponse, DemoAccount, RegisterPayload, User } from '../models/api.models';
import { ApiService } from './api.service';
import { ConfigService } from './config.service';

const TOKEN_KEY = 'ssd.token';

/**
 * Keeps track of who is signed in.
 *
 * The API token is stored in localStorage so a page refresh keeps the user
 * signed in; the user profile itself is always re-loaded from the API.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly config = inject(ConfigService);

  private readonly tokenSignal = signal<string | null>(readToken());
  private readonly userSignal = signal<User | null>(null);

  readonly user = this.userSignal.asReadonly();
  readonly token = this.tokenSignal.asReadonly();
  readonly isAuthenticated = computed(() => !!this.userSignal() && !!this.tokenSignal());
  readonly isAgent = computed(() => this.userSignal()?.is_agent ?? false);

  /** Called once at start-up to restore an existing session. */
  async restoreSession(): Promise<void> {
    if (!this.tokenSignal()) return;
    const user = await firstValueFrom(
      this.api.get<User>('auth/me/').pipe(catchError(() => of(null))),
    );
    if (user) {
      this.userSignal.set(user);
    } else {
      this.clearSession();
    }
  }

  login(username: string, password: string): Observable<AuthResponse> {
    return this.api
      .post<AuthResponse>('auth/login/', { username, password })
      .pipe(tap((response) => this.startSession(response)));
  }

  register(payload: RegisterPayload): Observable<AuthResponse> {
    return this.api
      .post<AuthResponse>('auth/register/', payload)
      .pipe(tap((response) => this.startSession(response)));
  }

  demoAccounts(): Observable<DemoAccount[]> {
    return this.api.get<DemoAccount[]>('auth/demo-accounts/').pipe(catchError(() => of([])));
  }

  logout(): void {
    // Best effort: invalidate the token on the server, then forget it locally.
    this.api.post('auth/logout/', {}).pipe(catchError(() => of(null))).subscribe();
    this.clearSession();
    void this.router.navigate(['/login']);
  }

  /** Forget the session without calling the API (e.g. after a 401). */
  clearSession(): void {
    writeToken(null);
    this.tokenSignal.set(null);
    this.userSignal.set(null);
    this.config.clear();
  }

  private startSession({ token, user }: AuthResponse): void {
    writeToken(token);
    this.tokenSignal.set(token);
    this.userSignal.set(user);
  }
}

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function writeToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable (private mode) - session lasts until refresh */
  }
}
