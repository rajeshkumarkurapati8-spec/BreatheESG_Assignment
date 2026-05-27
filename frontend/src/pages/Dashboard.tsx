import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchDashboard } from "../api/endpoints";
import { Loading } from "../components/Loading";

function formatKg(value: string | number) {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
  });

  if (isLoading) return <Loading />;
  if (error || !data) {
    return <p className="text-red-600">Failed to load dashboard.</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-600">Tenant emissions overview</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total emissions"
          value={`${formatKg(data.total_emissions_kg_co2e)} kg CO₂e`}
        />
        <StatCard
          label="Pending reviews"
          value={String(data.pending_reviews)}
          href="/review"
        />
        <StatCard
          label="Suspicious records"
          value={String(data.suspicious_records)}
          href="/review?suspicious=1"
        />
        <StatCard label="Scopes tracked" value={String(data.emissions_by_scope.length)} />
      </div>

      <section className="mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium">Emissions by scope</h2>
        <table className="mt-4 w-full text-sm">
          <thead>
            <tr className="border-b text-left text-slate-500">
              <th className="pb-2 font-medium">Scope</th>
              <th className="pb-2 font-medium">Records</th>
              <th className="pb-2 font-medium text-right">kg CO₂e</th>
            </tr>
          </thead>
          <tbody>
            {data.emissions_by_scope.map((row) => (
              <tr key={row.emission_scope} className="border-b border-slate-100">
                <td className="py-2 capitalize">{row.emission_scope}</td>
                <td className="py-2">{row.record_count}</td>
                <td className="py-2 text-right font-mono">
                  {formatKg(row.total_kg_co2e)}
                </td>
              </tr>
            ))}
            {data.emissions_by_scope.length === 0 && (
              <tr>
                <td colSpan={3} className="py-4 text-slate-500">
                  No normalized records yet.{" "}
                  <Link to="/upload" className="text-brand-700 underline">
                    Upload data
                  </Link>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function StatCard({
  label,
  value,
  href,
}: {
  label: string;
  value: string;
  href?: string;
}) {
  const inner = (
    <>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </>
  );
  const className =
    "rounded-lg border border-slate-200 bg-white p-5 shadow-sm hover:border-brand-200";
  if (href) {
    return (
      <Link to={href} className={className}>
        {inner}
      </Link>
    );
  }
  return <div className={className}>{inner}</div>;
}
