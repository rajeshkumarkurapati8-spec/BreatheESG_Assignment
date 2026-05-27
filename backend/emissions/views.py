from decimal import Decimal

from django.db.models import Count, Sum
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.mixins import TenantScopedQuerysetMixin
from config.permissions import HasTenant
from emissions.models import ApprovalStatus, NormalizedEmissionRecord
from emissions.serializers import (
    NormalizedEmissionRecordListSerializer,
    NormalizedEmissionRecordSerializer,
)


class NormalizedRecordFilter(filters.FilterSet):
    approval_status = filters.CharFilter()
    suspicious_flag = filters.BooleanFilter()
    emission_scope = filters.CharFilter()
    category = filters.CharFilter()
    activity_date_after = filters.DateFilter(field_name="activity_date", lookup_expr="gte")
    activity_date_before = filters.DateFilter(field_name="activity_date", lookup_expr="lte")
    data_source = filters.NumberFilter(field_name="raw_record__data_source_id")

    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            "approval_status",
            "suspicious_flag",
            "emission_scope",
            "category",
        ]


class NormalizedEmissionRecordViewSet(TenantScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = NormalizedEmissionRecord.objects.all()
    permission_classes = [IsAuthenticated, HasTenant]
    filterset_class = NormalizedRecordFilter
    ordering_fields = [
        "activity_date",
        "created_at",
        "calculated_emissions_kg_co2e",
        "approval_status",
    ]
    ordering = ["-created_at"]
    search_fields = ["category", "source_system"]

    def get_serializer_class(self):
        if self.action == "list":
            return NormalizedEmissionRecordListSerializer
        return NormalizedEmissionRecordSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("raw_record", "reviewed_by", "raw_record__data_source")
        )


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, HasTenant]

    def get(self, request):
        tenant = request.user.tenant
        base = NormalizedEmissionRecord.objects.filter(tenant=tenant)

        total_emissions = base.aggregate(
            total=Sum("calculated_emissions_kg_co2e")
        )["total"] or Decimal("0")

        pending_reviews = base.filter(approval_status=ApprovalStatus.PENDING).count()
        suspicious_count = base.filter(suspicious_flag=True).count()

        by_scope = (
            base.values("emission_scope")
            .annotate(
                total_kg_co2e=Sum("calculated_emissions_kg_co2e"),
                record_count=Count("id"),
            )
            .order_by("emission_scope")
        )

        return Response(
            {
                "total_emissions_kg_co2e": str(total_emissions.quantize(Decimal("0.01"))),
                "pending_reviews": pending_reviews,
                "suspicious_records": suspicious_count,
                "emissions_by_scope": list(by_scope),
            }
        )
