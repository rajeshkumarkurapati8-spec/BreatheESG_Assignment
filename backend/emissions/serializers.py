from rest_framework import serializers

from emissions.models import NormalizedEmissionRecord
from ingestion.serializers import RawRecordSerializer


class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username", read_only=True, default=None
    )
    emission_scope_display = serializers.CharField(
        source="get_emission_scope_display", read_only=True
    )
    approval_status_display = serializers.CharField(
        source="get_approval_status_display", read_only=True
    )
    raw_record_detail = RawRecordSerializer(source="raw_record", read_only=True)

    class Meta:
        model = NormalizedEmissionRecord
        fields = (
            "id",
            "tenant",
            "raw_record",
            "raw_record_detail",
            "emission_scope",
            "emission_scope_display",
            "category",
            "activity_date",
            "normalized_unit",
            "normalized_quantity",
            "emission_factor",
            "calculated_emissions_kg_co2e",
            "source_system",
            "suspicious_flag",
            "suspicious_reason",
            "approval_status",
            "approval_status_display",
            "locked_for_audit",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "created_at",
        )
        read_only_fields = fields


class NormalizedEmissionRecordListSerializer(serializers.ModelSerializer):
    """Lighter serializer for tables / review queue."""

    class Meta:
        model = NormalizedEmissionRecord
        fields = (
            "id",
            "emission_scope",
            "category",
            "activity_date",
            "normalized_unit",
            "normalized_quantity",
            "calculated_emissions_kg_co2e",
            "suspicious_flag",
            "approval_status",
            "locked_for_audit",
            "source_system",
            "created_at",
        )
        read_only_fields = fields
