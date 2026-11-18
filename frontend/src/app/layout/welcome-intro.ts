import { Component, DestroyRef, computed, inject, input, output, signal } from '@angular/core';

import { User } from '../core/models/api.models';
import { WelcomeKind } from '../core/services/auth.service';

/** Total time on screen before fading out, and the fade-out itself (ms). */
const SHOW_MS = 1900;
const FADE_MS = 450;
const REDUCED_MOTION_SHOW_MS = 700;

function prefersReducedMotion(): boolean {
  try {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch {
    return false;
  }
}

/**
 * Short full-screen welcome shown once right after signing in:
 * the logo tile pops in and its tick draws itself, the welcome text fades up,
 * a progress line fills, then everything fades away to reveal the app.
 * Click anywhere or press Esc to skip.
 */
@Component({
  selector: 'app-welcome-intro',
  host: { '(document:keydown.escape)': 'skip()' },
  template: `
    <div class="intro" [class.leaving]="leaving()" role="status" aria-live="polite" (click)="skip()">
      <div class="stage">
        <div class="mark" aria-hidden="true">
          <span class="ring"></span>
          <svg class="tile" viewBox="0 0 64 64">
            <rect width="64" height="64" rx="15" fill="#0f766e" />
            <path
              class="tick"
              d="M19 33.5l8.5 8.5L45.5 23"
              fill="none"
              stroke="#fff"
              stroke-width="6.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
        <p class="brand">Smart Support Desk</p>
        <h1 class="welcome">{{ heading() }}</h1>
        <p class="sub">{{ subtitle() }}</p>
        <div class="progress" aria-hidden="true"><span></span></div>
      </div>
      <button class="skip" type="button" (click)="skip(); $event.stopPropagation()">Skip</button>
    </div>
  `,
  styleUrl: './welcome-intro.scss',
})
export class WelcomeIntro {
  readonly user = input<User | null>(null);
  readonly kind = input<WelcomeKind>('back');
  /** Emitted once the intro has faded out. */
  readonly finished = output<void>();

  protected readonly leaving = signal(false);

  protected readonly heading = computed(() => {
    const name = this.user()?.first_name || this.user()?.username || '';
    const hello = this.kind() === 'new' ? 'Welcome' : 'Welcome back';
    return name ? `${hello}, ${name}` : hello;
  });

  protected readonly subtitle = computed(() =>
    this.user()?.is_agent ? 'Getting your support queue ready…' : 'Getting your tickets ready…',
  );

  private readonly timers: ReturnType<typeof setTimeout>[] = [];
  private done = false;

  constructor() {
    inject(DestroyRef).onDestroy(() => this.timers.forEach(clearTimeout));
    const showFor = prefersReducedMotion() ? REDUCED_MOTION_SHOW_MS : SHOW_MS;
    this.timers.push(setTimeout(() => this.skip(), showFor));
  }

  /** Start fading out now (also used by the Skip button, a click and Esc). */
  skip(): void {
    if (this.leaving()) return;
    this.leaving.set(true);
    const fade = prefersReducedMotion() ? 0 : FADE_MS;
    this.timers.push(setTimeout(() => this.finish(), fade));
  }

  private finish(): void {
    if (this.done) return;
    this.done = true;
    this.finished.emit();
  }
}
