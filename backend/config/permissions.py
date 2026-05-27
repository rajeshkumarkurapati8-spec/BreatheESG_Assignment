from rest_framework.permissions import BasePermission


class HasTenant(BasePermission):
    """User must belong to a tenant (not a bare superuser session)."""

    message = "User is not assigned to a tenant."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.tenant_id is not None
        )


class IsAnalyst(BasePermission):
    message = "Analyst role required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_analyst)


class IsUploader(BasePermission):
    message = "Uploader role required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_uploader)


class IsAnalystOrReadOnly(BasePermission):
    """Analysts can write; others read-only within tenant."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return HasTenant().has_permission(request, view)
        return IsAnalyst().has_permission(request, view)
