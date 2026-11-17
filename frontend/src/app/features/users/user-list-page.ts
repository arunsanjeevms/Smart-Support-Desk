import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';

import { User } from '../../core/models/api.models';
import { ConfigService } from '../../core/services/config.service';
import { PageHeader } from '../../shared/components/page-header';
import { UserAvatar } from '../../shared/components/user-avatar';
import { DataTable } from '../../shared/data-table/data-table';
import { CellTemplate, TableColumn } from '../../shared/data-table/table-column';
import { TableSource } from '../../shared/data-table/table-source';
import { RelativeTimePipe } from '../../shared/pipes/relative-time.pipe';

/** Directory of requesters and support agents (support team only). */
@Component({
  selector: 'app-user-list-page',
  imports: [
    DatePipe,
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
        icon="group"
        title="Users"
        description="People who raise tickets and the support agents who resolve them. Agents are added in the Django admin."
      />

      <app-data-table
        [source]="source"
        [columns]="columns"
        exportTitle="Users"
        searchPlaceholder="Search name, username, email…"
        emptyIcon="group"
        emptyTitle="No users found"
      >
        <ng-container tableFilters>
          <mat-form-field class="filter-field">
            <mat-label>Role</mat-label>
            <mat-select
              [value]="source.filters()['role']"
              (selectionChange)="source.setFilter('role', $event.value)"
            >
              <mat-option value="">All roles</mat-option>
              @for (role of config.roles(); track role.value) {
                <mat-option [value]="role.value">{{ role.label }}</mat-option>
              }
            </mat-select>
          </mat-form-field>
        </ng-container>

        <ng-template appCell="first_name" let-row>
          <app-user-avatar [user]="row" [subtitle]="row.email" [size]="34" />
        </ng-template>

        <ng-template appCell="username" let-row>
          <span class="mono">{{ row.username }}</span>
        </ng-template>

        <ng-template appCell="role" let-row>
          <span class="role" [class.agent]="row.is_agent">
            <mat-icon>{{ row.is_agent ? 'support_agent' : 'person' }}</mat-icon>
            {{ row.role_label }}
          </span>
        </ng-template>

        <ng-template appCell="is_active" let-row>
          <span class="active" [class.off]="!row.is_active">
            <mat-icon>{{ row.is_active ? 'check_circle' : 'block' }}</mat-icon>
            {{ row.is_active ? 'Active' : 'Disabled' }}
          </span>
        </ng-template>

        <ng-template appCell="date_joined" let-row>
          {{ row.date_joined | date: 'd MMM y' }}
        </ng-template>

        <ng-template appCell="last_login" let-row>
          <span [matTooltip]="(row.last_login | date: 'medium') ?? 'Never'">{{ row.last_login | relativeTime }}</span>
        </ng-template>
      </app-data-table>
    </div>
  `,
  styles: `
    .role {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 10px 2px 7px;
      border-radius: 999px;
      font-size: 12.5px;
      font-weight: 600;
      color: #0f766e;
      background: #effaf7;
      border: 1px solid #b9e7dc;
      white-space: nowrap;
      &.agent {
        color: #6d28d9;
        background: #f6f2ff;
        border-color: #ddd0fb;
      }
      .mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
    .active {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--app-success);
      .mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
      &.off {
        color: var(--app-text-muted);
      }
    }
  `,
})
export class UserListPage {
  protected readonly config = inject(ConfigService);

  protected readonly source = new TableSource<User>('users/', {
    sort: { active: 'first_name', direction: 'asc' },
    filters: { role: '' },
  });

  protected readonly columns: TableColumn<User>[] = [
    { key: 'first_name', label: 'Name', sortField: 'first_name' },
    { key: 'username', label: 'Username', sortField: 'username', hideOnMobile: true },
    { key: 'role', label: 'Role', sortField: 'role' },
    { key: 'job_title', label: 'Job title', hideOnMobile: true },
    { key: 'is_active', label: 'Status', hideOnMobile: true },
    { key: 'date_joined', label: 'Joined', sortField: 'date_joined', hideOnMobile: true },
    { key: 'last_login', label: 'Last sign-in', sortField: 'last_login' },
  ];
}
