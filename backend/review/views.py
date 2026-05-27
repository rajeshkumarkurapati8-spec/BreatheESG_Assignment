from django.core.exceptions import PermissionDenied, ValidationError
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.mixins import TenantScopedQuerysetMixin
from config.permissions import HasTenant, IsAnalyst
from emissions.models import ApprovalStatus, NormalizedEmissionRecord
from emissions.serializers import NormalizedEmissionRecordSerializer
from review.services.workflow import approve_record, reject_record


class PendingReviewFilter(filters.FilterSet):
    suspicious = filters.BooleanFilter(field_name="suspicious_flag")
    emission_scope = filters.CharFilter()

    class Meta:
        model = NormalizedEmissionRecord
        fields = ["suspicious_flag", "emission_scope"]


class PendingReviewViewSet(TenantScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """GET /api/review/pending/ — records awaiting analyst review."""

    queryset = NormalizedEmissionRecord.objects.all()
    permission_classes = [IsAuthenticated, HasTenant]
    serializer_class = NormalizedEmissionRecordSerializer
    filterset_class = PendingReviewFilter
    ordering_fields = ["activity_date", "created_at", "calculated_emissions_kg_co2e"]
    ordering = ["-suspicious_flag", "-created_at"]
    search_fields = ["category", "source_system"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(approval_status=ApprovalStatus.PENDING)
            .select_related("raw_record", "reviewed_by", "raw_record__data_source")
        )


class ApproveRecordView(APIView):
    permission_classes = [IsAuthenticated, HasTenant, IsAnalyst]

    def post(self, request):
        record_id = request.data.get("id") or request.data.get("record_id")
        if not record_id:
            return Response(
                {"detail": "Field 'id' or 'record_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = NormalizedEmissionRecord.objects.get(
                pk=record_id, tenant=request.user.tenant
            )
        except NormalizedEmissionRecord.DoesNotExist:
            return Response({"detail": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            record = approve_record(record, user=request.user)
        except (ValidationError, PermissionDenied) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(NormalizedEmissionRecordSerializer(record).data)


class RejectRecordView(APIView):
    permission_classes = [IsAuthenticated, HasTenant, IsAnalyst]

    def post(self, request):
        record_id = request.data.get("id") or request.data.get("record_id")
        reason = request.data.get("reason", "")

        if not record_id:
            return Response(
                {"detail": "Field 'id' or 'record_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = NormalizedEmissionRecord.objects.get(
                pk=record_id, tenant=request.user.tenant
            )
        except NormalizedEmissionRecord.DoesNotExist:
            return Response({"detail": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            record = reject_record(record, user=request.user, reason=reason)
        except (ValidationError, PermissionDenied) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(NormalizedEmissionRecordSerializer(record).data)
