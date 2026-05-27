# Phase 1 — Architecture Summary (for review)

## What we built in this phase

- Repository skeleton: `backend/`, `frontend/`, `docs/`
- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design, app boundaries, flows, API plan
- Root [README.md](../README.md) — orientation and phase list

**Not yet implemented:** Django project, models, parsers, API, UI, tests, deployment configs, MODEL/DECISIONS/TRADEOFFS/SOURCES.

---

## Architectural choices (explainable in an interview)

### 1. Five Django apps instead of one

**Choice:** `tenants`, `ingestion`, `emissions`, `review`, `audit`.

**Why:** Matches team boundaries and compliance concerns without deploying five services. An interviewer can ask “where does locking happen?” → `review` + `audit`.

**Avoided:** Microservices, event bus, separate “normalization service.”

### 2. Shared-database multi-tenancy

**Choice:** `tenant_id` on all tenant-owned rows; queryset filtering in permissions.

**Why:** Neon gives one Postgres; realistic for SMB ESG tools. Schema-per-tenant is ops-heavy for an intern MVP.

**Avoided:** Tenant resolution via subdomain, row-level security policies in Postgres (could add later).

### 3. Synchronous ingestion

**Choice:** Upload request runs parser → raw → normalized inline; status on `DataSource`.

**Why:** No Redis/Celery setup on Render free tier; easier to demo end-to-end. Honest about scale limits.

**Avoided:** “Enterprise” async job UI with progress websockets.

### 4. Explicit audit logging (not magic signals everywhere)

**Choice:** `audit.services.log_action()` called from review and ingestion orchestrator.

**Why:** Traceable in code review; signals alone are implicit and bug-prone.

**Avoided:** Full event-sourcing, immutable event store.

### 5. Three parsers behind one pipeline interface

**Choice:** `BaseIngestionParser` + `pipeline.run(data_source)`.

**Why:** Same upload endpoint, different `source_type`—realistic ops pattern without three copy-paste upload views.

### 6. `RawRecord` always stored

**Choice:** Keep original payload even when normalization fails.

**Why:** Analysts and auditors need to see what the company actually sent vs. what we derived.

### 7. Lock on approve (audit trail)

**Choice:** `locked_for_audit=True` after approval; edits blocked at service layer.

**Why:** Mimics SOX-style immutability for published emissions lines without blockchain theater.

---

## Intentional simplifications (Phase 1)

| Area | MVP | Full product |
|------|-----|----------------|
| Emission factors | Static table | Regional grids, supplier-specific factors |
| Travel ingestion | Mock JSON POST | OAuth to Concur/Navan |
| SAP | Subset: fuel CSV columns | IDoc, multiple modules |
| Auth | JWT + tenant on user | SSO, fine-grained RBAC |
| Files | CSV only for SAP/utility | Excel, PDF OCR |
| Async | None | SQS + worker for large files |

---

## Tradeoffs preview (for TRADEOFFS.md later)

1. **No real-time external travel API** — deterministic demo data; avoids API keys and rate limits.
2. **No workflow engine** — approve/reject are explicit endpoints, not Camunda/Temporal.
3. **No emission factor versioning** — factors in code/seed; versioning is a compliance feature for v2.

---

## Next phase (2): Backend models

Planned work:

1. `django-admin startproject` under `backend/`
2. Register five apps; custom user with `tenant`
3. Implement all models from brief + indexes
4. Initial migrations + `PlantCodeLookup` seed command
5. Draft `docs/MODEL.md` alongside models

Confirm to proceed with Phase 2, or share the assignment PDF if it adds requirements we should incorporate first.
