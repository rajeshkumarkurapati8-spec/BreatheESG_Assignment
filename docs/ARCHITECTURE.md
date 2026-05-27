# System Architecture

## Problem statement

Companies submit operational sustainability data from heterogeneous systems (SAP exports, utility portals, travel platforms). Data arrives messy, in different units and schemas. Analysts must validate suspicious rows before records enter an audit-locked state. Every state change must be traceable.

This is an **MVP prototype** scoped for a 4-day build: correct domain modeling and ingestion pipelines over UI polish or enterprise platform features.

---

## High-level topology

```
┌─────────────────┐     HTTPS/JWT      ┌──────────────────────────────┐
│  React (Vercel) │ ◄────────────────► │  Django REST (Render)        │
│  React Query    │                    │  ┌────────┐ ┌─────────────┐  │
│  Axios          │                    │  │ tenants│ │ ingestion   │  │
└─────────────────┘                    │  │emissions│ │ review      │  │
                                       │  │ audit  │ │ (services)  │  │
                                       └──────────┬───────────────────┘
                                                  │
                                       ┌──────────▼──────────┐
                                       │  PostgreSQL (Neon)  │
                                       └─────────────────────┘
```

**Deployment split:** Stateless API on Render; static SPA on Vercel; managed Postgres on Neon. No message queue in MVP—ingestion runs synchronously in the request/worker thread with clear status on `DataSource`.

---

## Django app boundaries

| App | Responsibility | Owns |
|-----|----------------|------|
| **tenants** | Multi-tenant identity & isolation | `Tenant`, tenant-scoped permissions |
| **ingestion** | Upload, raw storage, pipeline orchestration | `DataSource`, `RawRecord`, parsers, validation |
| **emissions** | Normalized domain records & calculations | `NormalizedEmissionRecord`, `PlantCodeLookup`, factor service |
| **review** | Analyst workflow (approve/reject/lock) | Review actions, filters, business rules for locks |
| **audit** | Append-only change log | `AuditLog`, signal/hook writers |

**Why five apps (not one monolith app):** Mirrors how a small team would split ownership—ingestion engineers vs. emissions domain vs. compliance/audit. Boundaries stay explainable in an interview without microservice overhead.

**Cross-cutting rule:** `NormalizedEmissionRecord` lives in `emissions` but state transitions that matter for compliance go through `review` services that call `audit` to write logs.

---

## Request / data flow

### Upload path (CSV or mocked API)

```
Client upload
    → POST /uploads/  (ingestion)
    → Create DataSource (processing_status=pending)
    → Parser selected by source_type (SAP | utility | travel)
    → For each row:
          RawRecord (raw_payload + validation_errors)
          if valid enough → NormalizationEngine → EmissionsCalculationService
          → NormalizedEmissionRecord (suspicious_flag, approval_status=pending)
    → DataSource.processing_status = completed | failed
    → AuditLog: source_uploaded, records_created (batch summary)
```

### Review path

```
Analyst → GET /review/pending/?suspicious=true
    → POST /review/approve/{id}/ or reject
    → review.services validates not locked
    → Update approval_status; on approve optionally lock_for_audit
    → audit.services.log_entity_change(...)
```

### Read path

```
Dashboard aggregates → emissions queries scoped by tenant
Record detail → normalized record + raw_record + audit logs by entity_id
```

---

## Multi-tenancy strategy

**Model:** Shared database, **row-level** tenant isolation via `ForeignKey(Tenant)` on tenant-owned tables.

| Approach | Choice | Rationale |
|----------|--------|-----------|
| Schema-per-tenant | No | Ops overhead; overkill for MVP |
| Shared DB + `tenant_id` | **Yes** | Standard for B2B SaaS prototypes; easy Neon hosting |
| Tenant from JWT | **Yes** | User profile links to one tenant for demo; staff users could be extended later |

**Enforcement:**

- Custom DRF permission: `IsTenantMember` — queryset `.filter(tenant=request.user.tenant)`.
- Never accept `tenant_id` from client on create without admin role (upload uses user's tenant).
- All list endpoints default-filtered by tenant.

**Intentional simplification:** No subdomain-based tenant routing; single API host.

---

## Authentication

- **SimpleJWT:** access + refresh tokens.
- User model: extend `AbstractUser` with `tenant` FK (in `tenants` app).
- Login → `/auth/token/` ; refresh → `/auth/token/refresh/`.
- Frontend stores access token in memory or `sessionStorage` (document tradeoff: XSS vs. persistence); refresh via axios interceptor.

**Not in MVP:** SSO, RBAC beyond `is_analyst` / `is_uploader` flags on user.

---

## Service layer (backend)

Keep fat models thin; put orchestration in services:

```
ingestion/
  services/
    parsers/
      sap_fuel.py          # CSV column mapping, German headers
      utility_electricity.py
      travel_api.py        # mocked JSON payload
    validation.py          # ValidationEngine
    normalization.py       # NormalizationEngine (delegates unit conversion)
    pipeline.py            # run_ingestion(data_source) orchestrator

emissions/
  services/
    calculation.py         # Emission factors, kg CO2e
    suspicious.py          # Utility spike: >2x rolling average

review/
  services/
    workflow.py            # approve, reject, lock checks

audit/
  services/
    logger.py              # log_action(entity_type, entity_id, old, new, user)
```

**No Celery in MVP:** Parsers run inline; `DataSource.processing_status` exposes progress. For files &lt; ~10k rows this is honest for an intern scope. Document async ingestion as future work in TRADEOFFS.md.

---

## Ingestion pipelines (design)

### 1. SAP fuel / procurement (CSV)

| Stage | Behavior |
|-------|----------|
| Parse | Map `Werk`, `Brennstoffart`, `Menge`, `Einheit`, `Buchungsdatum` (+ aliases) |
| Validate | Date parse (multi-format), positive quantity, known unit family |
| Normalize | Fuel → liters; plant via `PlantCodeLookup` |
| Scope | Scope 1 fuel combustion (simplified category map) |
| Output | `NormalizedEmissionRecord` linked to `RawRecord` |

### 2. Utility electricity (CSV)

| Stage | Behavior |
|-------|----------|
| Parse | meter_id, billing period, kwh_usage, tariff, facility |
| Validate | billing_start &lt; billing_end, non-negative kWh |
| Suspicious | Per meter_id: compare to rolling 6-period average; flag if &gt; 2x |
| Scope | Scope 2 electricity |
| Activity date | Midpoint of billing period (documented assumption) |

### 3. Corporate travel (mocked API)

| Stage | Behavior |
|-------|----------|
| Input | POST body mimicking Concur/Navan batch JSON (not real HTTP to vendor) |
| Validate | IATA airport codes, non-negative nights/distance |
| Normalize | Great-circle distance between airports; hotel nights factor; taxi km factor |
| Scope | Scope 3 business travel subcategories |

Each pipeline implements a common interface:

```python
class BaseIngestionParser(ABC):
    def parse_row(self, row: dict, row_number: int) -> tuple[RawRecord, NormalizedEmissionRecord | None]: ...
```

`pipeline.run(data_source)` selects parser by `source_type` + `ingestion_method`.

---

## API surface (planned)

| Prefix | Methods | Notes |
|--------|---------|-------|
| `/api/auth/` | token, refresh | SimpleJWT |
| `/api/tenants/` | CRUD (read-heavy) | Admin seed only in MVP |
| `/api/sources/` | list, retrieve | DataSource |
| `/api/uploads/` | create (multipart) | Triggers pipeline |
| `/api/raw-records/` | list, retrieve | Filter by data_source |
| `/api/normalized-records/` | list, retrieve | Dashboard + detail |
| `/api/review/pending/` | list | approval_status=pending |
| `/api/review/approve/` | POST | id in body |
| `/api/review/reject/` | POST | id in body |
| `/api/audit-logs/` | list | Filter entity_type, entity_id |

ViewSets for CRUD resources; `@action` or dedicated APIViews for review mutations (clearer audit semantics).

**Pagination:** PageNumberPagination, default page size 50.

**Filtering:** `django-filter` on suspicious_flag, approval_status, emission_scope, date range.

---

## Frontend architecture

```
src/
  api/           # axios instance, endpoints, types
  hooks/         # React Query keys + queries/mutations
  pages/         # Login, Dashboard, Upload, Review, Detail, Audit
  components/  # Table, Layout, StatusBadge, FileUpload
  types/         # mirrors API serializers
```

- **React Query** for server state; no Redux.
- **Tailwind** utility layout; one layout shell with nav.
- Routes: `/login`, `/`, `/upload`, `/review`, `/records/:id`, `/audit`.

Pages map 1:1 to analyst workflows—not feature-based component explosion.

---

## Audit model

Append-only `AuditLog`:

- `entity_type` + `entity_id` (string UUID/int as string for polymorphism without GenericForeignKey complexity in queries).
- `action`: `created`, `updated`, `approved`, `rejected`, `locked`, `upload_started`, etc.
- `old_values` / `new_values`: JSON snapshots of changed fields only.

**Writers:** Explicit calls from `review.workflow` and `ingestion.pipeline`—not blanket model signals (signals are harder to reason about in interviews). Optional signal only for `NormalizedEmissionRecord` post-save if we need belt-and-suspenders—prefer explicit.

---

## Emissions calculation (simplified)

Static factor table in code (or DB seed) for MVP:

| Category | Factor (illustrative) | Unit |
|----------|----------------------|------|
| Diesel | 2.68 | kg CO2e / liter |
| Electricity (grid avg) | 0.4 | kg CO2e / kWh |
| Short-haul flight | 0.15 | kg CO2e / km |
| Hotel night | 30 | kg CO2e / night |
| Taxi | 0.21 | kg CO2e / km |

Factors are **documented as placeholders**—real product would use DEFRA/EPA/eGRID regional data (SOURCES.md).

---

## Database indexing (planned)

- `(tenant_id, approval_status, suspicious_flag)` on normalized records — review queue.
- `(data_source_id, row_number)` on raw records.
- `(entity_type, entity_id, performed_at)` on audit logs.
- `PlantCodeLookup.code` PK.

---

## Security & deployment notes

- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` for Vercel preview + production URLs.
- `DATABASE_URL` from Neon via env.
- Docker Compose for local: `db` + `api` (optional `frontend` build).
- Render: `gunicorn` + `release: migrate`.
- Secrets never committed; `.env.example` in both packages.

---

## Testing strategy (later phases)

| Layer | Focus |
|-------|--------|
| Unit | `validation.py`, `normalization.py`, unit conversion, date parsing |
| Unit | SAP German column mapping, utility spike detection |
| API | Upload → raw + normalized counts; approve locks; reject audit entry |
| Integration | One fixture CSV per pipeline |

---

## Phase map (implementation order)

| Phase | Deliverable |
|-------|-------------|
| 1 | This document + repo skeleton |
| 2 | Django project, models, migrations, admin |
| 3 | Parsers + validation + normalization + calculation |
| 4 | DRF serializers, viewsets, JWT, permissions |
| 5 | React pages + API integration |
| 6 | pytest + API tests |
| 7 | Docker, Render, Vercel configs |
| 8 | MODEL, DECISIONS, TRADEOFFS, SOURCES |

---

## Assignment PDF note

No assignment PDF was found in the workspace at architecture time. Requirements above follow the written brief; if the PDF adds constraints (grading rubric, required endpoints), align in Phase 2+.
