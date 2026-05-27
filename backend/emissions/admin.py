from django.contrib import admin

from .models import NormalizedEmissionRecord, PlantCodeLookup


@admin.register(PlantCodeLookup)
class PlantCodeLookupAdmin(admin.ModelAdmin):
    list_display = ("code", "plant_name", "country")
    search_fields = ("code", "plant_name")


@admin.register(NormalizedEmissionRecord)
class NormalizedEmissionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "emission_scope",
        "category",
        "activity_date",
        "calculated_emissions_kg_co2e",
        "suspicious_flag",
        "approval_status",
        "locked_for_audit",
    )
    list_filter = (
        "tenant",
        "emission_scope",
        "approval_status",
        "suspicious_flag",
        "locked_for_audit",
    )
    readonly_fields = ("created_at",)
