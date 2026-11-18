import { HttpErrorResponse } from '@angular/common/http';
import { AbstractControl, FormGroup } from '@angular/forms';

import { ApiErrorBody } from '../models/api.models';

/** Best human readable message for any failed request. */
export function errorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'Cannot reach the server. Check that the backend is running and try again.';
    }
    const body = error.error as Partial<ApiErrorBody> | null;
    if (body && typeof body === 'object' && typeof body.message === 'string') {
      return body.message;
    }
    if (error.status >= 500) {
      return 'The server ran into a problem. Please try again in a moment.';
    }
  }
  return fallback;
}

/** Upload problems: the API lists every rejected file under `files`. */
export function fileErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof HttpErrorResponse && error.status === 400) {
    const files = (error.error as Partial<ApiErrorBody> | null)?.errors?.['files'];
    if (Array.isArray(files) && files.length) {
      return files.join(' ');
    }
  }
  return errorMessage(error, fallback);
}

/** Field errors from a 400 response, e.g. { title: ['This field is required.'] }. */
export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof HttpErrorResponse) || error.status !== 400) return {};
  const errors = (error.error as Partial<ApiErrorBody> | null)?.errors ?? {};
  const result: Record<string, string> = {};
  for (const [field, messages] of Object.entries(errors)) {
    result[field] = Array.isArray(messages) ? String(messages[0]) : String(messages);
  }
  return result;
}

/**
 * Shows backend validation messages on the matching form controls.
 * Returns the messages that did not match a control (to show in a banner).
 */
export function applyServerErrors(form: FormGroup, error: unknown): string[] {
  const unmatched: string[] = [];
  for (const [field, message] of Object.entries(fieldErrors(error))) {
    const control: AbstractControl | null = form.get(field);
    if (control) {
      control.setErrors({ ...(control.errors ?? {}), server: message });
      control.markAsTouched();
    } else {
      unmatched.push(message);
    }
  }
  return unmatched;
}
