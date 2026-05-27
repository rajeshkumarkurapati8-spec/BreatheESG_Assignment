from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.mixins import TenantScopedQuerysetMixin
from config.permissions import HasTenant, IsUploader
from ingestion.models import DataSource, RawRecord
from ingestion.serializers import (
    DataSourceSerializer,
    RawRecordSerializer,
    UploadSerializer,
)
from ingestion.services.pipeline import create_data_source_and_ingest


class DataSourceFilter(filters.FilterSet):
    source_type = filters.CharFilter()
    processing_status = filters.CharFilter()

    class Meta:
        model = DataSource
        fields = ["source_type", "processing_status"]


class DataSourceViewSet(TenantScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = DataSource.objects.all()
    permission_classes = [IsAuthenticated, HasTenant]
    serializer_class = DataSourceSerializer
    filterset_class = DataSourceFilter
    ordering_fields = ["uploaded_at", "id"]
    ordering = ["-uploaded_at"]


class RawRecordFilter(filters.FilterSet):
    data_source = filters.NumberFilter()

    class Meta:
        model = RawRecord
        fields = ["data_source"]


class RawRecordViewSet(TenantScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = RawRecord.objects.all()
    permission_classes = [IsAuthenticated, HasTenant]
    serializer_class = RawRecordSerializer
    tenant_lookup = "data_source__tenant"
    filterset_class = RawRecordFilter
    ordering_fields = ["row_number", "created_at"]
    ordering = ["data_source", "row_number"]


class UploadView(APIView):
    """
    POST multipart: source_type + file (CSV sources)
    POST JSON/multipart: source_type + api_payload (corporate travel)
    """

    permission_classes = [IsAuthenticated, HasTenant, IsUploader]

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_type = serializer.validated_data["source_type"]
        file = serializer.validated_data.get("file")
        api_payload = serializer.validated_data.get("api_payload")

        file_content = None
        filename = ""
        if file:
            file_content = file.read()
            filename = file.name

        data_source = create_data_source_and_ingest(
            tenant=request.user.tenant,
            source_type=source_type,
            ingestion_method=serializer.get_ingestion_method(),
            uploaded_by=request.user,
            original_filename=filename or f"{source_type}.json",
            file_content=file_content,
            api_payload=api_payload,
        )

        return Response(
            DataSourceSerializer(data_source).data,
            status=status.HTTP_201_CREATED,
        )
