import { api } from "./client";
import type {
  AuditLog,
  DashboardStats,
  DataSource,
  NormalizedRecord,
  NormalizedRecordListItem,
  Paginated,
  SourceType,
  TokenPair,
  User,
} from "./types";

export async function login(username: string, password: string): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>("/api/auth/token/", { username, password });
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/api/auth/me/");
  return data;
}

export async function fetchDashboard(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/api/dashboard/");
  return data;
}

export async function uploadCsv(sourceType: SourceType, file: File): Promise<DataSource> {
  const form = new FormData();
  form.append("source_type", sourceType);
  form.append("file", file);
  const { data } = await api.post<DataSource>("/api/uploads/", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function uploadTravel(payload: object): Promise<DataSource> {
  const { data } = await api.post<DataSource>("/api/uploads/", {
    source_type: "corporate_travel",
    api_payload: payload,
  });
  return data;
}

export async function fetchPendingReview(params?: {
  suspicious?: boolean;
  search?: string;
}): Promise<Paginated<NormalizedRecordListItem>> {
  const { data } = await api.get<Paginated<NormalizedRecordListItem>>(
    "/api/review/pending/",
    {
      params: {
        suspicious: params?.suspicious || undefined,
        search: params?.search || undefined,
      },
    }
  );
  return data;
}

export async function fetchNormalizedRecord(id: number): Promise<NormalizedRecord> {
  const { data } = await api.get<NormalizedRecord>(`/api/normalized-records/${id}/`);
  return data;
}

export async function approveRecord(id: number): Promise<NormalizedRecord> {
  const { data } = await api.post<NormalizedRecord>("/api/review/approve/", { id });
  return data;
}

export async function rejectRecord(id: number, reason?: string): Promise<NormalizedRecord> {
  const { data } = await api.post<NormalizedRecord>("/api/review/reject/", {
    id,
    reason,
  });
  return data;
}

export async function fetchAuditLogs(params?: {
  entity_type?: string;
  entity_id?: string;
}): Promise<Paginated<AuditLog>> {
  const { data } = await api.get<Paginated<AuditLog>>("/api/audit-logs/", { params });
  return data;
}

export async function fetchAuditLogsForRecord(recordId: number): Promise<AuditLog[]> {
  const { data } = await api.get<Paginated<AuditLog>>("/api/audit-logs/", {
    params: { entity_type: "normalized_emission_record", entity_id: String(recordId) },
  });
  return data.results;
}
