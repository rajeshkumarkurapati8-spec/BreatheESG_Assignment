from rest_framework import serializers

from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    performed_by_username = serializers.CharField(
        source="performed_by.username", read_only=True, default=None
    )

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "entity_type",
            "entity_id",
            "action",
            "old_values",
            "new_values",
            "performed_by",
            "performed_by_username",
            "performed_at",
        )
        read_only_fields = fields
