# Phase 5 — React Frontend Summary

## Stack

- React 18 + Vite + TypeScript
- TailwindCSS
- TanStack React Query
- Axios (JWT in `sessionStorage`)
- React Router v6

## Pages

| Route | Page | Roles |
|-------|------|-------|
| `/login` | Sign in | Public |
| `/` | Dashboard KPIs + scope table | All |
| `/upload` | CSV / travel JSON upload | Uploader |
| `/review` | Pending queue, approve/reject | Analyst |
| `/records/:id` | Raw + normalized + calculation + audit | All |
| `/audit` | Tenant audit timeline | All |

## Local dev

**Terminal 1 — API:**
```powershell
cd backend
.\.venv\Scripts\python manage.py runserver
```

**Terminal 2 — UI:**
```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` → `http://127.0.0.1:8000`.

Demo logins: `analyst` / `uploader` — password `demo1234`

## Production (Vercel)

Set environment variable:
```
VITE_API_URL=https://your-render-api.onrender.com
```

`vercel.json` enables SPA routing.

## Structure

```
frontend/src/
  api/          client, endpoints, types
  context/      AuthContext
  components/   Layout, badges, loading
  pages/        6 screens
```

## Next: Phase 6 — Tests (backend), Phase 7 — Deployment, Phase 8 — Docs
