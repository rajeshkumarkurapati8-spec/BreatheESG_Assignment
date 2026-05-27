from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from audit.views import AuditLogViewSet
from emissions.views import DashboardStatsView, NormalizedEmissionRecordViewSet
from ingestion.views import DataSourceViewSet, RawRecordViewSet, UploadView
from review.views import ApproveRecordView, PendingReviewViewSet, RejectRecordView
from tenants.views import CurrentUserView, TenantViewSet

router = DefaultRouter()
router.register(r"tenants", TenantViewSet, basename="tenant")
router.register(r"sources", DataSourceViewSet, basename="source")
router.register(r"raw-records", RawRecordViewSet, basename="raw-record")
router.register(r"normalized-records", NormalizedEmissionRecordViewSet, basename="normalized-record")
router.register(r"review/pending", PendingReviewViewSet, basename="review-pending")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", CurrentUserView.as_view(), name="current_user"),
    path("api/uploads/", UploadView.as_view(), name="upload"),
    path("api/review/approve/", ApproveRecordView.as_view(), name="review-approve"),
    path("api/review/reject/", RejectRecordView.as_view(), name="review-reject"),
    path("api/dashboard/", DashboardStatsView.as_view(), name="dashboard"),
    path("api/", include(router.urls)),
]
