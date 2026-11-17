import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { ConfigService } from '../services/config.service';
import { NotifyService } from '../services/notify.service';

/** Only signed-in users. */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  if (auth.isAuthenticated()) return true;
  return inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

/** Only visitors who are NOT signed in (login / register pages). */
export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.isAuthenticated() ? inject(Router).createUrlTree(['/dashboard']) : true;
};

/** Only members of the support team. */
export const agentGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  if (auth.isAgent()) return true;
  inject(NotifyService).error('That page is only available to the support team.');
  return inject(Router).createUrlTree(['/dashboard']);
};

/** Loads backend configuration (statuses, categories, ...) before the app shell renders. */
export const configGuard: CanActivateFn = () => {
  const config = inject(ConfigService);
  const notify = inject(NotifyService);
  if (config.loaded()) return true;
  return config.load().pipe(
    map(() => true),
    catchError(() => {
      notify.error('Could not load configuration from the server.');
      return of(true);
    }),
  );
};
