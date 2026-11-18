import { AttachmentConfig } from '../models/api.models';

/** Lets the browser save a blob under the given file name. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** 1536 -> "2 KB", 1572864 -> "1.5 MB" */
export function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

export function fileExtension(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot > 0 ? name.slice(dot + 1).toLowerCase() : '';
}

/** Material Symbols icon for a file type. */
export function fileIcon(extension: string): string {
  if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(extension)) return 'image';
  if (extension === 'pdf') return 'picture_as_pdf';
  if (['xlsx', 'csv'].includes(extension)) return 'table_chart';
  if (extension === 'zip') return 'folder_zip';
  if (['log', 'txt', 'json'].includes(extension)) return 'article';
  return 'description';
}

export interface FileCheck {
  accepted: File[];
  errors: string[];
}

/**
 * Quick checks in the browser with the backend's limits, so mistakes show up
 * straight away. The server checks every file again (including its contents).
 */
export function checkFiles(candidates: File[], alreadyChosen: number, config: AttachmentConfig): FileCheck {
  const accepted: File[] = [];
  const errors: string[] = [];
  const maxBytes = config.max_file_mb * 1024 * 1024;
  for (const file of candidates) {
    const extension = fileExtension(file.name);
    if (!config.allowed_extensions.includes(extension)) {
      errors.push(`${file.name}: this file type is not allowed.`);
    } else if (file.size === 0) {
      errors.push(`${file.name} is empty.`);
    } else if (file.size > maxBytes) {
      errors.push(`${file.name} is ${formatSize(file.size)}; the limit is ${config.max_file_mb} MB per file.`);
    } else if (alreadyChosen + accepted.length >= config.max_files) {
      errors.push(`You can attach up to ${config.max_files} files at a time.`);
      break;
    } else {
      accepted.push(file);
    }
  }
  return { accepted, errors };
}
