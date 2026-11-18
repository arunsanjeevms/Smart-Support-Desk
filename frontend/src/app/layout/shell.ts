import { BreakpointObserver } from '@angular/cdk/layout';
import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map } from 'rxjs';

import { AuthService } from '../core/services/auth.service';
import { UserAvatar } from '../shared/components/user-avatar';
import { WelcomeIntro } from './welcome-intro';

interface NavItem {
  label: string;
  icon: string;
  link: string;
  exact?: boolean;
  queryParams?: Record<string, string>;
}

/** App frame for signed-in users: sidebar navigation + top bar + page outlet. */
@Component({
  selector: 'app-shell',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatDividerModule,
    MatTooltipModule,
    UserAvatar,
    WelcomeIntro,
  ],
  templateUrl: './shell.html',
  styleUrl: './shell.scss',
})
export class Shell {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  /** Right after signing in: show the welcome intro, then animate the app in. */
  private readonly welcome = this.auth.consumeWelcome();
  protected readonly welcomeKind = this.welcome ?? 'back';
  protected readonly showIntro = signal(this.welcome !== null);
  protected readonly playEntrance = this.welcome !== null;

  protected readonly isMobile = toSignal(
    inject(BreakpointObserver)
      .observe('(max-width: 960px)')
      .pipe(map((state) => state.matches)),
    { initialValue: false },
  );
  protected readonly mobileOpen = signal(false);

  protected readonly workspaceNav = computed<NavItem[]>(() => [
    { label: 'Dashboard', icon: 'space_dashboard', link: '/dashboard' },
    {
      label: this.auth.isAgent() ? 'All tickets' : 'My tickets',
      icon: 'confirmation_number',
      link: '/tickets',
      exact: true,
    },
    { label: 'New ticket', icon: 'add_circle', link: '/tickets/new', exact: true },
  ]);

  protected readonly supportNav: NavItem[] = [
    { label: 'Activity log', icon: 'history', link: '/activity' },
    { label: 'Users', icon: 'group', link: '/users' },
    { label: 'Configuration', icon: 'tune', link: '/configuration' },
  ];

  protected readonly greeting = computed(() => {
    const hour = new Date().getHours();
    return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  });

  constructor() {
    // Close the mobile drawer after navigating.
    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.mobileOpen.set(false));
  }

  protected logout(): void {
    this.auth.logout();
  }
}
