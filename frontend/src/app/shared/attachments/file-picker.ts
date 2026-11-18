import { Component, ElementRef, computed, inject, input, model, signal, viewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { ConfigService } from '../../core/services/config.service';
import { checkFiles, fileExtension, fileIcon, formatSize } from '../../core/utils/files';

/**
 * Choose files to attach: drag and drop or "browse", with instant checks
 * against the backend's limits (type, size, number of files).
 *
 * `[(files)]` holds the chosen files; uploading is up to the page.
 * `compact` is the slim version used under the comment box.
 */
@Component({
  selector: 'app-file-picker',
  imports: [MatButtonModule, MatIconModule],
  template: `
    <input
      #fileInput
      class="native"
      type="file"
      multiple
      tabindex="-1"
      aria-hidden="true"
      [accept]="accept()"
      (change)="onSelected($event)"
    />

    @if (compact()) {
      <button mat-button type="button" class="attach" (click)="browse()" [disabled]="disabled()">
        <mat-icon>attach_file</mat-icon>
        Attach files
      </button>
    } @else {
      <div
        class="drop"
        [class.over]="dragging()"
        [class.disabled]="disabled()"
        (dragover)="onDragOver($event)"
        (dragleave)="dragging.set(false)"
        (drop)="onDrop($event)"
      >
        <span class="drop-icon" aria-hidden="true"><mat-icon>cloud_upload</mat-icon></span>
        <div class="drop-text">
          <strong>
            Drag files here or
            <button type="button" class="browse" (click)="browse()" [disabled]="disabled()">browse</button>
          </strong>
          <span>{{ hint() }}</span>
        </div>
      </div>
    }

    @if (files().length) {
      <ul class="chosen" [class.compact]="compact()" aria-label="Files to attach">
        @for (file of files(); track file) {
          <li>
            <mat-icon class="type" aria-hidden="true">{{ icon(file) }}</mat-icon>
            <span class="name" [title]="file.name">{{ file.name }}</span>
            <span class="size">{{ size(file) }}</span>
            <button
              type="button"
              class="remove"
              (click)="remove(file)"
              [disabled]="disabled()"
              [attr.aria-label]="'Remove ' + file.name"
            >
              <mat-icon>close</mat-icon>
            </button>
          </li>
        }
      </ul>
    }

    @if (errors().length) {
      <ul class="errors" role="alert">
        @for (error of errors(); track error) {
          <li><mat-icon>error</mat-icon>{{ error }}</li>
        }
      </ul>
    }
  `,
  styles: `
    :host {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .native {
      display: none;
    }
    .drop {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 16px 18px;
      border: 1.5px dashed var(--app-border-strong);
      border-radius: var(--app-radius);
      background: var(--app-surface-muted);
      transition:
        border-color 0.15s,
        background-color 0.15s;

      &.over {
        border-color: var(--app-primary);
        background: var(--app-primary-soft);
      }
      &.disabled {
        opacity: 0.6;
      }
    }
    .drop-icon {
      flex: none;
      display: grid;
      place-items: center;
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: var(--app-primary-soft);
      color: var(--app-primary);
    }
    .drop-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;

      strong {
        font-size: 13.5px;
        font-weight: 500;
        color: var(--app-text);
      }
      span {
        font-size: 12px;
        color: var(--app-text-muted);
      }
    }
    .browse {
      padding: 0;
      border: 0;
      background: none;
      font: inherit;
      font-weight: 600;
      color: var(--app-primary);
      text-decoration: underline;
      text-underline-offset: 2px;
      cursor: pointer;

      &:focus-visible {
        outline: 2px solid var(--app-primary);
        outline-offset: 2px;
        border-radius: 3px;
      }
    }
    .attach {
      align-self: flex-start;
      margin-left: -8px;
    }
    .chosen {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin: 0;
      padding: 0;
      list-style: none;

      &.compact {
        flex-direction: row;
        flex-wrap: wrap;
      }

      li {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
        padding: 6px 6px 6px 10px;
        border: 1px solid var(--app-border);
        border-radius: var(--app-radius-sm);
        background: var(--app-surface);
        font-size: 13px;
      }
      &.compact li {
        max-width: 260px;
        border-radius: 999px;
        padding: 3px 4px 3px 10px;
        font-size: 12.5px;
      }
    }
    .type {
      flex: none;
      font-size: 18px;
      width: 18px;
      height: 18px;
      color: var(--app-primary);
    }
    .name {
      flex: 1;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--app-text);
    }
    .size {
      flex: none;
      color: var(--app-text-muted);
      font-size: 12px;
    }
    .remove {
      flex: none;
      display: grid;
      place-items: center;
      width: 24px;
      height: 24px;
      padding: 0;
      border: 0;
      border-radius: 50%;
      background: none;
      color: var(--app-text-muted);
      cursor: pointer;

      &:hover {
        background: var(--app-surface-hover);
        color: var(--app-danger);
      }
      .mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
    .errors {
      margin: 0;
      padding: 0;
      list-style: none;
      font-size: 12.5px;
      color: var(--app-danger);

      li {
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
  `,
})
export class FilePicker {
  readonly files = model<File[]>([]);
  readonly compact = input(false);
  readonly disabled = input(false);

  private readonly config = inject(ConfigService);
  private readonly fileInput = viewChild.required<ElementRef<HTMLInputElement>>('fileInput');

  protected readonly errors = signal<string[]>([]);
  protected readonly dragging = signal(false);
  protected readonly accept = computed(() =>
    this.config
      .attachments()
      .allowed_extensions.map((extension) => `.${extension}`)
      .join(','),
  );
  protected readonly hint = computed(() => {
    const limits = this.config.attachments();
    const types = limits.allowed_extensions.map((extension) => extension.toUpperCase()).join(', ');
    return `${types} · up to ${limits.max_file_mb} MB each, ${limits.max_files} files`;
  });

  browse(): void {
    this.fileInput().nativeElement.click();
  }

  /** Adds files after checking them; problems are listed under the picker. */
  add(candidates: File[]): void {
    const { accepted, errors } = checkFiles(candidates, this.files().length, this.config.attachments());
    this.errors.set(errors);
    if (accepted.length) {
      this.files.update((list) => [...list, ...accepted]);
    }
  }

  remove(file: File): void {
    this.files.update((list) => list.filter((item) => item !== file));
    this.errors.set([]);
  }

  protected onSelected(event: Event): void {
    const element = event.target as HTMLInputElement;
    this.add(Array.from(element.files ?? []));
    element.value = ''; // allows choosing the same file again after removing it
  }

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    if (!this.disabled()) this.dragging.set(true);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(false);
    if (!this.disabled()) this.add(Array.from(event.dataTransfer?.files ?? []));
  }

  protected icon(file: File): string {
    return fileIcon(fileExtension(file.name));
  }

  protected size(file: File): string {
    return formatSize(file.size);
  }
}
