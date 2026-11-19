import { Routes } from '@angular/router';

import { agentGuard, authGuard, configGuard, guestGuard, requesterGuard } from './core/guards/auth.guards';

/**
 * Every page is lazy loaded, so the browser only downloads the code for the
 * screens a person actually opens.
 */
export const routes: Routes = [
  {
    path: 'login',
    title: 'Sign in',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login-page').then((m) => m.LoginPage),
  },
  {
    path: 'register',
    title: 'Create account',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/register-page').then((m) => m.RegisterPage),
  },
  {
    path: '',
    canActivate: [authGuard, configGuard],
    loadComponent: () => import('./layout/shell').then((m) => m.Shell),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        title: 'Dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard-page').then((m) => m.DashboardPage),
      },
      {
        path: 'tickets',
        title: 'Tickets',
        loadComponent: () =>
          import('./features/tickets/ticket-list-page').then((m) => m.TicketListPage),
      },
      {
        path: 'tickets/new',
        title: 'New ticket',
        canActivate: [requesterGuard],
        loadComponent: () =>
          import('./features/tickets/ticket-create-page').then((m) => m.TicketCreatePage),
      },
      {
        path: 'tickets/:id',
        title: 'Ticket details',
        loadComponent: () =>
          import('./features/tickets/ticket-detail-page').then((m) => m.TicketDetailPage),
      },
      {
        path: 'activity',
        title: 'Activity log',
        canActivate: [agentGuard],
        loadComponent: () =>
          import('./features/activity/activity-log-page').then((m) => m.ActivityLogPage),
      },
      {
        path: 'users',
        title: 'Users',
        canActivate: [agentGuard],
        loadComponent: () => import('./features/users/user-list-page').then((m) => m.UserListPage),
      },
      {
        path: 'configuration',
        title: 'Configuration',
        canActivate: [agentGuard],
        loadComponent: () =>
          import('./features/configuration/configuration-page').then((m) => m.ConfigurationPage),
      },
    ],
  },
  {
    path: '**',
    title: 'Page not found',
    loadComponent: () => import('./features/not-found-page').then((m) => m.NotFoundPage),
  },
];
