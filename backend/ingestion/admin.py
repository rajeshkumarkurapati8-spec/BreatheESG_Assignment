from django.contrib import admin

from .models import DataSource, RawRecord


class RawRecordInline(admin.TabularInline):
    model = RawRecord
    extra = 0
    readonly_fields = ("row_number", "raw_payload", "validation_errors", "created_at")
    can_delete = False


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "source_type",
        "ingestion_method",
        "processing_status",
        "uploaded_at",
    )
    list_filter = ("source_type", "processing_status", "tenant")
    inlines = [RawRecordInline]


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "data_source", "row_number", "created_at")
    list_filter = ("data_source__source_type",)
