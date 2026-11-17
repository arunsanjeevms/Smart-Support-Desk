import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Params, RouterLink } from '@angular/router';

import { TicketStats } from '../../core/models/api.models';
import { AuthService } from '../../core/services/auth.service';
import { TicketService } from '../../core/services/ticket.service';
import { errorMessage } from '../../core/utils/api-errors';
import { autoRefresh } from '../../core/utils/auto-refresh';
import { CountUp } from '../../shared/components/count-up';
import { LiveIndicator } from '../../shared/components/live-indicator';
import { LookupBadge } from '../../shared/components/lookup-badge';
import { PageHeader } from '../../shared/components/page-header';
import { StatusBadge } from '../../shared/components/status-badge';
import { UserAvatar } from '../../shared/components/user-avatar';
import { RelativeTimePipe } from '../../shared/pipes/relative-time.pipe';

const PIE_CENTER = 90;
const PIE_RADIUS = 86;

interface StatTile {
  label: string;
  /** Numeric value (animated); `null` shows a dash. */
  value: number | null;
  decimals?: number;
  suffix?: string;
  icon: string;
  tone: 'blue' | 'amber' | 'green' | 'slate' | 'violet';
  caption: string;
  link?: string;
  queryParams?: Params;
}

@Component({
  selector: 'app-dashboard-page',
  imports: [
    DatePipe,
    DecimalPipe,
    RouterLink,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
    PageHeader,
    StatusBadge,
    LookupBadge,
    UserAvatar,
    CountUp,
    LiveIndicator,
    RelativeTimePipe,
  ],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.scss',
})
export class DashboardPage implements OnInit {
  protected readonly auth = inject(AuthService);
  private readonly tickets = inject(TicketService);

  protected readonly stats = signal<TicketStats | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly today = new Date();
  protected readonly lastUpdated = signal<Date | null>(null);
  private requestInFlight = false;

  protected readonly tiles = computed<StatTile[]>(() => {
    const stats = this.stats();
    if (!stats) return [];
    const count = (value: string) => stats.by_status.find((s) => s.value === value)?.count ?? 0;
    const open = count('open');
    const inProgress = count('in_progress');
    const resolved = count('resolved');
    const avg = stats.average_resolution_hours;
    const inDays = avg !== null && avg >= 48;
    const avgValue = avg === null ? null : inDays ? avg / 24 : avg;
    const avgSuffix = inDays ? ' d' : ' h';
    const avgText = avgValue === null ? '—' : `${avgValue.toFixed(1)}${avgSuffix}`;

    if (this.auth.isAgent()) {
      return [
        {
          label: 'Open queue',
          value: open + inProgress,
          icon: 'inbox',
          tone: 'blue',
          caption: `${stats.unassigned_open ?? 0} waiting for an owner`,
          link: '/tickets',
          queryParams: { status: 'open,in_progress' },
        },
        {
          label: 'Assigned to me',
          value: stats.assigned_to_me_open ?? 0,
          icon: 'assignment_ind',
          tone: 'violet',
          caption: 'Open or in progress',
          link: '/tickets',
          queryParams: { assigned_to: 'me', status: 'open,in_progress' },
        },
        {
          label: 'Resolved this week',
          value: stats.resolved_last_7_days,
          icon: 'task_alt',
          tone: 'green',
          caption: `${resolved} resolved in total`,
          link: '/tickets',
          queryParams: { status: 'resolved' },
        },
        {
          label: 'Avg. resolution time',
          value: avgValue,
          decimals: 1,
          suffix: avgSuffix,
          icon: 'timer',
          tone: 'amber',
          caption: `${stats.created_last_7_days} new tickets in 7 days`,
        },
      ];
    }
    return [
      {
        label: 'My tickets',
        value: stats.total,
        icon: 'confirmation_number',
        tone: 'slate',
        caption: `${stats.created_last_7_days} raised in the last 7 days`,
        link: '/tickets',
      },
      {
        label: 'Open',
        value: open,
        icon: 'radio_button_unchecked',
        tone: 'blue',
        caption: 'Waiting for the support team',
        link: '/tickets',
        queryParams: { status: 'open' },
      },
      {
        label: 'In progress',
        value: inProgress,
        icon: 'autorenew',
        tone: 'amber',
        caption: 'An agent is working on it',
        link: '/tickets',
        queryParams: { status: 'in_progress' },
      },
      {
        label: 'Resolved',
        value: resolved,
        icon: 'check_circle',
        tone: 'green',
        caption: avg === null ? 'No resolved tickets yet' : `Typically resolved in ${avgText}`,
        link: '/tickets',
        queryParams: { status: 'resolved' },
      },
    ];
  });

  /** Share of each status, used by both the pie chart and its legend. */
  protected readonly statusShare = computed(() => {
    const stats = this.stats();
    if (!stats || stats.total === 0) return [];
    return stats.by_status.map((s) => ({ ...s, percent: (s.count / stats.total) * 100 }));
  });

  /** SVG pie slices (only statuses that have tickets), drawn clockwise from 12 o'clock. */
  protected readonly pieSlices = computed(() => {
    const shares = this.statusShare().filter((s) => s.count > 0);
    const radius = PIE_RADIUS;
    let angle = -Math.PI / 2;
    return shares.map((share) => {
      // A single status covers the whole circle, which an arc path cannot draw.
      if (share.percent >= 99.999) {
        return { ...share, path: null as string | null };
      }
      const sweep = (share.percent / 100) * 2 * Math.PI;
      const start = angle;
      const end = angle + sweep;
      angle = end;
      const point = (a: number) =>
        `${(PIE_CENTER + radius * Math.cos(a)).toFixed(2)} ${(PIE_CENTER + radius * Math.sin(a)).toFixed(2)}`;
      const largeArc = sweep > Math.PI ? 1 : 0;
      const path = `M ${PIE_CENTER} ${PIE_CENTER} L ${point(start)} A ${radius} ${radius} 0 ${largeArc} 1 ${point(end)} Z`;
      return { ...share, path };
    });
  });

  protected readonly pieSize = PIE_CENTER * 2;
  protected readonly pieRadius = PIE_RADIUS;
  protected readonly pieCenter = PIE_CENTER;

  protected readonly categoryRows = computed(() => {
    const rows = [...(this.stats()?.by_category ?? [])].sort((a, b) => b.count - a.count);
    const max = Math.max(1, ...rows.map((r) => r.count));
    return rows.map((row) => ({ ...row, percent: (row.count / max) * 100 }));
  });

  constructor() {
    // Keep the numbers current while the page stays open.
    autoRefresh(() => this.load(true));
  }

  ngOnInit(): void {
    this.load();
  }

  /** `silent` = background refresh: no loading bar, and a failure keeps the current numbers. */
  protected load(silent = false): void {
    if (this.requestInFlight) return;
    this.requestInFlight = true;
    if (!silent) {
      this.loading.set(true);
      this.error.set(null);
    }
    this.tickets.stats().subscribe({
      next: (stats) => {
        this.requestInFlight = false;
        this.stats.set(stats);
        this.lastUpdated.set(new Date());
        this.loading.set(false);
        this.error.set(null);
      },
      error: (error: unknown) => {
        this.requestInFlight = false;
        this.loading.set(false);
        if (!silent) this.error.set(errorMessage(error, 'Could not load the dashboard.'));
      },
    });
  }
}
