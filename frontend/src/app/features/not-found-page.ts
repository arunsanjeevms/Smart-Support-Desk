import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found-page',
  imports: [RouterLink, MatButtonModule, MatIconModule],
  template: `
    <main class="not-found">
      <span class="icon"><mat-icon>travel_explore</mat-icon></span>
      <p class="code mono">404</p>
      <h1>We couldn't find that page</h1>
      <p class="muted">The link may be broken, or the page may have been moved.</p>
      <a mat-flat-button routerLink="/dashboard">
        <mat-icon>home</mat-icon>
        Back to dashboard
      </a>
    </main>
  `,
  styles: `
    .not-found {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 24px;
      text-align: center;
    }
    .icon {
      display: grid;
      place-items: center;
      width: 64px;
      height: 64px;
      border-radius: 18px;
      background: var(--app-primary-soft);
      color: var(--app-primary);
      .mat-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
      }
    }
    .code {
      color: var(--app-text-muted);
      letter-spacing: 0.2em;
    }
    h1 {
      font-size: 24px;
    }
    a {
      margin-top: 12px;
    }
  `,
})
export class NotFoundPage {}
