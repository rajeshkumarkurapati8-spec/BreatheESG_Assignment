from django.conf import settings
from django.db import models

from tenants.models import Tenant


class SourceType(models.TextChoices):
    SAP_FUEL = "sap_fuel", "SAP Fuel / Procurement"
    UTILITY_ELECTRICITY = "utility_electricity", "Utility Electricity"
    CORPORATE_TRAVEL = "corporate_travel", "Corporate Travel"


class IngestionMethod(models.TextChoices):
    CSV_UPLOAD = "csv_upload", "CSV Upload"
    API_MOCK = "api_mock", "Mocked API"


class ProcessingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class DataSource(models.Model):
    """
    One upload or API batch from an external system.
    Tracks pipeline status; links all raw rows for that ingestion run.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="data_sources",
    )
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    ingestion_method = models.CharField(max_length=16, choices=IngestionMethod.choices)
    original_filename = models.CharField(max_length=512, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_data_sources",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(
        max_length=16,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    # Optional summary after pipeline completes (row counts, errors)
    processing_summary = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["tenant", "-uploaded_at"]),
            models.Index(fields=["tenant", "processing_status"]),
        ]

    def __str__(self):
        label = self.original_filename or self.get_source_type_display()
        return f"{label} ({self.processing_status})"


class RawRecord(models.Model):
    """
    Immutable-ish capture of one source row as received.
    validation_errors populated when row fails structural checks.
    """

    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="raw_records",
    )
    raw_payload = models.JSONField(
        help_text="Original row fields exactly as parsed from CSV/API.",
    )
    row_number = models.PositiveIntegerField(
        help_text="1-based line number in source file or batch index.",
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of human-readable validation error strings.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data_source", "row_number"]
        indexes = [
            models.Index(fields=["data_source", "row_number"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["data_source", "row_number"],
                name="unique_raw_record_per_source_row",
            ),
        ]

    def __str__(self):
        return f"Row {self.row_number} — {self.data_source_id}"

    @property
    def is_valid(self) -> bool:
        return len(self.validation_errors or []) == 0
