import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 text-sm font-medium rounded-md ${
    isActive ? "bg-brand-700 text-white" : "text-slate-200 hover:bg-brand-800"
  }`;

export function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-brand-800 text-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-lg font-semibold tracking-tight">
              ESG Emissions
            </Link>
            <nav className="flex gap-1">
              <NavLink to="/" end className={navLinkClass}>
                Dashboard
              </NavLink>
              {user?.is_uploader && (
                <NavLink to="/upload" className={navLinkClass}>
                  Upload
                </NavLink>
              )}
              {user?.is_analyst && (
                <NavLink to="/review" className={navLinkClass}>
                  Review
                </NavLink>
              )}
              <NavLink to="/audit" className={navLinkClass}>
                Audit
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-brand-100">
              {user?.tenant.company_name} · {user?.username}
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded border border-brand-600 px-3 py-1 hover:bg-brand-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        ESG Emissions Ingestion &amp; Review — MVP prototype
      </footer>
    </div>
  );
}
