from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    """Company / organization boundary for row-level multi-tenancy."""

    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name


class User(AbstractUser):
    """
    Platform user scoped to a single tenant for MVP.
    Superusers may have null tenant for Django admin access.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )
    is_analyst = models.BooleanField(
        default=False,
        help_text="Can approve/reject normalized emission records.",
    )
    is_uploader = models.BooleanField(
        default=False,
        help_text="Can upload source data files.",
    )

    class Meta:
        ordering = ["username"]

    def __str__(self):
        if self.tenant_id:
            return f"{self.username} ({self.tenant.company_name})"
        return self.username
