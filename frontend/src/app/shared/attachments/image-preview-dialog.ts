import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

import { Attachment } from '../../core/models/api.models';
import { formatSize } from '../../core/utils/files';

export interface ImagePreviewData {
  attachment: Attachment;
  /** Blob URL of the image (already loaded with the sign-in token). */
  url: string;
}

/** Full-size view of an attached image. Closes with 'download' when the user wants the file. */
@Component({
  selector: 'app-image-preview-dialog',
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <h2 mat-dialog-title class="title">
      <mat-icon>image</mat-icon>
      <span class="name">{{ data.attachment.file_name }}</span>
      <span class="size">{{ size }}</span>
    </h2>
    <mat-dialog-content class="content">
      <img [src]="data.url" [alt]="data.attachment.file_name" />
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button type="button" [mat-dialog-close]="'download'">
        <mat-icon>download</mat-icon>
        Download
      </button>
      <button mat-flat-button type="button" mat-dialog-close cdkFocusInitial>Close</button>
    </mat-dialog-actions>
  `,
  styles: `
    .title {
      display: flex;
      align-items: center;
      gap: 10px;
      padding-top: 20px;
      font-size: 16px;

      &::before {
        display: none;
      }
      .mat-icon {
        flex: none;
        color: var(--app-primary);
      }
    }
    .name {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .size {
      flex: none;
      font-size: 12.5px;
      font-weight: 400;
      color: var(--app-text-muted);
    }
    .content {
      display: grid;
      place-items: center;
      background:
        repeating-conic-gradient(#f3f4f6 0% 25%, #ffffff 0% 50%) 50% / 16px 16px;
      border-radius: var(--app-radius);
      padding: 12px !important;
    }
    img {
      display: block;
      max-width: min(860px, 82vw);
      max-height: 70vh;
      object-fit: contain;
      border-radius: 6px;
      box-shadow: var(--app-shadow-sm);
    }
  `,
})
export class ImagePreviewDialog {
  protected readonly data = inject<ImagePreviewData>(MAT_DIALOG_DATA);
  protected readonly size = formatSize(this.data.attachment.size);
}
