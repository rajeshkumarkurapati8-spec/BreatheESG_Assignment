import json
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from emissions.models import ApprovalStatus, NormalizedEmissionRecord
from tenants.models import User

SEED_DIR = Path(__file__).resolve().parents[1] / "seed_data"


@pytest.fixture
def api_client():
    client = APIClient()
    client.enforce_csrf_checks = False
    return client


@pytest.mark.django_db
def test_auth_token_and_me(api_client, demo_users):
    response = api_client.post(
        "/api/auth/token/",
        {"username": "analyst", "password": "demo1234"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    me = api_client.get("/api/auth/me/")
    assert me.status_code == status.HTTP_200_OK
    assert me.data["username"] == "analyst"
    assert me.data["is_analyst"] is True


@pytest.mark.django_db
def test_dashboard_stats(analyst_client, demo_users):
    response = analyst_client.get("/api/dashboard/")
    assert response.status_code == status.HTTP_200_OK
    assert "total_emissions_kg_co2e" in response.data
    assert "pending_reviews" in response.data


@pytest.mark.django_db
def test_upload_sap_csv(uploader_client, demo_users):
    content = (SEED_DIR / "sap_fuel_messy.csv").read_bytes()
    upload = SimpleUploadedFile("sap_fuel_messy.csv", content, content_type="text/csv")
    response = uploader_client.post(
        "/api/uploads/",
        {"source_type": "sap_fuel", "file": upload},
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["processing_status"] == "completed"
    assert response.data["processing_summary"]["raw_created"] >= 1


@pytest.mark.django_db
def test_upload_travel_json(uploader_client, demo_users):
    payload = json.loads((SEED_DIR / "travel_api_batch.json").read_text())
    response = uploader_client.post(
        "/api/uploads/",
        {"source_type": "corporate_travel", "api_payload": payload},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_review_approve_reject(analyst_client, uploader_client, analyst_user, demo_users):
    record = NormalizedEmissionRecord.objects.filter(
        tenant=analyst_user.tenant,
        approval_status=ApprovalStatus.PENDING,
    ).first()
    if not record:
        content = (SEED_DIR / "sap_fuel_messy.csv").read_bytes()
        upload = SimpleUploadedFile("test.csv", content, content_type="text/csv")
        uploader_client.post(
            "/api/uploads/",
            {"source_type": "sap_fuel", "file": upload},
            format="multipart",
        )
        record = NormalizedEmissionRecord.objects.filter(
            tenant=analyst_user.tenant,
            approval_status=ApprovalStatus.PENDING,
        ).first()

    assert record is not None

    approve = analyst_client.post(
        "/api/review/approve/",
        {"id": record.pk},
        format="json",
    )
    assert approve.status_code == status.HTTP_200_OK
    assert approve.data["approval_status"] == "approved"
    assert approve.data["locked_for_audit"] is True

    # Second approve should fail
    again = analyst_client.post(
        "/api/review/approve/",
        {"id": record.pk},
        format="json",
    )
    assert again.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_uploader_cannot_approve(uploader_client, demo_users):
    record = NormalizedEmissionRecord.objects.filter(
        approval_status=ApprovalStatus.PENDING
    ).first()
    if not record:
        pytest.skip("No pending records")

    response = uploader_client.post(
        "/api/review/approve/",
        {"id": record.pk},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_tenant_scoped_list(analyst_client, analyst_user, demo_users):
    response = analyst_client.get("/api/normalized-records/")
    assert response.status_code == status.HTTP_200_OK

    tenant_id = analyst_user.tenant_id
    ids = [r["id"] for r in response.data["results"]]
    if ids:
        assert (
            NormalizedEmissionRecord.objects.filter(id__in=ids)
            .exclude(tenant_id=tenant_id)
            .count()
            == 0
        )


@pytest.mark.django_db
def test_audit_logs_list(analyst_client, demo_users):
    response = analyst_client.get("/api/audit-logs/")
    assert response.status_code == status.HTTP_200_OK
