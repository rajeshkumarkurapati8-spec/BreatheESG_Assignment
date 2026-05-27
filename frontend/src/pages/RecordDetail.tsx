import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchAuditLogsForRecord, fetchNormalizedRecord } from "../api/endpoints";
import { Loading } from "../components/Loading";
import { StatusBadge } from "../components/StatusBadge";

export function RecordDetailPage() {
  const { id } = useParams<{ id: string }>();
  const recordId = Number(id);

  const { data: record, isLoading, error } = useQuery({
    queryKey: ["record", recordId],
    queryFn: () => fetchNormalizedRecord(recordId),
    enabled: !Number.isNaN(recordId),
  });

  const { data: auditLogs } = useQuery({
    queryKey: ["record-audit", recordId],
    queryFn: () => fetchAuditLogsForRecord(recordId),
    enabled: !Number.isNaN(recordId),
  });

  if (isLoading) return <Loading />;
  if (error || !record) {
    return <p className="text-red-600">Record not found.</p>;
  }

  const qty = Number(record.normalized_quantity);
  const factor = Number(record.emission_factor);
  const calculated = Number(record.calculated_emissions_kg_co2e);
  const raw = record.raw_record_detail;
  const breakdown = raw?.raw_payload?.calculated_breakdown as
    | Record<string, string>
    | undefined;

  return (
    <div>
      <Link to="/review" className="text-sm text-brand-700 hover:underline">
        ← Back to review
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Record #{record.id}</h1>
      <div className="mt-2 flex flex-wrap gap-2">
        <StatusBadge status={record.approval_status} />
        {record.suspicious_flag && (
          <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
            Suspicious
          </span>
        )}
        {record.locked_for_audit && (
          <span className="rounded bg-slate-200 px-2 py-0.5 text-xs">Audit locked</span>
        )}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-medium">Normalized data</h2>
          <dl className="mt-4 space-y-2 text-sm">
            <Row label="Scope" value={record.emission_scope_display} />
            <Row label="Category" value={record.category} />
            <Row label="Activity date" value={record.activity_date} />
            <Row
              label="Quantity"
              value={`${record.normalized_quantity} ${record.normalized_unit}`}
            />
            <Row label="Source system" value={record.source_system} />
            <Row label="Emission factor" value={`${record.emission_factor} kg CO₂e / unit`} />
            <Row
              label="Calculated"
              value={`${record.calculated_emissions_kg_co2e} kg CO₂e`}
            />
            {record.suspicious_reason && (
              <Row label="Suspicious reason" value={record.suspicious_reason} />
            )}
            {record.reviewed_by_username && (
              <Row
                label="Reviewed by"
                value={`${record.reviewed_by_username} at ${record.reviewed_at}`}
              />
            )}
          </dl>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-medium">Emissions calculation</h2>
          <div className="mt-4 rounded bg-slate-50 p-4 font-mono text-sm text-slate-800">
            <p>
              {qty} {record.normalized_unit} × {factor} kg CO₂e/{record.normalized_unit}
            </p>
            <p className="mt-2 font-semibold">= {calculated.toFixed(4)} kg CO₂e</p>
          </div>
          {breakdown && (
            <ul className="mt-4 space-y-1 text-sm text-slate-600">
              {Object.entries(breakdown).map(([k, v]) => (
                <li key={k}>
                  {k}: {v} kg CO₂e
                </li>
              ))}
            </ul>
          )}
          {(() => {
            const plant = raw?.raw_payload?.resolved_plant as
              | { plant_name?: string }
              | undefined;
            if (!plant) return null;
            return (
              <p className="mt-3 text-sm text-slate-600">
                Plant: {plant.plant_name ?? "Unknown"}
              </p>
            );
          })()}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="font-medium">Raw payload</h2>
          <pre className="mt-3 max-h-80 overflow-auto rounded bg-slate-900 p-4 text-xs text-slate-100">
            {JSON.stringify(raw?.raw_payload ?? {}, null, 2)}
          </pre>
          {raw?.validation_errors && raw.validation_errors.length > 0 && (
            <p className="mt-2 text-sm text-red-600">
              Validation: {raw.validation_errors.join("; ")}
            </p>
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="font-medium">Audit history (this record)</h2>
          <ul className="mt-4 space-y-3">
            {(auditLogs ?? []).map((log) => (
              <li
                key={log.id}
                className="border-l-2 border-brand-600 pl-4 text-sm"
              >
                <span className="font-medium">{log.action}</span>
                <span className="text-slate-500">
                  {" "}
                  — {log.performed_by_username ?? "system"} ·{" "}
                  {new Date(log.performed_at).toLocaleString()}
                </span>
                {Object.keys(log.new_values).length > 0 && (
                  <pre className="mt-1 text-xs text-slate-600">
                    {JSON.stringify(log.new_values, null, 2)}
                  </pre>
                )}
              </li>
            ))}
            {(auditLogs ?? []).length === 0 && (
              <li className="text-slate-500">No audit entries for this record yet.</li>
            )}
          </ul>
        </section>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}
