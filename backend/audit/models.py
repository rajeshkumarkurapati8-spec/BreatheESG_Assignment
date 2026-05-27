from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    CREATED = "created", "Created"
    UPDATED = "updated", "Updated"
    UPLOAD_STARTED = "upload_started", "Upload Started"
    UPLOAD_COMPLETED = "upload_completed", "Upload Completed"
    UPLOAD_FAILED = "upload_failed", "Upload Failed"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    LOCKED = "locked", "Locked for Audit"


class EntityType(models.TextChoices):
    DATA_SOURCE = "data_source", "Data Source"
    RAW_RECORD = "raw_record", "Raw Record"
    NORMALIZED_RECORD = "normalized_emission_record", "Normalized Emission Record"
    TENANT = "tenant", "Tenant"


class AuditLog(models.Model):
    """
    Append-only compliance log.
    entity_id stored as string to avoid GenericForeignKey query complexity.
    """

    entity_type = models.CharField(max_length=64, choices=EntityType.choices)
    entity_id = models.CharField(max_length=64)
    action = models.CharField(max_length=32, choices=AuditAction.choices)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-performed_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id", "-performed_at"]),
            models.Index(fields=["-performed_at"]),
            models.Index(fields=["performed_by", "-performed_at"]),
        ]

    def __str__(self):
        return f"{self.action} on {self.entity_type}:{self.entity_id}"
