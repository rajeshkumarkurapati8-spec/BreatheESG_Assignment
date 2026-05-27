from django.conf import settings
from django.db import models

from ingestion.models import RawRecord
from tenants.models import Tenant


class EmissionScope(models.TextChoices):
    SCOPE_1 = "scope1", "Scope 1"
    SCOPE_2 = "scope2", "Scope 2"
    SCOPE_3 = "scope3", "Scope 3"


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class PlantCodeLookup(models.Model):
    """Reference data for SAP Werk / plant codes → human-readable facility."""

    code = models.CharField(max_length=32, primary_key=True)
    plant_name = models.CharField(max_length=255)
    country = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 country code")

    class Meta:
        verbose_name = "Plant code lookup"
        verbose_name_plural = "Plant code lookups"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.plant_name}"


class NormalizedEmissionRecord(models.Model):
    """
    Canonical emissions line after normalization and calculation.
    Analyst workflow mutates approval_status and locked_for_audit via review services.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="emission_records",
    )
    raw_record = models.OneToOneField(
        RawRecord,
        on_delete=models.CASCADE,
        related_name="normalized_record",
        null=True,
        blank=True,
        help_text="Source row; null only for edge cases / manual entry later.",
    )
    emission_scope = models.CharField(max_length=8, choices=EmissionScope.choices)
    category = models.CharField(
        max_length=128,
        help_text="e.g. stationary_combustion, purchased_electricity, business_travel_air",
    )
    activity_date = models.DateField(
        help_text="Date activity occurred or billing period representative date.",
    )
    normalized_unit = models.CharField(
        max_length=32,
        help_text="Standard unit after conversion, e.g. liter, kwh, km.",
    )
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=6)
    emission_factor = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        help_text="kg CO2e per normalized unit used at calculation time.",
    )
    calculated_emissions_kg_co2e = models.DecimalField(max_digits=18, decimal_places=6)
    source_system = models.CharField(
        max_length=64,
        help_text="Originating system label, e.g. sap_mm, utility_portal, concur_mock.",
    )
    suspicious_flag = models.BooleanField(
        default=False,
        help_text="Set by rules e.g. utility usage spike > 2x rolling average.",
    )
    suspicious_reason = models.CharField(max_length=512, blank=True)
    approval_status = models.CharField(
        max_length=16,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    locked_for_audit = models.BooleanField(
        default=False,
        help_text="When True, record cannot be edited — audit-published state.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_emission_records",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "approval_status", "suspicious_flag"]),
            models.Index(fields=["tenant", "emission_scope"]),
            models.Index(fields=["tenant", "-activity_date"]),
            models.Index(fields=["tenant", "locked_for_audit"]),
        ]

    def __str__(self):
        return (
            f"{self.get_emission_scope_display()} — {self.category} "
            f"({self.calculated_emissions_kg_co2e} kg CO2e)"
        )

    @property
    def is_editable(self) -> bool:
        return not self.locked_for_audit
