import { DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter, fromEvent, merge, timer } from 'rxjs';

/** How often the dashboard and tables reload their data in the background. */
export const AUTO_REFRESH_MS = 30_000;

/**
 * Calls `refresh` every `intervalMs` while the browser tab is visible, and once
 * more as soon as the person comes back to the tab. Stops by itself when the
 * component / service that called it is destroyed.
 *
 * Must be called in an injection context (a constructor or field initialiser).
 */
export function autoRefresh(refresh: () => void, intervalMs: number = AUTO_REFRESH_MS): void {
  if (intervalMs <= 0) return;
  merge(timer(intervalMs, intervalMs), fromEvent(document, 'visibilitychange'))
    .pipe(
      filter(() => !document.hidden),
      takeUntilDestroyed(inject(DestroyRef)),
    )
    .subscribe(() => refresh());
}
