from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from config.permissions import HasTenant
from tenants.models import Tenant
from tenants.serializers import TenantSerializer, UserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, HasTenant]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """Tenant members can view their own organization only."""

    queryset = Tenant.objects.all()
    permission_classes = [IsAuthenticated, HasTenant]
    serializer_class = TenantSerializer

    def get_queryset(self):
        return Tenant.objects.filter(pk=self.request.user.tenant_id)
