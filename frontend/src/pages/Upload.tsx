import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { uploadCsv, uploadTravel } from "../api/endpoints";
import type { DataSource, SourceType } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

const SOURCE_OPTIONS: { value: SourceType; label: string }[] = [
  { value: "sap_fuel", label: "SAP Fuel / Procurement (CSV)" },
  { value: "utility_electricity", label: "Utility Electricity (CSV)" },
  { value: "corporate_travel", label: "Corporate Travel (JSON mock API)" },
];

export function UploadPage() {
  const { user } = useAuth();
  const [sourceType, setSourceType] = useState<SourceType>("sap_fuel");
  const [file, setFile] = useState<File | null>(null);
  const [travelJson, setTravelJson] = useState(
    '{\n  "trips": [\n    {\n      "employee_id": "E10001",\n      "trip_type": "air",\n      "departure_airport": "FRA",\n      "arrival_airport": "MUC",\n      "hotel_nights": 0,\n      "taxi_distance_km": 0,\n      "trip_date": "2024-07-01"\n    }\n  ]\n}'
  );
  const [result, setResult] = useState<DataSource | null>(null);
  const [parseError, setParseError] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      if (sourceType === "corporate_travel") {
        const payload = JSON.parse(travelJson);
        return uploadTravel(payload);
      }
      if (!file) throw new Error("Select a CSV file");
      return uploadCsv(sourceType, file);
    },
    onSuccess: (data) => {
      setResult(data);
      setParseError("");
    },
    onError: (err: Error) => {
      setResult(null);
      setParseError(err.message || "Upload failed");
    },
  });

  if (!user?.is_uploader) {
    return <Navigate to="/" replace />;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setParseError("");
    if (sourceType === "corporate_travel") {
      try {
        JSON.parse(travelJson);
      } catch {
        setParseError("Invalid JSON payload");
        return;
      }
    }
    mutation.mutate();
  }

  const summary = result?.processing_summary as Record<string, number> | undefined;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Upload data</h1>
      <p className="mt-1 text-sm text-slate-600">
        Submit operational data for normalization and review
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-6 max-w-xl space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <label className="block text-sm font-medium text-slate-700">Source type</label>
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as SourceType)}
          >
            {SOURCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {sourceType !== "corporate_travel" ? (
          <div>
            <label className="block text-sm font-medium text-slate-700">CSV file</label>
            <input
              type="file"
              accept=".csv"
              className="mt-1 block w-full text-sm"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-slate-700">
              API payload (JSON)
            </label>
            <textarea
              className="mt-1 w-full rounded border border-slate-300 font-mono text-xs p-3"
              rows={12}
              value={travelJson}
              onChange={(e) => setTravelJson(e.target.value)}
            />
          </div>
        )}

        {(parseError || mutation.isError) && (
          <p className="text-sm text-red-600">{parseError || "Upload failed"}</p>
        )}

        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded bg-brand-700 px-4 py-2 text-sm font-medium text-white hover:bg-brand-800 disabled:opacity-50"
        >
          {mutation.isPending ? "Processing…" : "Upload & ingest"}
        </button>
      </form>

      {result && (
        <section className="mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-medium">Processing results</h2>
          <div className="mt-2 flex items-center gap-2">
            <StatusBadge status={result.processing_status} />
            <span className="text-sm text-slate-600">{result.original_filename}</span>
          </div>
          {summary && (
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
              <Item label="Rows total" value={summary.rows_total} />
              <Item label="Raw created" value={summary.raw_created} />
              <Item label="Normalized" value={summary.normalized_created} />
              <Item label="Validation failed" value={summary.validation_failed} />
              <Item label="Suspicious" value={summary.suspicious_count} />
            </dl>
          )}
        </section>
      )}
    </div>
  );
}

function Item({ label, value }: { label: string; value?: number }) {
  return (
    <div className="rounded bg-slate-50 px-3 py-2">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-semibold">{value ?? "—"}</dd>
    </div>
  );
}
