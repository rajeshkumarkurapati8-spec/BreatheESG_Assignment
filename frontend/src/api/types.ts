export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Tenant {
  id: number;
  company_name: string;
  industry: string;
  created_at: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  tenant: Tenant;
  is_analyst: boolean;
  is_uploader: boolean;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface DashboardStats {
  total_emissions_kg_co2e: string;
  pending_reviews: number;
  suspicious_records: number;
  emissions_by_scope: {
    emission_scope: string;
    total_kg_co2e: string | number;
    record_count: number;
  }[];
}

export interface DataSource {
  id: number;
  source_type: string;
  ingestion_method: string;
  original_filename: string;
  processing_status: string;
  processing_summary: Record<string, unknown>;
  uploaded_at: string;
}

export interface RawRecord {
  id: number;
  data_source: number;
  raw_payload: Record<string, unknown>;
  row_number: number;
  validation_errors: string[];
  created_at: string;
}

export interface NormalizedRecordListItem {
  id: number;
  emission_scope: string;
  category: string;
  activity_date: string;
  normalized_unit: string;
  normalized_quantity: string;
  calculated_emissions_kg_co2e: string;
  suspicious_flag: boolean;
  approval_status: string;
  locked_for_audit: boolean;
  source_system: string;
  created_at: string;
}

export interface NormalizedRecord extends NormalizedRecordListItem {
  tenant: number;
  raw_record: number;
  raw_record_detail: RawRecord | null;
  emission_scope_display: string;
  approval_status_display: string;
  emission_factor: string;
  suspicious_reason: string;
  reviewed_by: number | null;
  reviewed_by_username: string | null;
  reviewed_at: string | null;
}

export interface AuditLog {
  id: number;
  entity_type: string;
  entity_id: string;
  action: string;
  old_values: Record<string, unknown>;
  new_values: Record<string, unknown>;
  performed_by_username: string | null;
  performed_at: string;
}

export type SourceType = "sap_fuel" | "utility_electricity" | "corporate_travel";
