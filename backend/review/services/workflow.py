"""
Analyst review workflow — approve, reject, audit lock.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from audit.models import AuditAction, EntityType
from audit.services.logger import log_action
from emissions.models import ApprovalStatus, NormalizedEmissionRecord


class RecordLockedError(ValidationError):
    pass


class RecordNotPendingError(ValidationError):
    pass


def _ensure_analyst(user) -> None:
    if not user.is_analyst:
        raise PermissionDenied("Analyst role required to review records.")


def _snapshot(record: NormalizedEmissionRecord) -> dict:
    return {
        "approval_status": record.approval_status,
        "locked_for_audit": record.locked_for_audit,
        "suspicious_flag": record.suspicious_flag,
        "reviewed_by_id": record.reviewed_by_id,
    }


def approve_record(record: NormalizedEmissionRecord, *, user) -> NormalizedEmissionRecord:
    _ensure_analyst(user)

    if record.tenant_id != user.tenant_id:
        raise PermissionDenied("Record belongs to another tenant.")

    if record.locked_for_audit:
        raise RecordLockedError("Record is locked for audit and cannot be modified.")

    if record.approval_status != ApprovalStatus.PENDING:
        raise RecordNotPendingError(
            f"Only pending records can be approved (current: {record.approval_status})."
        )

    old_values = _snapshot(record)
    now = timezone.now()

    record.approval_status = ApprovalStatus.APPROVED
    record.locked_for_audit = True
    record.reviewed_by = user
    record.reviewed_at = now
    record.save(
        update_fields=[
            "approval_status",
            "locked_for_audit",
            "reviewed_by",
            "reviewed_at",
        ]
    )

    log_action(
        entity_type=EntityType.NORMALIZED_RECORD,
        entity_id=record.pk,
        action=AuditAction.APPROVED,
        performed_by=user,
        old_values=old_values,
        new_values=_snapshot(record),
    )
    log_action(
        entity_type=EntityType.NORMALIZED_RECORD,
        entity_id=record.pk,
        action=AuditAction.LOCKED,
        performed_by=user,
        old_values={"locked_for_audit": False},
        new_values={"locked_for_audit": True},
    )
    return record


def reject_record(
    record: NormalizedEmissionRecord, *, user, reason: str = ""
) -> NormalizedEmissionRecord:
    _ensure_analyst(user)

    if record.tenant_id != user.tenant_id:
        raise PermissionDenied("Record belongs to another tenant.")

    if record.locked_for_audit:
        raise RecordLockedError("Record is locked for audit and cannot be modified.")

    if record.approval_status != ApprovalStatus.PENDING:
        raise RecordNotPendingError(
            f"Only pending records can be rejected (current: {record.approval_status})."
        )

    old_values = _snapshot(record)
    now = timezone.now()

    record.approval_status = ApprovalStatus.REJECTED
    record.locked_for_audit = False
    record.reviewed_by = user
    record.reviewed_at = now
    if reason:
        record.suspicious_reason = (
            f"{record.suspicious_reason} | Rejection: {reason}".strip(" |")
        )
    record.save(
        update_fields=[
            "approval_status",
            "locked_for_audit",
            "reviewed_by",
            "reviewed_at",
            "suspicious_reason",
        ]
    )

    new_values = _snapshot(record)
    if reason:
        new_values["rejection_reason"] = reason

    log_action(
        entity_type=EntityType.NORMALIZED_RECORD,
        entity_id=record.pk,
        action=AuditAction.REJECTED,
        performed_by=user,
        old_values=old_values,
        new_values=new_values,
    )
    return record
