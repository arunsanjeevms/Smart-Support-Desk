import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../environments/environment';
import { AuthResponse, User } from '../models/api.models';
import { AuthService } from './auth.service';

// Stub route so logout() can navigate to the sign-in page.
const routes = [{ path: 'login', children: [] }];

const agent: User = {
  id: '6afc905d5ce249f392ca1e01',
  username: 'meera',
  full_name: 'Meera Iyer',
  email: 'meera@example.com',
  initials: 'MI',
  role: 'agent',
  first_name: 'Meera',
  last_name: 'Iyer',
  job_title: 'Support Engineer',
  role_label: 'Support Agent',
  is_agent: true,
  is_active: true,
  date_joined: '2026-11-01T10:00:00Z',
  last_login: null,
};

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter(routes)],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('starts signed out', () => {
    expect(service.isAuthenticated()).toBe(false);
    expect(service.isAgent()).toBe(false);
  });

  it('stores the token and user after a successful login', () => {
    service.login('meera', 'secret').subscribe();

    const request = http.expectOne(`${environment.apiUrl}/auth/login/`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ username: 'meera', password: 'secret' });
    request.flush({ token: 'abc123', user: agent } satisfies AuthResponse);

    expect(service.isAuthenticated()).toBe(true);
    expect(service.isAgent()).toBe(true);
    expect(localStorage.getItem('ssd.token')).toBe('abc123');
  });

  it('asks for the welcome intro once after signing in', () => {
    expect(service.consumeWelcome()).toBeNull();
    service.login('meera', 'secret').subscribe();
    http.expectOne(`${environment.apiUrl}/auth/login/`).flush({ token: 'abc123', user: agent });

    expect(service.consumeWelcome()).toBe('back');
    expect(service.consumeWelcome()).toBeNull(); // only once
  });

  it('forgets the session on logout', () => {
    service.login('meera', 'secret').subscribe();
    http.expectOne(`${environment.apiUrl}/auth/login/`).flush({ token: 'abc123', user: agent });

    service.logout();
    http.expectOne(`${environment.apiUrl}/auth/logout/`).flush(null);

    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('ssd.token')).toBeNull();
  });

  it('clears a stored token that the API no longer accepts', async () => {
    localStorage.setItem('ssd.token', 'expired');
    // A fresh instance reads the token from storage.
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter(routes)],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);

    const restoring = service.restoreSession();
    http
      .expectOne(`${environment.apiUrl}/auth/me/`)
      .flush({ message: 'expired' }, { status: 401, statusText: 'Unauthorized' });
    await restoring;

    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('ssd.token')).toBeNull();
  });
});
