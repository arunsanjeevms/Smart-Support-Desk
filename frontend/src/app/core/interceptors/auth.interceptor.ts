import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuthService } from '../services/auth.service';

/**
 * Adds the API token to every backend request and sends the user back to the
 * login page when the token is no longer valid.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.token();
  const isApiCall = req.url.startsWith(environment.apiUrl);

  const request =
    token && isApiCall ? req.clone({ setHeaders: { Authorization: `Token ${token}` } }) : req;

  return next(request).pipe(
    catchError((error: unknown) => {
      const isAuthEndpoint = req.url.includes('/auth/login') || req.url.includes('/auth/register');
      if (error instanceof HttpErrorResponse && error.status === 401 && isApiCall && !isAuthEndpoint) {
        auth.clearSession();
        void router.navigate(['/login'], {
          queryParams: { returnUrl: router.url, expired: 1 },
        });
      }
      return throwError(() => error);
    }),
  );
};
