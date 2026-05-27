# Architecture and Delivery Decisions

This document explains the practical tradeoffs and assumptions made while building the ESG emissions ingestion and analyst review platform.

It is written from the point of view of a startup engineering team shipping an MVP under time and infrastructure constraints.

---

## CSV ingestion instead of PDF parsing

CSV was chosen because it is a stable, machine-readable format that matches the available seed data and the assignment scope.

PDF parsing is a larger implementation risk: it requires OCR, field extraction heuristics, and error handling for noisy layouts.
For an MVP, it is safer to normalize structured CSV and provide a working review flow than to build unreliable PDF extraction.

## Synchronous ingestion

The ingestion pipeline is synchronous by design.

Reasons:

- the deployment target is a simple Render-style container, not a queue-based architecture
- synchronous processing keeps the behavior predictable for upload API users
- it avoids introducing Redis/Celery or background worker complexity for the MVP

This is an operational tradeoff. It means large uploads may be slower, but the implementation is simpler and easier to reason about in a demo environment.

## Static emission factors for MVP

Emission factors are stored as code constants rather than a versioned factor service.

This was acceptable because:

- the scope is proof-of-concept, not audited emissions reporting
- factor versioning is a compliance feature that adds complexity beyond the minimum viable workflow
- storing the factor on the record preserves auditability even when factors are static

The tradeoff is that the system is not yet ready for regulatory-grade factor management, but it is sufficient for validating ingestion, normalization, and review flows.

## Mocked travel APIs

Travel ingestion is implemented as a mocked JSON payload rather than a live external API integration.

That choice was made because:

- real travel APIs require credentials, OAuth flows, and variable vendor data shapes
- the MVP needs a repeatable, testable data path
- mocked payloads allow the platform to demonstrate scope 3 ingestion without external dependency risk

In a full product, the mock would be replaced with connectors to actual travel sources.

## SAP subset intentionally handled

The platform handles a narrow SAP fuel CSV subset.

It focuses on the columns needed to derive fuel type, plant code, quantity, unit, and date.

This is intentional: the goal is to prove the ingestion and normalization path.

It does not attempt to support every SAP module or every export variant. That would require broader field mapping, probably schema-driven parsing, and more robust data validation.

## Assumptions about utility billing exports

Utility ingestion assumes a relatively clean CSV export with meter ID, billing start/end, and usage values.

The implementation assumes:

- each line represents a single billing period
- the meter ID is stable and comparable across batches
- usage is reported in kWh or a directly convertible unit

These assumptions are acceptable for an MVP, but in a production implementation we would need to confirm the actual vendor file formats and support missing/partial periods explicitly.

## Assumptions about travel payloads

Travel payloads are assumed to contain a consistent trip structure with flight kilometers, hotel nights, and ground transport kilometers.

The mock API is intentionally simplified so the platform can focus on normalization and review, not on full travel itinerary parsing.

In a real implementation, the payload shape would need to be defined by the integration partner, and additional validation would be required for optional fields, currency, and route-level logic.

## Why RawRecord and NormalizedEmissionRecord are separated

The data model separates raw ingestion from normalized emissions data on purpose.

`RawRecord` captures the source row and any validation issues. It is the source-of-truth for what was submitted.

`NormalizedEmissionRecord` contains the derived, reviewable emissions line.

That separation is important because it allows the system to:

- retain the original payload for audit and debugging
- keep review logic focused on normalized emissions values
- avoid mixing parser-specific fields into the review surface

It is a deliberate architectural choice rather than a temporary workaround.

## Operational tradeoffs

### Simplifications made

- no async ingestion queue
- no factor versioning service
- no external travel API integration
- no PDF ingestion
- shared database tenancy instead of schema-per-tenant
- rule-based suspicious detection rather than machine learning

These choices reduce implementation risk and keep the codebase understandable.

### Known limitations

- the platform is not optimized for very large file uploads
- the SAP fuel parser covers only a limited export shape
- mocked travel ingestion is not production-ready
- static factors are not sufficient for audited emissions reporting
- tenant isolation is application-enforced rather than database-enforced

## Questions for PM / stakeholders

If this were a real production project, the next questions would be:

- Which exact source file formats must we support for SAP, utilities, and travel?
- Should we prioritize a user-uploaded CSV path or invest in API connectors first?
- Do we need emission factor versioning and supplier-specific factors in the initial compliant release?
- How should we handle late-arriving or corrected source data? Do we support replacement runs or line-level corrections?
- What are the required audit retention and immutability guarantees for approved records?
- Which travel providers or data partners should we integrate with, and what payload schemas do they expose?
- Is it acceptable to keep `AuditLog` tenant information implicit via the actor, or do we need tenant-scoped audit records?
- What scale of uploads and tenant concurrency should the MVP be expected to handle?

These questions reflect the realistic boundaries of the current implementation and what needs to be clarified before moving toward production.
