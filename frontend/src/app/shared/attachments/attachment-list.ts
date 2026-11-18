import { Component, DestroyRef, effect, inject, input, output, signal, untracked } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { Attachment } from '../../core/models/api.models';
import { AttachmentService } from '../../core/services/attachment.service';
import { NotifyService } from '../../core/services/notify.service';
import { errorMessage } from '../../core/utils/api-errors';
import { fileIcon, formatSize } from '../../core/utils/files';
import { ConfirmDialog, ConfirmDialogData } from '../components/confirm-dialog';
import { RelativeTimePipe } from '../pipes/relative-time.pipe';
import { ImagePreviewData, ImagePreviewDialog } from './image-preview-dialog';

/**
 * Files attached to a ticket: image thumbnails or file-type icons, with
 * download, preview (images) and remove (when allowed).
 *
 * `compact` is the slim list shown under a comment in the timeline.
 */
@Component({
  selector: 'app-attachment-list',
  imports: [MatButtonModule, MatIconModule, MatTooltipModule, RelativeTimePipe],
  template: `
    <ul class="files" [class.compact]="compact()">
      @for (item of attachments(); track item.id) {
        <li class="file">
          <button
            type="button"
            class="thumb"
            [class.image]="item.is_image"
            (click)="open(item)"
            [attr.aria-label]="(item.is_image ? 'Preview ' : 'Download ') + item.file_name"
            [matTooltip]="item.is_image ? 'Preview' : 'Download'"
          >
            @if (!compact() && thumbs()[item.id]; as url) {
              <img [src]="url" alt="" />
            } @else {
              <mat-icon>{{ icon(item) }}</mat-icon>
            }
          </button>
          <div class="meta">
            <span class="name" [title]="item.file_name">{{ item.file_name }}</span>
            <span class="sub">
              {{ size(item) }}
              @if (!compact()) {
                · {{ item.uploaded_by?.full_name ?? 'Someone' }} · {{ item.created_at | relativeTime }}
              }
            </span>
          </div>
          <div class="actions">
            <button
              mat-icon-button
              type="button"
              (click)="download(item)"
              [disabled]="busy() === item.id"
              matTooltip="Download"
              [attr.aria-label]="'Download ' + item.file_name"
            >
              <mat-icon>download</mat-icon>
            </button>
            @if (item.can_delete && !compact()) {
              <button
                mat-icon-button
                type="button"
                class="delete"
                (click)="confirmRemove(item)"
                [disabled]="busy() === item.id"
                matTooltip="Remove"
                [attr.aria-label]="'Remove ' + item.file_name"
              >
                <mat-icon>delete</mat-icon>
              </button>
            }
          </div>
        </li>
      }
    </ul>
  `,
  styles: `
    .files {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr));
      gap: 10px;
      margin: 0;
      padding: 0;
      list-style: none;

      &.compact {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
      }
    }
    .file {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      padding: 8px 6px 8px 8px;
      border: 1px solid var(--app-border);
      border-radius: var(--app-radius);
      background: var(--app-surface);
      transition:
        border-color 0.15s,
        box-shadow 0.15s;

      &:nth-child(even) {
        background: var(--app-row-alt);
      }
      &:hover {
        border-color: var(--app-primary-border);
        box-shadow: var(--app-shadow-xs);
      }
    }
    .compact .file {
      max-width: 300px;
      padding: 4px 4px 4px 6px;
    }
    .thumb {
      flex: none;
      display: grid;
      place-items: center;
      width: 44px;
      height: 44px;
      padding: 0;
      overflow: hidden;
      border: 1px solid var(--app-border);
      border-radius: 8px;
      background: var(--app-primary-soft);
      color: var(--app-primary);
      cursor: pointer;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      &:focus-visible {
        outline: 2px solid var(--app-primary);
        outline-offset: 2px;
      }
    }
    .compact .thumb {
      width: 30px;
      height: 30px;
      border-radius: 6px;

      .mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }
    .meta {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 13px;
      font-weight: 500;
      color: var(--app-text);
    }
    .sub {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 11.5px;
      color: var(--app-text-muted);
    }
    .actions {
      flex: none;
      display: flex;
      color: var(--app-text-muted);
    }
    .compact .actions button {
      transform: scale(0.85);
    }
    .delete:hover {
      color: var(--app-danger);
    }
  `,
})
export class AttachmentList {
  readonly attachments = input<Attachment[]>([]);
  readonly compact = input(false);
  /** A file was removed on the server. */
  readonly removed = output<Attachment>();

  private readonly files = inject(AttachmentService);
  private readonly dialog = inject(MatDialog);
  private readonly notify = inject(NotifyService);

  /** Blob URLs of image thumbnails, by attachment id. */
  protected readonly thumbs = signal<Record<string, string>>({});
  protected readonly busy = signal<string | null>(null);
  private readonly requested = new Set<string>();

  constructor() {
    // Load thumbnails for images (with the sign-in token, so not a plain <img src>).
    effect(() => {
      if (this.compact()) return;
      for (const item of this.attachments()) {
        if (item.is_image && !this.requested.has(item.id)) {
          untracked(() => this.loadThumb(item));
        }
      }
    });
    inject(DestroyRef).onDestroy(() => Object.values(this.thumbs()).forEach((url) => URL.revokeObjectURL(url)));
  }

  protected icon(item: Attachment): string {
    return fileIcon(item.extension);
  }

  protected size(item: Attachment): string {
    return formatSize(item.size);
  }

  protected open(item: Attachment): void {
    if (!item.is_image) {
      this.download(item);
      return;
    }
    const url = this.thumbs()[item.id];
    if (url) {
      this.preview(item, url);
      return;
    }
    this.files.blob(item).subscribe({
      next: (blob) => {
        const blobUrl = URL.createObjectURL(blob);
        this.thumbs.update((map) => ({ ...map, [item.id]: blobUrl }));
        this.preview(item, blobUrl);
      },
      error: (error: unknown) => this.notify.error(errorMessage(error, 'The image could not be opened.')),
    });
  }

  protected download(item: Attachment): void {
    this.busy.set(item.id);
    this.files.download(item).subscribe({
      next: () => this.busy.set(null),
      error: (error: unknown) => {
        this.busy.set(null);
        this.notify.error(errorMessage(error, 'The file could not be downloaded.'));
      },
    });
  }

  protected confirmRemove(item: Attachment): void {
    const data: ConfirmDialogData = {
      title: 'Remove this file?',
      message: `${item.file_name} will be removed from the ticket. This is recorded in the activity log.`,
      confirmLabel: 'Remove file',
      icon: 'delete',
      danger: true,
    };
    this.dialog
      .open<ConfirmDialog, ConfirmDialogData, boolean>(ConfirmDialog, { data, width: '440px' })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.busy.set(item.id);
        this.files.remove(item).subscribe({
          next: () => {
            this.busy.set(null);
            this.notify.success(`Removed ${item.file_name}`);
            this.removed.emit(item);
          },
          error: (error: unknown) => {
            this.busy.set(null);
            this.notify.error(errorMessage(error, 'The file could not be removed.'));
          },
        });
      });
  }

  private loadThumb(item: Attachment): void {
    this.requested.add(item.id);
    this.files.blob(item).subscribe({
      next: (blob) => this.thumbs.update((map) => ({ ...map, [item.id]: URL.createObjectURL(blob) })),
      error: () => this.requested.delete(item.id), // the icon stays; a click retries
    });
  }

  private preview(item: Attachment, url: string): void {
    this.dialog
      .open<ImagePreviewDialog, ImagePreviewData, string>(ImagePreviewDialog, {
        data: { attachment: item, url },
        maxWidth: '94vw',
      })
      .afterClosed()
      .subscribe((result) => {
        if (result === 'download') this.download(item);
      });
  }
}
