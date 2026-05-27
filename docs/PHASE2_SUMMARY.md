# Phase 2 — Backend Models Summary

## Delivered

- Django project `backend/config/`
- Apps: `tenants`, `ingestion`, `emissions`, `review`, `audit`
- All domain models + migrations
- Django admin for all models (audit log read-only)
- Seed commands: `seed_plant_codes`, `seed_demo_users`
- [MODEL.md](./MODEL.md)

## Local setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py seed_plant_codes
.\.venv\Scripts\python manage.py seed_demo_users
```

Demo logins: `analyst` / `uploader` — password `demo1234`

## Model decisions (quick reference)

| Decision | Why |
|----------|-----|
| `User.tenant` nullable | Django superuser has no tenant |
| `RawRecord` always saved | Auditors see failed rows + errors |
| `OneToOne` raw → normalized | One canonical line per source row |
| `tenant` on normalized record | Fast review queue without joins |
| `emission_factor` on record | Snapshot — recalc won't rewrite history |
| `suspicious_reason` text field | Analysts see *why* flagged |
| `processing_summary` on DataSource | Batch stats without extra table |
| `PlantCodeLookup` global | MVP; per-tenant plants = v2 |
| `review` app has no models | Workflow = services in Phase 3 |

## Intentional additions beyond bare spec

- `suspicious_reason` — supports UI explanation
- `processing_summary` on `DataSource` — pipeline metadata
- TextChoices enums — type safety + admin labels
- Unique `(data_source, row_number)` — idempotent row identity

## Next: Phase 3 — Ingestion services

- `validation.py`, `normalization.py`, `calculation.py`
- Parsers: SAP fuel, utility electricity, travel mock API
- `pipeline.run(data_source)`
- Sample messy CSV / JSON fixtures
