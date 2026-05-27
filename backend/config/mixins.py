class TenantScopedQuerysetMixin:
    """Filter querysets to the authenticated user's tenant."""

    tenant_lookup = "tenant"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated or not user.tenant_id:
            return qs.none()
        return qs.filter(**{self.tenant_lookup: user.tenant})
