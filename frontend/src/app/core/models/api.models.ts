/**
 * TypeScript shapes of the JSON returned by the Django API.
 * Keeping them in one file makes it easy to see the whole contract.
 */

export type Role = 'requester' | 'agent';
export type TicketStatus = 'open' | 'in_progress' | 'resolved';
export type ExportFileType = 'pdf' | 'xlsx';

export interface Paginated<T> {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: T[];
}

/** Error body produced by the backend's custom exception handler. */
export interface ApiErrorBody {
  message: string;
  errors: Record<string, string[] | string>;
}

// ---------------------------------------------------------------- users
export interface UserSummary {
  id: string;
  username: string;
  full_name: string;
  email: string;
  initials: string;
  role: Role;
}

export interface User extends UserSummary {
  first_name: string;
  last_name: string;
  job_title: string;
  role_label: string;
  is_agent: boolean;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface DemoAccount {
  username: string;
  password: string;
  label: string;
  description: string;
  icon: string;
  full_name: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  confirm_password: string;
}

// ---------------------------------------------------------------- configuration
export interface LookupOption {
  id: string;
  code: string;
  label: string;
  description: string;
  icon: string;
  color: string;
  sort_order: number;
  is_default: boolean;
}

export interface LookupType {
  id: string;
  code: string;
  name: string;
  description: string;
  is_system: boolean;
  value_count: number;
}

export interface LookupValue {
  id: string;
  lookup_type: string;
  lookup_type_code: string;
  lookup_type_name: string;
  code: string;
  label: string;
  description: string;
  icon: string;
  color: string;
  sort_order: number;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface StatusOption {
  value: TicketStatus;
  label: string;
  icon: string;
  color: string;
  description: string;
  transitions: TicketStatus[];
}

export interface ValueLabel {
  value: string;
  label: string;
}

export interface AppConfig {
  statuses: StatusOption[];
  categories: LookupOption[];
  priorities: LookupOption[];
  activity_types: ValueLabel[];
  roles: ValueLabel[];
  agents: UserSummary[];
  export_formats: { value: ExportFileType; label: string }[];
  validation: {
    title_min: number;
    title_max: number;
    description_min: number;
    description_max: number;
    resolution_min: number;
  };
  similarity: SimilarityConfig;
}

/** Similar ticket suggestions, as configured in the backend. */
export interface SimilarityConfig {
  enabled: boolean;
  max_results: number;
  /** Characters of title + description needed before a search. */
  min_length: number;
}

// ---------------------------------------------------------------- tickets
export interface Ticket {
  id: string;
  reference: string;
  title: string;
  category: LookupOption;
  priority: LookupOption | null;
  status: TicketStatus;
  status_label: string;
  created_by: UserSummary;
  assigned_to: UserSummary | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface TicketDetail extends Ticket {
  description: string;
  resolution_note: string;
  resolved_by: UserSummary | null;
  allowed_statuses: ValueLabel[];
  can_manage: boolean;
}

export interface TicketCreatePayload {
  title: string;
  description: string;
  category: string;
  priority?: string | null;
}

export interface TicketUpdatePayload {
  status?: TicketStatus;
  resolution_note?: string;
  assigned_to?: string | null;
  category?: string;
  priority?: string | null;
}

export interface TicketActivity {
  id: string;
  ticket: { id: string; reference: string; title: string };
  actor: UserSummary | null;
  activity_type: string;
  activity_label: string;
  icon: string;
  message: string;
  from_status: TicketStatus | '';
  to_status: TicketStatus | '';
  note: string;
  created_at: string;
}

// ---------------------------------------------------------------- similar tickets
export type SimilarityEngine = 'semantic' | 'keyword';

/** A resolved ticket suggested because it looks like the new issue. */
export interface SimilarTicket {
  id: string;
  reference: string;
  title: string;
  description: string;
  resolution_note: string;
  category: LookupOption;
  resolved_at: string | null;
  resolved_by: { full_name: string; initials: string } | null;
  /** Cosine similarity, 0 (unrelated) to 1 (same meaning). */
  score: number;
  match: 'strong' | 'possible';
}

export interface SimilarTicketsQuery {
  title?: string;
  description?: string;
  /** Leave this ticket out (when looking from an existing ticket). */
  exclude?: string | null;
}

export interface SimilarTicketsResponse {
  results: SimilarTicket[];
  engine: SimilarityEngine;
  model: string;
  compared: number;
  min_score: number;
}

export interface CountItem {
  count: number;
}

export interface TicketStats {
  total: number;
  by_status: (StatusOption & CountItem)[];
  by_category: (LookupOption & CountItem)[];
  created_last_7_days: number;
  resolved_last_7_days: number;
  average_resolution_hours: number | null;
  recent: Ticket[];
  assigned_to_me_open?: number;
  unassigned_open?: number;
}
