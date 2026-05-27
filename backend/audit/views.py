from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from config.permissions import HasTenant


class AuditLogFilter(filters.FilterSet):
    entity_type = filters.CharFilter()
    entity_id = filters.CharFilter()
    action = filters.CharFilter()

    class Meta:
        model = AuditLog
        fields = ["entity_type", "entity_id", "action"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated, HasTenant]
    serializer_class = AuditLogSerializer
    filterset_class = AuditLogFilter
    ordering = ["-performed_at"]

    def get_queryset(self):
        tenant = self.request.user.tenant
        tenant_user_ids = tenant.users.values_list("id", flat=True)
        source_ids = [str(pk) for pk in tenant.data_sources.values_list("id", flat=True)]
        record_ids = [str(pk) for pk in tenant.emission_records.values_list("id", flat=True)]
        return AuditLog.objects.filter(
            Q(performed_by_id__in=tenant_user_ids)
            | Q(entity_type="data_source", entity_id__in=source_ids)
            | Q(entity_type="normalized_emission_record", entity_id__in=record_ids)
        ).select_related("performed_by")
