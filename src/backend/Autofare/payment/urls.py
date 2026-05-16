from django.urls import path

from . import views

urlpatterns = [
    path("wallet/", views.WalletView.as_view(), name="payment-wallet"),
    path("wallet/recharge/", views.WalletRechargeView.as_view(), name="payment-wallet-recharge"),
]
