# Data Model

This document explains the domain model for the ESG emissions ingestion and analyst review platform. Implementation lives under `backend/` across five Django apps.

---

## Entity relationship overview

```
Tenant ─────────────┬──────────── DataSource ──── RawRecord
    │               │                  │              │
    │               │                  │              │ 1:1 (when normalized)
    │               └──── User         │              ▼
    │                    (uploaded_by)│     NormalizedEmissionRecord
    │                                   │              │
    └───────────────────────────────────┴──────────────┘
                                                    │
                              reviewed_by ──────────┤
                                                    │
AuditLog (entity_type + entity_id) ─── polymorphic reference, no FK

PlantCodeLookup — standalone reference (SAP Werk → plant name)
```

---

## Multi-tenancy

**Pattern:** Shared PostgreSQL database, **row-level** isolation.

| Model | Tenant FK | Notes |
|-------|-----------|-------|
| `Tenant` | — | Root entity |
| `User` | optional | Null only for Django superuser |
| `DataSource` | required | Uploads scoped to company |
| `RawRecord` | via `data_source` | Inherited scope |
| `NormalizedEmissionRecord` | required | Denormalized for query performance |
| `AuditLog` | — | `performed_by` links to user (who has tenant) |
| `PlantCodeLookup` | — | **Global** reference data (same SAP codes across clients in MVP) |

**Why duplicate `tenant` on `NormalizedEmissionRecord`:** Review queue and dashboard queries filter by tenant without joining through `raw_record → data_source`. In production you might enforce consistency with DB constraints or triggers; MVP relies on service layer always setting tenant from `DataSource`.

**Enforcement (Phase 4):** DRF permissions filter querysets with `request.user.tenant_id`. Clients never pass arbitrary `tenant_id` on create.

---

## Core entities

### Tenant

Represents one reporting company.

| Field | Purpose |
|-------|---------|
| `company_name` | Display / legal name |
| `industry` | Context for benchmarks (not heavily used in MVP) |
| `created_at` | Onboarding audit |

### User (`AUTH_USER_MODEL`)

Extends Django `AbstractUser`.

| Field | Purpose |
|-------|---------|
| `tenant` | Company membership |
| `is_analyst` | Can approve/reject records |
| `is_uploader` | Can POST uploads |

MVP uses coarse flags instead of a permission matrix — sufficient for demo, document as simplification.

---

## Source tracking

### DataSource

One **ingestion run**: a CSV file or mocked API batch.

| Field | Purpose |
|-------|---------|
| `source_type` | `sap_fuel`, `utility_electricity`, `corporate_travel` — selects parser |
| `ingestion_method` | `csv_upload` or `api_mock` |
| `original_filename` | Audit trail for file-based sources |
| `uploaded_by` / `uploaded_at` | Who submitted and when |
| `processing_status` | `pending` → `processing` → `completed` / `failed` |
| `processing_summary` | JSON row counts, error totals (set by pipeline) |

**Design intent:** Analysts and auditors can answer “what file produced these numbers?” without digging in object storage.

### RawRecord

**Immutable capture** of one source row.

| Field | Purpose |
|-------|---------|
| `raw_payload` | Exact parsed fields (German SAP headers preserved in JSON keys) |
| `row_number` | 1-based index; unique per `data_source` |
| `validation_errors` | List of strings; empty means structurally valid |

**Why keep invalid rows:** Failed validation still stored so analysts can see what the company sent and fix upstream exports.

**Normalization link:** `NormalizedEmissionRecord.raw_record` is `OneToOneField` — at most one canonical line per raw row.

---

## Normalized emissions domain

### NormalizedEmissionRecord

Canonical line after validation, unit conversion, and emission calculation.

| Field | Purpose |
|-------|---------|
| `emission_scope` | `scope1`, `scope2`, `scope3` (GHG Protocol aligned labels) |
| `category` | Finer bucket: e.g. `stationary_combustion`, `purchased_electricity`, `business_travel_air` |
| `activity_date` | When activity occurred (or utility billing midpoint) |
| `normalized_unit` / `normalized_quantity` | Standardized activity data (liters, kWh, km) |
| `emission_factor` | Factor **at time of calculation** (snapshot for audit) |
| `calculated_emissions_kg_co2e` | `quantity × factor` |
| `source_system` | e.g. `sap_mm`, `utility_portal`, `concur_mock` |
| `suspicious_flag` / `suspicious_reason` | Rule engine output (e.g. utility spike) |
| `approval_status` | `pending`, `approved`, `rejected` |
| `locked_for_audit` | `True` → no edits (set on approve in Phase 3) |
| `reviewed_by` / `reviewed_at` | Analyst accountability |

**Indexes:** `(tenant, approval_status, suspicious_flag)` optimizes review queue; `(tenant, emission_scope)` for dashboard breakdown.

### PlantCodeLookup

Maps SAP `Werk` codes to facility metadata.

| Field | Purpose |
|-------|---------|
| `code` (PK) | SAP plant code |
| `plant_name` | Resolved name |
| `country` | ISO-2 for regional factors (future) |

Includes `UNKNOWN` fallback so ingestion never hard-fails on unmapped plants — flags for analyst review instead.

**Global table:** Shared across tenants in MVP. Multi-tenant plant registries would be a v2 feature.

---

## Auditability

### AuditLog

**Append-only.** No update/delete in Django admin.

| Field | Purpose |
|-------|---------|
| `entity_type` | `data_source`, `raw_record`, `normalized_emission_record`, `tenant` |
| `entity_id` | String PK (avoids GenericForeignKey) |
| `action` | `created`, `approved`, `locked`, `upload_completed`, etc. |
| `old_values` / `new_values` | JSON diff snapshots (changed fields only) |
| `performed_by` / `performed_at` | Actor and timestamp |

**Written explicitly** from ingestion pipeline and review services (Phase 3), not blanket `post_save` signals — easier to explain in code review.

### Lock semantics

```
pending + locked_for_audit=False  → editable by pipeline retry (MVP: no re-run)
approved + locked_for_audit=True  → immutable
rejected + locked_for_audit=False → stays rejected; re-upload creates new rows
```

`is_editable` property on model: `not locked_for_audit`.

---

## Scope categorization (by source)

| Source | Typical scope | Category examples |
|--------|---------------|-------------------|
| SAP fuel CSV | Scope 1 | `stationary_combustion`, fuel type from `Brennstoffart` |
| Utility electricity | Scope 2 | `purchased_electricity` |
| Corporate travel (mock API) | Scope 3 | `business_travel_air`, `hotel_stay`, `ground_transport` |

Parsers assign scope in Phase 3; model only stores the result.

---

## Normalization flow (data perspective)

```
CSV/API row
    → RawRecord.raw_payload
    → ValidationEngine → validation_errors
    → NormalizationEngine → normalized_unit, normalized_quantity, activity_date
    → EmissionsCalculationService → emission_factor, calculated_emissions_kg_co2e
    → NormalizedEmissionRecord (suspicious_flag from SuspiciousRules)
```

Emission factor is **copied onto the record** so historical recalculations do not silently change published numbers.

---

## Review app (no tables)

`review` has no models. Workflow mutates `NormalizedEmissionRecord` and writes `AuditLog`. Keeps compliance logic out of generic CRUD.

---

## Seed commands

```bash
python manage.py migrate
python manage.py seed_plant_codes
python manage.py seed_demo_users
```

---

## Phase 2 deliverables checklist

- [x] Django project `config`
- [x] Apps: `tenants`, `ingestion`, `emissions`, `review`, `audit`
- [x] All models per assignment spec
- [x] Indexes for review queue and audit timeline
- [x] Admin registration (audit log read-only)
- [x] `seed_plant_codes` and `seed_demo_users` commands
- [ ] Migrations committed after `makemigrations` run locally
