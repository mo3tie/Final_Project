from django.urls import path

from . import views
from .admin_views import AdminAccountListView, AdminDashboardStatsView, AdminTripsListView, AdminWalletStatsView
from .photo_views import ProfilePhotoView
from .trip_views import TripHistoryView
from .verify_views import VerifyPasswordView

app_name = "users"

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/signup/", views.SignupView.as_view(), name="auth-signup"),
    path("auth/send-otp/", views.SendSignupOtpView.as_view(), name="auth-send-otp"),
    path("me/", views.CurrentUserView.as_view(), name="me"),
    path("me/photo/", ProfilePhotoView.as_view(), name="me-photo"),
    path("me/verify-password/", VerifyPasswordView.as_view(), name="me-verify-password"),
    path("trips/", TripHistoryView.as_view(), name="trips-history"),
    path("admin/accounts/", AdminAccountListView.as_view(), name="admin-accounts"),
    path("admin/dashboard/", AdminDashboardStatsView.as_view(), name="admin-dashboard"),
    path("admin/trips/", AdminTripsListView.as_view(), name="admin-trips"),
    path("admin/wallet/", AdminWalletStatsView.as_view(), name="admin-wallet"),
]
