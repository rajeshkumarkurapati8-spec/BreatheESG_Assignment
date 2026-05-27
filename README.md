# ESG Emissions Ingestion & Analyst Review Platform

Enterprise prototype for multi-tenant sustainability data ingestion, normalization, analyst review, and audit-locked emissions records.

**Stack:** Django REST Framework + PostgreSQL + React (Vite/TypeScript)  
**Deploy:** Render (API) · Vercel (UI) · Neon (PostgreSQL)

## Repository layout

```
backend/          # Django project + apps
frontend/         # React + Vite + TypeScript
docs/             # Architecture, models, decisions, deployment
```

## Local development (after setup)

See `docs/DEPLOYMENT.md` for environment variables and Docker.

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (requires Node.js 18+)
cd frontend && npm install && npm run dev
# UI: http://localhost:5173  (proxies /api to Django)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, boundaries, data flow |
| [docs/MODEL.md](docs/MODEL.md) | Data model rationale |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Engineering decisions *(Phase 8)* |
| [docs/TRADEOFFS.md](docs/TRADEOFFS.md) | Intentional omissions *(Phase 8)* |
| [docs/SOURCES.md](docs/SOURCES.md) | Research & assumptions *(Phase 8)* |

## Build phases

1. Architecture ✓  
2. Backend models ✓  
3. Ingestion services ✓  
4. REST APIs ✓  
5. Frontend ✓  
6. Tests  
7. Deployment  
8. Full documentation  
