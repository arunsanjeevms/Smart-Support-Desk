/**
 * Production build: the Angular app and the Django API are served from the same
 * domain (Nginx sends /api/ to Django), so the API address is relative.
 * `ng serve` uses environment.development.ts (http://localhost:8000/api) instead.
 */
export const environment = {
  production: true,
  apiUrl: '/api',
};