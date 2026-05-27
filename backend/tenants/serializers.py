from rest_framework import serializers

from tenants.models import Tenant, User


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("id", "company_name", "industry", "created_at")
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "tenant",
            "is_analyst",
            "is_uploader",
        )
        read_only_fields = fields
