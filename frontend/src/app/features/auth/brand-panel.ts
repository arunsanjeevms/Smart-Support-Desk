import { Component } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

/** Left-hand marketing panel shown on the sign-in and sign-up pages. */
@Component({
  selector: 'app-brand-panel',
  imports: [MatIconModule],
  template: `
    <div class="logo">
      <span class="mark"><mat-icon class="filled">support_agent</mat-icon></span>
      Smart Support Desk
    </div>

    <div class="pitch">
      <h2>Report an issue. Track it. Get it resolved.</h2>
      <p>One place for your team to raise software problems and for support to resolve them.</p>
      <ul class="features">
        <li>
          <span class="feature-icon"><mat-icon>edit_note</mat-icon></span>
          <div>
            <strong>Raise tickets in seconds</strong>
            <span>Pick a category, describe the problem, done.</span>
          </div>
        </li>
        <li>
          <span class="feature-icon"><mat-icon>timeline</mat-icon></span>
          <div>
            <strong>Follow every step</strong>
            <span>Status changes, comments and resolutions in one timeline.</span>
          </div>
        </li>
        <li>
          <span class="feature-icon"><mat-icon>ios_share</mat-icon></span>
          <div>
            <strong>Share reports</strong>
            <span>Export any table to PDF or Excel, or email it.</span>
          </div>
        </li>
      </ul>
    </div>

    <p class="brand-footer">Angular · Django REST Framework · MongoDB</p>
  `,
  styleUrl: './brand-panel.scss',
})
export class BrandPanel {}
