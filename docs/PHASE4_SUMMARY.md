# Phase 4 — REST API Summary

## Endpoints

| Method | Path | Auth | Role |
|--------|------|------|------|
| POST | `/api/auth/token/` | Public | JWT login |
| POST | `/api/auth/token/refresh/` | Public | Refresh token |
| GET | `/api/auth/me/` | JWT | Current user + tenant |
| GET | `/api/tenants/` | JWT | Own tenant only |
| GET | `/api/sources/` | JWT | Data sources (tenant-scoped) |
| POST | `/api/uploads/` | JWT | **Uploader** — CSV or travel JSON |
| GET | `/api/raw-records/` | JWT | Raw rows (`?data_source=`) |
| GET | `/api/normalized-records/` | JWT | Emission lines (filter/search) |
| GET | `/api/review/pending/` | JWT | Pending approval queue |
| POST | `/api/review/approve/` | JWT | **Analyst** — locks record |
| POST | `/api/review/reject/` | JWT | **Analyst** |
| GET | `/api/audit-logs/` | JWT | Tenant audit trail |
| GET | `/api/dashboard/` | JWT | KPI aggregates |

## Example requests

**Login:**
```http
POST /api/auth/token/
{"username": "analyst", "password": "demo1234"}
```

**Upload SAP CSV:**
```http
POST /api/uploads/
Authorization: Bearer <token>
Content-Type: multipart/form-data

source_type=sap_fuel
file=<csv>
```

**Approve:**
```http
POST /api/review/approve/
{"id": 42}
```

## Architecture

- **TenantScopedQuerysetMixin** — all list/detail queries filtered by `request.user.tenant`
- **review.services.workflow** — approve/reject + audit logs (not raw ORM in views)
- **UploadView** — wraps `create_data_source_and_ingest()` from Phase 3

## Filters (examples)

- `/api/normalized-records/?suspicious_flag=true&approval_status=pending`
- `/api/review/pending/?suspicious=true`
- `/api/audit-logs/?entity_type=normalized_emission_record&entity_id=42`

## Next: Phase 5 — React frontend
