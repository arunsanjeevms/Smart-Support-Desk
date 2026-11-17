import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterLink } from '@angular/router';

import { TicketActivity } from '../../core/models/api.models';
import { ConfigService } from '../../core/services/config.service';
import { PageHeader } from '../../shared/components/page-header';
import { UserAvatar } from '../../shared/components/user-avatar';
import { DataTable } from '../../shared/data-table/data-table';
import { CellTemplate, TableColumn } from '../../shared/data-table/table-column';
import { TableSource } from '../../shared/data-table/table-source';
import { RelativeTimePipe } from '../../shared/pipes/relative-time.pipe';

/** Audit log of every ticket event (support team only). */
@Component({
  selector: 'app-activity-log-page',
  imports: [
    DatePipe,
    RouterLink,
    MatFormFieldModule,
    MatIconModule,
    MatSelectModule,
    MatTooltipModule,
    PageHeader,
    DataTable,
    CellTemplate,
    UserAvatar,
    RelativeTimePipe,
  ],
  template: `
    <div class="page">
      <app-page-header
        icon="history"
        title="Activity log"
        description="Every ticket event in one place: new tickets, status changes, assignments and comments."
      />

      <app-data-table
        [source]="source"
        [columns]="columns"
        [rowLink]="rowLink"
        exportTitle="Activity log"
        searchPlaceholder="Search ticket, details or note…"
        emptyIcon="history"
        emptyTitle="No activity yet"
      >
        <ng-container tableFilters>
          <mat-form-field floatLabel="always" class="filter-field wide">
            <mat-label>Activity</mat-label>
            <mat-select
              [value]="source.filters()['activity_type']"
              (selectionChange)="source.setFilter('activity_type', $event.value)"
            >
              <mat-option value="">All activity</mat-option>
              @for (type of config.activityTypes(); track type.value) {
                <mat-option [value]="type.value">{{ type.label }}</mat-option>
              }
            </mat-select>
          </mat-form-field>
        </ng-container>

        <ng-template appCell="created_at" let-row>
          <span class="when" [matTooltip]="(row.created_at | date: 'medium') ?? ''">
            {{ row.created_at | date: 'd MMM, h:mm a' }}
            <small>{{ row.created_at | relativeTime }}</small>
          </span>
        </ng-template>

        <ng-template appCell="ticket" let-row>
          <a class="ticket" [routerLink]="['/tickets', row.ticket.id]">
            <span class="ref-chip">{{ row.ticket.reference }}</span>
            <span class="ticket-title">{{ row.ticket.title }}</span>
          </a>
        </ng-template>

        <ng-template appCell="activity_type" let-row>
          <span class="activity" [class]="'activity ' + row.activity_type">
            <mat-icon>{{ row.icon }}</mat-icon>
            {{ row.activity_label }}
          </span>
        </ng-template>

        <ng-template appCell="message" let-row>
          <span class="message">{{ row.message }}</span>
          @if (row.note) {
            <span class="note" [matTooltip]="row.note">{{ row.note }}</span>
          }
        </ng-template>

        <ng-template appCell="actor" let-row>
          <app-user-avatar [user]="row.actor" [size]="26" emptyLabel="System" />
        </ng-template>
      </app-data-table>
    </div>
  `,
  styles: `
    .when {
      display: flex;
      flex-direction: column;
      white-space: nowrap;
      color: var(--app-text);
      small {
        color: var(--app-text-muted);
      }
    }
    .ticket {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
      max-width: 280px;
      color: inherit;
      text-decoration: none;
    }
    .ticket-title {
      max-width: 100%;
      color: var(--app-text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .ticket:hover .ticket-title {
      color: var(--app-primary);
    }
    .activity {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
      font-weight: 500;
      color: var(--app-text);
      .mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
        color: var(--app-text-muted);
      }
      &.created .mat-icon {
        color: #1f4fbf;
      }
      &.status_changed .mat-icon {
        color: #b45309;
      }
      &.commented .mat-icon {
        color: #6d28d9;
      }
      &.assigned .mat-icon {
        color: #0f766e;
      }
    }
    .message {
      display: block;
      color: var(--app-text);
    }
    .note {
      display: block;
      max-width: 360px;
      color: var(--app-text-muted);
      font-size: 12.5px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  `,
})
export class ActivityLogPage {
  protected readonly config = inject(ConfigService);

  protected readonly source = new TableSource<TicketActivity>('activities/', {
    sort: { active: 'created_at', direction: 'desc' },
    pageSize: 25,
    filters: { activity_type: '' },
  });

  protected readonly columns: TableColumn<TicketActivity>[] = [
    { key: 'created_at', label: 'When', sortField: 'created_at', width: '150px' },
    { key: 'ticket', label: 'Ticket', sortField: 'ticket__reference' },
    { key: 'activity_type', label: 'Activity', sortField: 'activity_type' },
    { key: 'message', label: 'Details' },
    { key: 'actor', label: 'By', sortField: 'actor__first_name', hideBelow: 'sm' },
  ];

  protected readonly rowLink = (row: TicketActivity) => ['/tickets', row.ticket.id];
}
