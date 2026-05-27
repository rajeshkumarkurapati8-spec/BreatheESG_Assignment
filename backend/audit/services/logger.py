from typing import Any

from audit.models import AuditAction, AuditLog, EntityType


def log_action(
    *,
    entity_type: str,
    entity_id: int | str,
    action: str,
    performed_by=None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
) -> AuditLog:
    """Append a single audit log entry."""
    return AuditLog.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        old_values=old_values or {},
        new_values=new_values or {},
        performed_by=performed_by,
    )


def log_upload_started(data_source, performed_by) -> AuditLog:
    return log_action(
        entity_type=EntityType.DATA_SOURCE,
        entity_id=data_source.pk,
        action=AuditAction.UPLOAD_STARTED,
        performed_by=performed_by,
        new_values={
            "source_type": data_source.source_type,
            "ingestion_method": data_source.ingestion_method,
            "original_filename": data_source.original_filename,
        },
    )


def log_upload_completed(data_source, performed_by, summary: dict) -> AuditLog:
    return log_action(
        entity_type=EntityType.DATA_SOURCE,
        entity_id=data_source.pk,
        action=AuditAction.UPLOAD_COMPLETED,
        performed_by=performed_by,
        new_values=summary,
    )


def log_upload_failed(data_source, performed_by, error: str) -> AuditLog:
    return log_action(
        entity_type=EntityType.DATA_SOURCE,
        entity_id=data_source.pk,
        action=AuditAction.UPLOAD_FAILED,
        performed_by=performed_by,
        new_values={"error": error},
    )
