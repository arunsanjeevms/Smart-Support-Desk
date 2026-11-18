import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

import { SimilarTicket } from '../../../core/models/api.models';
import { LookupBadge } from '../../../shared/components/lookup-badge';
import { similarityPercent } from './similar-text';

export interface SimilarTicketDialogData {
  ticket: SimilarTicket;
  sameCategory: boolean;
  /** Agents looking from an existing ticket can copy the resolution note. */
  canUseNote: boolean;
  /** Agents can open the full ticket (in a new tab, so nothing typed is lost). */
  canOpenTicket: boolean;
}

/** Result of the dialog: 'use-note' when the agent wants to reuse the resolution note. */
export type SimilarTicketDialogResult = 'use-note' | undefined;

/** Read-only details of a suggested resolved ticket. */
@Component({
  selector: 'app-similar-ticket-dialog',
  imports: [DatePipe, RouterLink, MatDialogModule, MatButtonModule, MatIconModule, LookupBadge],
  template: `
    <h2 mat-dialog-title class="dialog-title">
      <span class="title-icon"><mat-icon>task_alt</mat-icon></span>
      <span class="title-text">
        <small>{{ ticket.reference }} · Resolved ticket</small>
        {{ ticket.title }}
      </span>
    </h2>

    <mat-dialog-content class="content">
      <div class="meta">
        <app-lookup-badge [option]="ticket.category" />
        @if (data.sameCategory) {
          <span class="tag same"><mat-icon>check</mat-icon>Same category</span>
        }
        <span class="tag score" [class.strong]="ticket.match === 'strong'">
          <mat-icon>join_inner</mat-icon>{{ percent }}% similar
        </span>
        @if (ticket.resolved_at) {
          <span class="when">
            <mat-icon>event_available</mat-icon>
            Resolved {{ ticket.resolved_at | date: 'd MMM y' }}
            @if (ticket.resolved_by) {
              by {{ ticket.resolved_by.full_name }}
            }
          </span>
        }
      </div>

      <p class="advisory" role="note">
        <mat-icon>info</mat-icon>
        <span>
          Suggested because its wording is {{ percent }}% similar to
          {{ data.canUseNote ? 'this ticket' : 'yours' }}. It is not a confirmed answer, so check that the
          fix applies before relying on it.
        </span>
      </p>

      <section class="block">
        <h3><mat-icon>description</mat-icon>The problem</h3>
        <p class="prose">{{ ticket.description }}</p>
      </section>

      <section class="block resolution">
        <h3><mat-icon>check_circle</mat-icon>How it was resolved</h3>
        <p class="prose">{{ ticket.resolution_note }}</p>
      </section>
    </mat-dialog-content>

    <mat-dialog-actions align="end" class="actions">
      @if (data.canOpenTicket) {
        <a mat-button [routerLink]="['/tickets', ticket.id]" target="_blank" rel="noopener">
          <mat-icon>open_in_new</mat-icon>
          Open full ticket
        </a>
      }
      <span class="spacer"></span>
      @if (data.canUseNote) {
        <button mat-stroked-button type="button" [mat-dialog-close]="'use-note'">
          <mat-icon>content_paste</mat-icon>
          Use this note
        </button>
      }
      <button mat-flat-button type="button" mat-dialog-close cdkFocusInitial>
        {{ data.canUseNote ? 'Close' : 'Back to my ticket' }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    .dialog-title {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-top: 20px;
      line-height: 1.3;

      // Material's baseline spacer does not suit a flex title.
      &::before {
        display: none;
      }
    }
    .title-icon {
      flex: none;
      display: grid;
      place-items: center;
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: var(--app-success-soft);
      color: var(--app-success);
    }
    .title-text {
      display: flex;
      flex-direction: column;
      font-size: 17px;

      small {
        font-size: 12px;
        font-weight: 500;
        color: var(--app-text-muted);
      }
    }
    .content {
      display: flex;
      flex-direction: column;
      gap: 14px;
      width: min(600px, 86vw);
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }
    .tag,
    .when {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 12.5px;

      .mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
    .tag {
      padding: 3px 9px 3px 7px;
      border-radius: 999px;
      font-weight: 500;
      border: 1px solid var(--app-border);
      background: var(--app-surface-muted);
      color: var(--app-text-secondary);
    }
    .tag.same {
      color: var(--app-primary);
      background: var(--app-primary-soft);
      border-color: var(--app-primary-border);
    }
    .tag.score.strong {
      color: var(--app-success);
      background: var(--app-success-soft);
      border-color: #abefc6;
    }
    .when {
      color: var(--app-text-muted);
    }
    .advisory {
      display: flex;
      gap: 8px;
      margin: 0;
      padding: 10px 12px;
      border-radius: var(--app-radius);
      background: var(--app-warning-soft);
      border: 1px solid #fedf89;
      color: #7a2e0e;
      font-size: 13px;

      .mat-icon {
        flex: none;
        font-size: 18px;
        width: 18px;
        height: 18px;
        color: var(--app-warning);
      }
    }
    .block h3 {
      display: flex;
      align-items: center;
      gap: 6px;
      margin: 0 0 6px;
      font-size: 13px;
      font-weight: 600;
      color: var(--app-text-secondary);

      .mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
        color: var(--app-text-muted);
      }
    }
    .prose {
      margin: 0;
      white-space: pre-line;
      color: var(--app-text);
      font-size: 14px;
      line-height: 1.6;
    }
    .resolution {
      padding: 12px 14px;
      border-radius: var(--app-radius);
      background: var(--app-success-soft);
      border: 1px solid #abefc6;

      h3,
      h3 .mat-icon {
        color: var(--app-success);
      }
    }
    .actions {
      flex-wrap: wrap;
      gap: 8px;
    }
  `,
})
export class SimilarTicketDialog {
  protected readonly data = inject<SimilarTicketDialogData>(MAT_DIALOG_DATA);
  protected readonly ticket = this.data.ticket;
  protected readonly percent = similarityPercent(this.data.ticket.score);
}
