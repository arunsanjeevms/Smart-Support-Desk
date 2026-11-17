import { HttpErrorResponse } from '@angular/common/http';
import { FormControl, FormGroup } from '@angular/forms';

import { applyServerErrors, errorMessage, fieldErrors } from './api-errors';

function badRequest(errors: Record<string, string[]>) {
  return new HttpErrorResponse({
    status: 400,
    error: { message: 'Please correct the highlighted fields.', errors },
  });
}

describe('api-errors', () => {
  it('uses the backend message when there is one', () => {
    expect(errorMessage(badRequest({}))).toBe('Please correct the highlighted fields.');
  });

  it('explains when the backend cannot be reached', () => {
    expect(errorMessage(new HttpErrorResponse({ status: 0 }))).toContain('Cannot reach the server');
  });

  it('falls back to a generic message for unknown errors', () => {
    expect(errorMessage(new Error('boom'), 'Fallback')).toBe('Fallback');
  });

  it('reads the first message of each field', () => {
    expect(fieldErrors(badRequest({ title: ['Too short.', 'Other'] }))).toEqual({ title: 'Too short.' });
  });

  it('puts server messages on matching form controls and returns the rest', () => {
    const form = new FormGroup({ title: new FormControl('Hey') });
    const unmatched = applyServerErrors(
      form,
      badRequest({ title: ['The title should be at least 5 characters.'], non_field_errors: ['Nope'] }),
    );

    expect(form.controls.title.getError('server')).toBe('The title should be at least 5 characters.');
    expect(form.controls.title.touched).toBe(true);
    expect(unmatched).toEqual(['Nope']);
  });
});
