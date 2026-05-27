import datetime

import pytest
from django.urls import reverse
from rest_framework import status

from audit.models import AuditAction, AuditLog, EntityType
from emissions.models import ApprovalStatus, NormalizedEmissionRecord


def _create_pending_record(tenant):
    return NormalizedEmissionRecord.objects.create(
        tenant=tenant,
        emission_scope="scope1",
        category="stationary_combustion",
        activity_date=datetime.date.today(),
        normalized_unit="liter",
        normalized_quantity=100,
        emission_factor=2.5,
        calculated_emissions_kg_co2e=250,
        source_system="sap_mm",
    )


@pytest.mark.django_db
class TestReviewWorkflow:
    def test_approve_record_locks_record(self, analyst_client, analyst_user):
        record = _create_pending_record(analyst_user.tenant)

        response = analyst_client.post(
            reverse("review-approve"),
            {"id": record.pk},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["approval_status"] == ApprovalStatus.APPROVED
        assert response.data["locked_for_audit"] is True

        record.refresh_from_db()
        assert record.approval_status == ApprovalStatus.APPROVED
        assert record.locked_for_audit is True
        assert record.reviewed_by_id == analyst_user.pk

    def test_reject_record_keeps_unlocked(self, analyst_client, analyst_user):
        record = _create_pending_record(analyst_user.tenant)

        response = analyst_client.post(
            reverse("review-reject"),
            {"id": record.pk, "reason": "Data quality issue."},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["approval_status"] == ApprovalStatus.REJECTED
        assert response.data["locked_for_audit"] is False

        record.refresh_from_db()
        assert record.approval_status == ApprovalStatus.REJECTED
        assert record.locked_for_audit is False
        assert "Data quality issue." in record.suspicious_reason

    def test_approve_creates_audit_log(self, analyst_client, analyst_user):
        record = _create_pending_record(analyst_user.tenant)

        response = analyst_client.post(
            reverse("review-approve"),
            {"id": record.pk},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        logs = AuditLog.objects.filter(
            entity_type=EntityType.NORMALIZED_RECORD,
            entity_id=str(record.pk),
        )
        assert logs.filter(action=AuditAction.APPROVED).exists()
        assert logs.filter(action=AuditAction.LOCKED).exists()

    def test_reject_creates_audit_log(self, analyst_client, analyst_user):
        record = _create_pending_record(analyst_user.tenant)

        response = analyst_client.post(
            reverse("review-reject"),
            {"id": record.pk, "reason": "Vendor mismatch."},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        logs = AuditLog.objects.filter(
            entity_type=EntityType.NORMALIZED_RECORD,
            entity_id=str(record.pk),
            action=AuditAction.REJECTED,
        )
        assert logs.count() == 1

    def test_tenant_isolation_prevents_cross_tenant_review(
        self, analyst_client, analyst_user
    ):
        from tenants.models import Tenant

        other_tenant = Tenant.objects.create(company_name="OtherCo", industry="Energy")
        record = _create_pending_record(other_tenant)

        approve = analyst_client.post(
            reverse("review-approve"),
            {"id": record.pk},
            format="json",
        )
        reject = analyst_client.post(
            reverse("review-reject"),
            {"id": record.pk, "reason": "Wrong tenant."},
            format="json",
        )

        assert approve.status_code == status.HTTP_404_NOT_FOUND
        assert reject.status_code == status.HTTP_404_NOT_FOUND
