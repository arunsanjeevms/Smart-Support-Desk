import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { AppConfig, LookupOption, StatusOption } from '../models/api.models';
import { ApiService } from './api.service';

/**
 * Backend-managed options (statuses, categories, priorities, ...).
 *
 * Nothing in the UI hard-codes these lists: they come from GET /api/config/,
 * so values added in the Django admin or the Configuration screen show up
 * without a frontend change.
 */
@Injectable({ providedIn: 'root' })
export class ConfigService {
  private readonly api = inject(ApiService);
  private readonly configSignal = signal<AppConfig | null>(null);

  readonly config = this.configSignal.asReadonly();
  readonly loaded = computed(() => this.configSignal() !== null);
  readonly statuses = computed(() => this.configSignal()?.statuses ?? []);
  readonly categories = computed(() => this.configSignal()?.categories ?? []);
  readonly priorities = computed(() => this.configSignal()?.priorities ?? []);
  readonly agents = computed(() => this.configSignal()?.agents ?? []);
  readonly activityTypes = computed(() => this.configSignal()?.activity_types ?? []);
  readonly roles = computed(() => this.configSignal()?.roles ?? []);
  readonly exportFormats = computed(
    () =>
      this.configSignal()?.export_formats ?? [
        { value: 'pdf' as const, label: 'PDF' },
        { value: 'xlsx' as const, label: 'Excel' },
      ],
  );
  readonly validation = computed(
    () =>
      this.configSignal()?.validation ?? {
        title_min: 5,
        title_max: 150,
        description_min: 20,
        description_max: 5000,
        resolution_min: 10,
      },
  );

  readonly attachments = computed(
    () =>
      this.configSignal()?.attachments ?? {
        max_file_mb: 10,
        max_files: 5,
        allowed_extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'txt', 'log', 'csv', 'json', 'xlsx', 'docx', 'zip'],
      },
  );

  readonly similarity = computed(
    () =>
      this.configSignal()?.similarity ?? {
        enabled: false,
        max_results: 3,
        min_length: 10,
        category_suggestions: false,
      },
  );

  private readonly statusMap = computed(
    () => new Map(this.statuses().map((status) => [status.value as string, status])),
  );

  load(): Observable<AppConfig> {
    return this.api.get<AppConfig>('config/').pipe(tap((config) => this.configSignal.set(config)));
  }

  clear(): void {
    this.configSignal.set(null);
  }

  status(value: string | null | undefined): StatusOption | undefined {
    return value ? this.statusMap().get(value) : undefined;
  }

  defaultPriority(): LookupOption | undefined {
    return this.priorities().find((priority) => priority.is_default);
  }
}
