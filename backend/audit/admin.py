from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "entity_type",
        "entity_id",
        "action",
        "performed_by",
        "performed_at",
    )
    list_filter = ("entity_type", "action")
    readonly_fields = (
        "entity_type",
        "entity_id",
        "action",
        "old_values",
        "new_values",
        "performed_by",
        "performed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
