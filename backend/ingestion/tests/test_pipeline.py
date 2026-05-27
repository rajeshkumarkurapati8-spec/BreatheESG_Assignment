import json
from pathlib import Path

import pytest

from audit.models import AuditLog
from emissions.models import NormalizedEmissionRecord
from ingestion.models import DataSource, RawRecord, SourceType, IngestionMethod
from ingestion.services.pipeline import run_ingestion
from tenants.models import Tenant, User

SEED_DIR = Path(__file__).resolve().parents[2] / "seed_data"


@pytest.fixture
def demo_tenant(db):
    tenant, _ = Tenant.objects.get_or_create(
        company_name="Pipeline Test GmbH",
        defaults={"industry": "Test"},
    )
    user, _ = User.objects.get_or_create(
        username="pipeline_uploader",
        defaults={"tenant": tenant, "is_uploader": True},
    )
    user.tenant = tenant
    user.save()
    return tenant, user


@pytest.mark.django_db
def test_ingest_sap_csv(demo_tenant):
    tenant, user = demo_tenant
    content = (SEED_DIR / "sap_fuel_messy.csv").read_bytes()

    data_source = DataSource.objects.create(
        tenant=tenant,
        source_type=SourceType.SAP_FUEL,
        ingestion_method=IngestionMethod.CSV_UPLOAD,
        original_filename="sap_fuel_messy.csv",
        uploaded_by=user,
    )
    summary = run_ingestion(data_source, file_content=content, performed_by=user)

    assert summary["rows_total"] == 8
    assert summary["raw_created"] == 8
    assert summary["validation_failed"] >= 2
    assert RawRecord.objects.filter(data_source=data_source).count() == 8
    assert NormalizedEmissionRecord.objects.filter(tenant=tenant).count() >= 3
    assert AuditLog.objects.filter(entity_id=str(data_source.pk)).exists()
    data_source.refresh_from_db()
    assert data_source.processing_status == "completed"


@pytest.mark.django_db
def test_ingest_utility_detects_spike(demo_tenant):
    tenant, user = demo_tenant
    content = (SEED_DIR / "utility_electricity.csv").read_bytes()

    data_source = DataSource.objects.create(
        tenant=tenant,
        source_type=SourceType.UTILITY_ELECTRICITY,
        ingestion_method=IngestionMethod.CSV_UPLOAD,
        original_filename="utility_electricity.csv",
        uploaded_by=user,
    )
    summary = run_ingestion(data_source, file_content=content, performed_by=user)

    assert summary["suspicious_count"] >= 1
    suspicious = NormalizedEmissionRecord.objects.filter(
        tenant=tenant, suspicious_flag=True
    )
    assert suspicious.exists()


@pytest.mark.django_db
def test_ingest_travel_api(demo_tenant):
    tenant, user = demo_tenant
    payload = json.loads((SEED_DIR / "travel_api_batch.json").read_text())

    data_source = DataSource.objects.create(
        tenant=tenant,
        source_type=SourceType.CORPORATE_TRAVEL,
        ingestion_method=IngestionMethod.API_MOCK,
        original_filename="travel_api_batch.json",
        uploaded_by=user,
    )
    summary = run_ingestion(data_source, api_payload=payload, performed_by=user)

    assert summary["normalized_created"] >= 3
    assert summary["validation_failed"] >= 1
