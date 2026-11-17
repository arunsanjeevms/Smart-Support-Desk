import { Component, DestroyRef, computed, effect, inject, input, signal, untracked } from '@angular/core';

/** Easing: fast start, gentle landing. */
const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

function prefersReducedMotion(): boolean {
  try {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch {
    return false;
  }
}

/**
 * Shows a number that counts up (or down) to its value.
 *
 *   <app-count-up [value]="14" />
 *   <app-count-up [value]="33.1" [decimals]="1" suffix=" h" />
 *
 * A `null` value renders an em dash. People who prefer reduced motion see the
 * final number straight away.
 */
@Component({
  selector: 'app-count-up',
  template: '{{ text() }}',
})
export class CountUp {
  readonly value = input.required<number | null>();
  readonly decimals = input(0);
  readonly suffix = input('');
  readonly duration = input(900);

  private readonly shown = signal(0);
  private frame = 0;

  protected readonly text = computed(() => {
    if (this.value() === null) return '—';
    const digits = this.decimals();
    const formatted = this.shown().toLocaleString('en', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
    return formatted + this.suffix();
  });

  constructor() {
    inject(DestroyRef).onDestroy(() => cancelAnimationFrame(this.frame));

    effect(() => {
      const target = this.value();
      const duration = this.duration();
      untracked(() => this.animateTo(target ?? 0, duration));
    });
  }

  private animateTo(target: number, duration: number): void {
    cancelAnimationFrame(this.frame);
    const from = this.shown();
    if (from === target || duration <= 0 || prefersReducedMotion()) {
      this.shown.set(target);
      return;
    }
    // Use the first frame's own timestamp as the start, so the clock never runs
    // "backwards" relative to the timestamps requestAnimationFrame hands us.
    let startedAt: number | null = null;
    const step = (now: number) => {
      startedAt ??= now;
      const progress = Math.min(1, Math.max(0, (now - startedAt) / duration));
      this.shown.set(from + (target - from) * easeOutCubic(progress));
      if (progress < 1) this.frame = requestAnimationFrame(step);
    };
    this.frame = requestAnimationFrame(step);
  }
}
