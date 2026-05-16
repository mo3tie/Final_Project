from django.urls import path

from .views import AdminPlateScanView, PlateScanDetailView, UserPlateScanListView

urlpatterns = [
    path("plate-scans/", UserPlateScanListView.as_view(), name="plate-scan-list"),
    path("plate-scans/<int:pk>/", PlateScanDetailView.as_view(), name="plate-scan-detail"),
    path("admin/plate-scans/", AdminPlateScanView.as_view(), name="admin-plate-scan"),
]
