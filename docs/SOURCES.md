# Source Assumptions and Data Decisions

This document records the assumptions made about source data, sample payloads, and operational limitations for the MVP.

## SAP export assumptions

The implementation assumes a narrow SAP fuel export shape, not a full SAP integration.

- expected fields include plant code, fuel type, unit, quantity, date, and cost center.
- exports are structured CSV, not free-form reports.
- `Werk` values map to a shared `PlantCodeLookup` table.
- unmapped plants are treated as suspicious rather than fatal.

This is a pragmatic assumption for initial coverage. A real SAP project would need to support multiple report variants, currency normalization, and possibly direct ERP extract APIs.

## Utility billing export assumptions

Utility ingestion assumes that billing data arrives in a CSV-like table with stable meter identifiers.

- each row represents one billing period
- billing start/end dates are available
- usage is reported in kWh or in a unit convertible to kWh
- meter IDs persist across uploads so rolling averages are meaningful

This works for a common class of utility portal exports, but it does not cover meter aggregation, partial period splits, or vendor-specific file formats.

## Concur / Navan travel assumptions

Travel ingestion is based on mock JSON payloads, not a real vendor integration.

- payloads are assumed to contain trip entries with discrete flight, hotel, and ground transport quantities
- distances are expressed in kilometers and nights as integer values
- the payload shape is stable and pre-agreed for the mock

That assumption is intentionally limited. Real travel systems have richer itinerary data, currency issues, itinerary changes, and provider-specific field names.

## Realistic sample data choices

The sample data is chosen to exercise the core normalization and review paths, not to prove complete source coverage.

- SAP sample uses messy column headers and German labels to validate parser robustness.
- utility sample includes billing periods and meter IDs to exercise spike detection.
- travel sample is a batch JSON with flight/hotel/taxi fields to demonstrate scope 3 normalization.

These choices are realistic enough to show the platform working, but they are not a substitute for actual partner data contracts.

## Emission factor simplifications

Emission factors are encoded as static constants in code.

- fuel factors are per liter for diesel, petrol, heating oil, and a default fuel factor
- electricity uses a single grid-average kWh factor
- travel uses fixed per-km and per-night factors

This is acceptable for MVP validation, but it is not sufficient for regulated reporting because it lacks region, supplier, or time-based factor versioning.

## Enterprise operational limitations

The MVP is intentionally not enterprise-grade in several ways.

- ingestion is synchronous, so large files may block and slow down the service
- tenant isolation is enforced in application code, not via DB row-level security
- source connectors are mocked or CSV-only, so upstream vendor changes are manual
- audit logging is explicit but does not include tenant metadata on `AuditLog`

These limitations are acceptable for a demo and initial product fit, but they would need to be addressed before broad enterprise adoption.

## What would fail at large scale

The current design would struggle with:

- very large CSV uploads due to synchronous processing and memory use
- multiple source variants from the same ERP or vendor without parser extensibility
- concurrent uploads and review actions under high tenant volume
- factor management and historical recalculation requirements

If the platform were scaled, it would need batching, job queues, schema-driven ingestion, and stronger tenant isolation.

## Where manual analyst review is still required

The platform still relies on analysts for decisions that cannot be automated safely.

- approvals and rejects based on context or data quality
- review of suspicious utility spikes and unmapped SAP plants
- handling of records with unclear source data or exceptional values
- deciding whether a normalized record should be counted in a report when source metadata is incomplete

This is intentional: the system is designed to support analyst review rather than replace it.
