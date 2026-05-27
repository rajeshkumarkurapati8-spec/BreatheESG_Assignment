from rest_framework import serializers

from ingestion.models import DataSource, IngestionMethod, RawRecord, SourceType


class DataSourceSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = DataSource
        fields = (
            "id",
            "tenant",
            "source_type",
            "ingestion_method",
            "original_filename",
            "uploaded_by",
            "uploaded_by_username",
            "uploaded_at",
            "processing_status",
            "processing_summary",
        )
        read_only_fields = (
            "id",
            "tenant",
            "uploaded_by",
            "uploaded_at",
            "processing_status",
            "processing_summary",
        )


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = (
            "id",
            "data_source",
            "raw_payload",
            "row_number",
            "validation_errors",
            "created_at",
        )
        read_only_fields = fields


class UploadSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(choices=SourceType.choices)
    file = serializers.FileField(required=False, allow_empty_file=False)
    api_payload = serializers.JSONField(required=False)

    def validate(self, attrs):
        source_type = attrs["source_type"]
        file = attrs.get("file")
        api_payload = attrs.get("api_payload")

        if source_type == SourceType.CORPORATE_TRAVEL:
            if not api_payload:
                raise serializers.ValidationError(
                    {"api_payload": "Travel ingestion requires JSON payload with trips."}
                )
        else:
            if not file:
                raise serializers.ValidationError(
                    {"file": "CSV file required for this source type."}
                )
            if not file.name.lower().endswith(".csv"):
                raise serializers.ValidationError({"file": "Only CSV files are supported."})

        return attrs

    def get_ingestion_method(self):
        source_type = self.validated_data["source_type"]
        if source_type == SourceType.CORPORATE_TRAVEL:
            return IngestionMethod.API_MOCK
        return IngestionMethod.CSV_UPLOAD
