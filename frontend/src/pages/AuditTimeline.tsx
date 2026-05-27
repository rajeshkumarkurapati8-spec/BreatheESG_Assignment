import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { fetchAuditLogs } from "../api/endpoints";
import { Loading } from "../components/Loading";

export function AuditTimelinePage() {
  const [entityType, setEntityType] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["audit-logs", entityType],
    queryFn: () =>
      fetchAuditLogs({
        entity_type: entityType || undefined,
      }),
  });

  if (isLoading) return <Loading />;
  if (error) return <p className="text-red-600">Failed to load audit logs.</p>;

  const logs = data?.results ?? [];

  return (
    <div>
      <h1 className="text-2xl font-semibold">Audit timeline</h1>
      <p className="mt-1 text-sm text-slate-600">Chronological activity across your tenant</p>

      <div className="mt-4">
        <select
          className="rounded border border-slate-300 px-3 py-2 text-sm"
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
        >
          <option value="">All entity types</option>
          <option value="data_source">Data source</option>
          <option value="normalized_emission_record">Emission record</option>
        </select>
      </div>

      <ol className="mt-8 relative border-l border-slate-200 ml-3">
        {logs.map((log) => (
          <li key={log.id} className="mb-8 ml-6">
            <span className="absolute -left-1.5 flex h-3 w-3 rounded-full bg-brand-600" />
            <time className="text-xs text-slate-500">
              {new Date(log.performed_at).toLocaleString()}
            </time>
            <p className="mt-1 text-sm font-medium text-slate-900">
              {log.action.replace(/_/g, " ")}{" "}
              <span className="font-normal text-slate-600">
                on {log.entity_type} #{log.entity_id}
              </span>
            </p>
            <p className="text-xs text-slate-500">
              by {log.performed_by_username ?? "system"}
            </p>
            {log.entity_type === "normalized_emission_record" && (
              <Link
                to={`/records/${log.entity_id}`}
                className="text-xs text-brand-700 hover:underline"
              >
                View record
              </Link>
            )}
            {Object.keys(log.new_values).length > 0 && (
              <pre className="mt-2 max-h-32 overflow-auto rounded bg-slate-50 p-2 text-xs">
                {JSON.stringify(log.new_values, null, 2)}
              </pre>
            )}
          </li>
        ))}
        {logs.length === 0 && (
          <li className="ml-6 text-slate-500 text-sm">No audit events yet.</li>
        )}
      </ol>
    </div>
  );
}
