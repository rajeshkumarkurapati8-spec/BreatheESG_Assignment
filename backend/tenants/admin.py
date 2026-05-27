from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("company_name", "industry", "created_at")
    search_fields = ("company_name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "tenant", "is_analyst", "is_uploader", "is_staff")
    list_filter = ("tenant", "is_analyst", "is_uploader", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("ESG platform", {"fields": ("tenant", "is_analyst", "is_uploader")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("ESG platform", {"fields": ("tenant", "is_analyst", "is_uploader")}),
    )
