import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { approveRecord, fetchPendingReview, rejectRecord } from "../api/endpoints";
import { Loading } from "../components/Loading";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

export function ReviewQueuePage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const suspiciousOnly = searchParams.get("suspicious") === "1";
  const [search, setSearch] = useState("");
  const [rejectId, setRejectId] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["review-pending", suspiciousOnly, search],
    queryFn: () =>
      fetchPendingReview({
        suspicious: suspiciousOnly || undefined,
        search: search || undefined,
      }),
  });

  const approveMut = useMutation({
    mutationFn: approveRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-pending"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const rejectMut = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => rejectRecord(id, reason),
    onSuccess: () => {
      setRejectId(null);
      setRejectReason("");
      queryClient.invalidateQueries({ queryKey: ["review-pending"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (!user?.is_analyst) {
    return <Navigate to="/" replace />;
  }

  if (isLoading) return <Loading />;
  if (error) return <p className="text-red-600">Failed to load review queue.</p>;

  const rows = data?.results ?? [];

  return (
    <div>
      <h1 className="text-2xl font-semibold">Review queue</h1>
      <p className="mt-1 text-sm text-slate-600">Approve or reject pending emission records</p>

      <div className="mt-4 flex flex-wrap gap-3">
        <input
          type="search"
          placeholder="Search category, source…"
          className="rounded border border-slate-300 px-3 py-2 text-sm w-64"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={suspiciousOnly}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams);
              if (e.target.checked) next.set("suspicious", "1");
              else next.delete("suspicious");
              navigate({ pathname: "/review", search: next.toString() });
            }}
          />
          Suspicious only
        </label>
      </div>

      <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">ID</th>
              <th className="px-4 py-3 font-medium">Scope</th>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium text-right">kg CO₂e</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                className={`border-t ${
                  row.suspicious_flag ? "bg-amber-50" : ""
                }`}
              >
                <td className="px-4 py-3">
                  <Link to={`/records/${row.id}`} className="text-brand-700 hover:underline">
                    #{row.id}
                  </Link>
                </td>
                <td className="px-4 py-3 capitalize">{row.emission_scope}</td>
                <td className="px-4 py-3">{row.category}</td>
                <td className="px-4 py-3">{row.activity_date}</td>
                <td className="px-4 py-3 text-right font-mono">
                  {Number(row.calculated_emissions_kg_co2e).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={row.approval_status} />
                  {row.suspicious_flag && (
                    <span className="ml-1 text-xs text-amber-700">⚠ suspicious</span>
                  )}
                </td>
                <td className="px-4 py-3 space-x-2">
                  <button
                    type="button"
                    className="rounded bg-brand-700 px-2 py-1 text-xs text-white hover:bg-brand-800 disabled:opacity-50"
                    disabled={approveMut.isPending}
                    onClick={() => approveMut.mutate(row.id)}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="rounded border border-red-300 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                    onClick={() => setRejectId(row.id)}
                  >
                    Reject
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                  No pending records
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {rejectId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
            <h3 className="font-medium">Reject record #{rejectId}</h3>
            <textarea
              className="mt-3 w-full rounded border border-slate-300 p-2 text-sm"
              rows={3}
              placeholder="Optional reason…"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded border px-3 py-1 text-sm"
                onClick={() => setRejectId(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="rounded bg-red-600 px-3 py-1 text-sm text-white"
                onClick={() => rejectMut.mutate({ id: rejectId, reason: rejectReason })}
              >
                Confirm reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
