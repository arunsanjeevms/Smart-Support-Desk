import { Component, computed, input } from '@angular/core';

import { UserSummary } from '../../core/models/api.models';

const PALETTE = ['#1f4fbf', '#0f766e', '#7c3aed', '#b45309', '#be185d', '#0369a1', '#4d7c0f'];

type AvatarUser = Pick<UserSummary, 'full_name' | 'initials' | 'username'>;

/** Initials avatar, optionally followed by the name and a second line. */
@Component({
  selector: 'app-user-avatar',
  template: `
    @if (user(); as person) {
      <span class="user">
        <span
          class="avatar"
          aria-hidden="true"
          [style.background]="color()"
          [style.width.px]="size()"
          [style.height.px]="size()"
          [style.font-size.px]="size() * 0.4"
        >
          {{ person.initials }}
        </span>
        @if (showName()) {
          <span class="text">
            <span class="name">{{ person.full_name }}</span>
            @if (subtitle()) {
              <span class="sub">{{ subtitle() }}</span>
            }
          </span>
        }
      </span>
    } @else {
      <span class="muted">{{ emptyLabel() }}</span>
    }
  `,
  styles: `
    .user {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      max-width: 100%;
    }
    .avatar {
      flex: none;
      display: grid;
      place-items: center;
      border-radius: 50%;
      color: #fff;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .text {
      display: flex;
      flex-direction: column;
      min-width: 0;
      line-height: 1.25;
    }
    .name {
      color: var(--app-text);
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .sub {
      color: var(--app-text-muted);
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  `,
})
export class UserAvatar {
  readonly user = input<AvatarUser | null | undefined>(null);
  readonly size = input(28);
  readonly showName = input(true);
  readonly subtitle = input<string | null | undefined>('');
  readonly emptyLabel = input('Unassigned');

  /** Stable colour per user so people are easy to recognise. */
  protected readonly color = computed(() => {
    const key = this.user()?.username ?? '';
    let hash = 0;
    for (const char of key) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
    return PALETTE[hash % PALETTE.length];
  });
}
