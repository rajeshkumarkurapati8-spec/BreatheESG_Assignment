# Data Model

This document describes the model and architecture decisions for the ESG emissions ingestion and analyst review platform.

It is written from the perspective of a backend engineer defending the design in a technical review, with emphasis on tenant safety, traceability, and review semantics.

---

## Multi-tenancy

The platform uses a shared database and enforces tenant boundaries through explicit row-level scoping.

- `Tenant` is the root company/entity.
- `User` belongs to a tenant or is a null-tenant superuser.
- `DataSource` belongs to a tenant and represents one ingestion batch.
- `RawRecord` inherits tenant scope through `data_source`.
- `NormalizedEmissionRecord` stores tenant directly for fast review and query performance.

### Why tenant on normalized records?

Normalized rows are the review and reporting surface. If tenant filtering required joining from `NormalizedEmissionRecord → RawRecord → DataSource`, review queries would be heavier and more error-prone.

Storing tenant on normalized records is a deliberate redundancy for safety and performance. The service layer must set the tenant consistently from the source batch.

### Enforcement strategy

Tenant isolation is enforced in the request/permission layer. Review and listing endpoints filter by `request.user.tenant`, and approval/rejection lookups explicitly require the record to belong to the analyst's tenant.

This is a practical MVP choice: it avoids complex DB-level multi-tenant routing while preserving isolation in the application layer.

---

## Source-of-truth tracking

### DataSource

`DataSource` represents one upload or API batch. It is the operational unit of ingestion.

Fields of note:

- `source_type` selects parser behavior.
- `ingestion_method` distinguishes CSV upload from API mock.
- `original_filename` records the source artifact for audit.
- `uploaded_by` and `uploaded_at` record actor and time.
- `processing_status` tracks pipeline progress.
- `processing_summary` stores row counts and pipeline outcomes.

This object is the trace anchor for the ingest path. If a reconciliation question arises, `DataSource` answers “which file/batch and who submitted it?”.

### RawRecord

`RawRecord` stores the original parsed payload and row metadata.

Key properties:

- `raw_payload` preserves the exact submitted fields.
- `row_number` provides stable source-row identity within the batch.
- `validation_errors` keeps parsing and structural failures.

Raw records are intentionally retained even when validation fails.
That means the system does not lose the original source row just because it failed normalization.

**Why RawRecord exists:** it is the source-of-truth for ingestion. It separates the original input from derived emissions data.

---

## Normalization strategy

The model separates raw ingestion from canonical emissions records.

### NormalizedEmissionRecord

A normalized record is the first trusted emissions line after:

1. validation
2. unit conversion
3. date normalization
4. factor resolution
5. emissions calculation

Important stored fields:

- `emission_scope` (`scope1` / `scope2` / `scope3`)
- `category` (business domain bucket)
- `normalized_unit` / `normalized_quantity`
- `emission_factor` snapshot
- `calculated_emissions_kg_co2e`
- `source_system`
- `suspicious_flag` / `suspicious_reason`
- `approval_status`
- `locked_for_audit`

### Why normalized records are separated

Raw ingestion and reporting are separate concerns.

- `RawRecord` is about what was submitted.
- `NormalizedEmissionRecord` is about what the system accepted for emissions accounting.

This avoids exposing parser internals through the review API and enables an audit trail from source payload to approved emission line.

---

## Suspicious record handling

The model supports suspicious scoring directly on normalized records.

- `suspicious_flag` is a boolean rule output.
- `suspicious_reason` stores analyst-facing explanation.

The rule engine in the ingestion layer can mark records without blocking them. For example, utility electricity rows can be accepted while still flagged when usage exceeds twice the rolling average for the same meter.

This is deliberate: suspicious handling is advisory during review, not a hard ingestion failure.

---

## Review workflow

The `review` app is intentionally model-free. Review behavior is implemented in services.

### Flow

- analyst requests pending records
- analyst approves or rejects a normalized record
- service layer validates analyst role and tenant ownership
- approve sets `approval_status=approved` and `locked_for_audit=True`
- reject sets `approval_status=rejected`; record remains unlocked

### Locking strategy

Approval is the transition that makes a record audit-locked.

- `pending` and `locked_for_audit=False` are mutable during ingestion/review.
- `approved` and `locked_for_audit=True` are treated as immutable.
- rejected records remain unlocked so downstream processes can still examine them.

This is a practical lock model for an MVP: the system enforces immutability through service validation rather than complicated DB constraints.

---

## Auditability

Audit records are explicit and append-only.

### AuditLog design

`AuditLog` stores:

- `entity_type` and `entity_id` instead of foreign keys, to avoid cross-model coupling
- `action` for lifecycle events
- `old_values` and `new_values` as JSON diffs
- `performed_by` and `performed_at`

The pipeline writes audit entries at key points: upload start/completion/failure and record approve/reject/lock.

This makes it possible to trace a normalized record from source ingestion through analyst decision.

---

## Emission scope categorization

The model uses discrete scope choices aligned with GHG protocol semantics:

- `scope1`: direct emissions, primarily SAP fuel
- `scope2`: indirect purchased electricity
- `scope3`: travel and other downstream activities

Scope is assigned by parser logic, not by review or analysis. That keeps classification deterministic and consistent in the data model.

---

## Ingestion architecture

The ingestion path is synchronous and explicit.

1. create `DataSource`
2. parse rows into `RawRecord`
3. validate each row
4. normalize units and dates
5. calculate emissions
6. persist `NormalizedEmissionRecord`
7. update `DataSource.processing_summary`
8. emit audit log entries

This design avoids queue infrastructure while preserving the full lineage of each row.

---

## Tenant isolation

Tenant isolation is enforced at the application layer:

- `request.user.tenant` scopes all relevant querysets
- `DataSource` and `NormalizedEmissionRecord` always store tenant IDs
- review endpoints only look up records within `request.user.tenant`

The model intentionally does not store tenant on `AuditLog`; audit rows are scoped by the actor and entity IDs, not by tenant field.

---

## Analyst review process

Analyst users do not ingest data. Their workflow is:

- inspect pending normalized records in `/api/review/pending/`
- approve or reject individual records
- approval sets an audit lock and emits approval + lock entries
- rejection preserves unlocked state so the record can remain informational and potentially be corrected by a later ingestion

This keeps the review process lightweight and makes the audit trail primary. Rejected records are not deleted or overwritten; they remain part of history.

---

## Engineering rationale

- Multi-tenancy uses a single database to reduce operational overhead for MVP.
- Source-of-truth tracking is explicit: `DataSource` → `RawRecord` → `NormalizedEmissionRecord`.
- Auditing is explicit and service-driven, not implicit via signals.
- Suspicious handling is a first-class field on normalized records, not a separate flag table.
- Locking is stateful, not enforced by database-level immutability, which is appropriate for a small deployed prototype.
- Emission scope is stored as a typed choice so downstream dashboards and filters can rely on consistent classification.

The architecture is intentionally pragmatic: it keeps the platform understandable in code review while preserving the necessary lineage for compliance and tenant separation.
