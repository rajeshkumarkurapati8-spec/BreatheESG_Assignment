# Architecture Tradeoffs

This document explains why certain production-grade features were intentionally omitted from the MVP.

## 1. Asynchronous ingestion processing

### Why excluded
Synchronous ingestion keeps the pipeline simple and deployable on a single Render container without Redis/Celery or worker infrastructure.

### Operational complexity
Asynchronous processing would require queue management, retry logic, visibility into job status, and separate worker deployment.
It would also make upload behavior less predictable for users because the API response could no longer represent final ingestion results.

### Future production considerations
If the product targets larger files or higher concurrency, moving ingestion to an async queue is a reasonable next step.
That future design should include durable task state, failure notifications, and a way to reconcile partial batches.

## 2. Real ERP / utility integrations

### Why excluded
The MVP focuses on proving the ingestion and review workflow using structured inputs.
Real ERP and utility connectors introduce vendor-specific auth, schema variation, and operational dependencies that exceed the minimal deliverable.

### Operational complexity
Real integrations require credential management, API rate limiting, batch pagination, schema drift handling, and partner onboarding processes.
They also add a dependency on external availability and make testing harder.

### Future production considerations
A production version should support concrete source contracts, connector retry policies, and a way to normalize multiple export variants per source.
It should also treat external integration failures separately from internal validation failures.

## 3. Emission factor versioning

### Why excluded
Static factors are sufficient to validate the ingestion/normalization/review pipeline in an MVP context.
Supporting versioned factors would add another domain to the model and require historical applicability rules.

### Operational complexity
Versioning factors means tracking effective dates, source provenance, and reapplying or preserving historical calculations.
It also requires a governance process for factor updates and rules for whether old records are recalculated or preserved.

### Future production considerations
A production system should separate factor lookup from record storage and capture both the factor identifier and the value used.
It should also support factor lifecycle controls and audit trails for factor changes.
