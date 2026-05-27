# Phase 3 — Ingestion Services Summary

## Delivered

### Service layers

| Module | Location | Role |
|--------|----------|------|
| ValidationEngine | `ingestion/services/validation.py` | Dates, units, quantities, airports, billing periods |
| NormalizationEngine | `ingestion/services/normalization.py` | Liters, plant lookup, billing midpoint |
| Emission factors | `emissions/services/factors.py` | Static kg CO2e factors |
| Calculation | `emissions/services/calculation.py` | `quantity × factor` |
| Suspicious rules | `emissions/services/suspicious.py` | Utility spike > 2× rolling average |
| Audit logger | `audit/services/logger.py` | Upload started/completed/failed |
| Pipeline | `ingestion/services/pipeline.py` | Orchestrates parse → raw → normalized |

### Parsers

| Parser | Source | Output |
|--------|--------|--------|
| `SapFuelParser` | CSV (German SAP columns) | Scope 1, liters, plant resolution |
| `UtilityElectricityParser` | CSV portal export | Scope 2, kWh, spike detection |
| `TravelApiParser` | Mock JSON (`trips[]`) | Scope 3, flight/hotel/taxi combined |

### Sample data

- `backend/seed_data/sap_fuel_messy.csv`
- `backend/seed_data/utility_electricity.csv`
- `backend/seed_data/travel_api_batch.json`

### Commands

```bash
python manage.py ingest_sample --source sap_fuel
python manage.py ingest_sample --all
```

### Tests

```bash
pytest ingestion/tests
```

19 tests — validation, normalization, parsers, pipeline, airports.

---

## Architectural choices

1. **Unmapped SAP plant → suspicious, not hard fail** — Real analysts fix mapping; bad rows still normalize for review.
2. **Utility spike uses DB history** — Rolling average from prior `NormalizedEmissionRecord` rows with same `meter_id` in `raw_payload`.
3. **Travel: combined emissions, one line** — Flight + hotel + taxi summed; `calculation_notes` explains breakdown.
4. **Synchronous pipeline** — Same request/transaction; `DataSource.processing_summary` reports counts.
5. **Explicit audit on upload lifecycle** — Per-record audit deferred to review phase (Phase 4).

---

## Simplifications

| Area | MVP behavior |
|------|----------------|
| Emission factors | Static constants, not DEFRA/eGRID versioned tables |
| Airport distances | Haversine on ~12 IATA codes |
| m³ fuel | Rough 1000 L conversion |
| Spike detection | 6-period rolling avg, same tenant only |
| Re-ingestion | No dedup; new `DataSource` per upload |

---

## Example ingest output

```
sap_fuel: 8 rows → 4 normalized, 4 validation failures, 1 suspicious
utility: 10 rows → 9 normalized, 1 spike flagged
travel: 5 rows → 4 normalized, 1 invalid airport (ZZZ)
```

---

## Next: Phase 4 — REST APIs

- JWT auth endpoints
- Upload API wrapping `run_ingestion`
- ViewSets + review approve/reject
- Tenant-scoped permissions
