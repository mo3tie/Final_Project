import uuid
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.demo_payload import build_synthetic_demo, should_use_demo
from users.models import Transaction, Wallet

from .serializers import WalletRechargeSerializer


def _mask_card(last4: str) -> str:
    return f"Card *{last4}"


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if should_use_demo(request.user):
            return Response(build_synthetic_demo(request.user.id)["wallet"])

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        txs = wallet.transactions.order_by("-date")[:100]
        recharged = (
            wallet.transactions.filter(transaction_type="Recharge").aggregate(
                s=Sum("amount")
            )["s"]
            or Decimal("0")
        )
        fares = (
            wallet.transactions.filter(transaction_type="Fare").aggregate(s=Sum("amount"))[
                "s"
            ]
            or Decimal("0")
        )
        fines = (
            wallet.transactions.filter(transaction_type="Fine").aggregate(s=Sum("amount"))[
                "s"
            ]
            or Decimal("0")
        )

        transactions_list = [
            {
                "id": t.id,
                "date": t.date.isoformat(),
                "type": t.transaction_type,
                "amount": str(t.amount),
                "source": t.visa_type or "Wallet",
                "status": "Completed",
            }
            for t in txs
        ]

        data = {
            "balance": str(wallet.wallet_balance),
            "currency": "EGP",
            "summary": {
                "total_recharged": str(recharged),
                "total_fares": str(abs(fares) if fares < 0 else fares),
                "total_fines": str(abs(fines) if fines < 0 else fines),
            },
            "transactions": transactions_list,
        }
        return Response(data)


class WalletRechargeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = WalletRechargeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        amount = ser.validated_data["amount"]
        card_digits = ser.validated_data["card_number"]
        last4 = card_digits[-4:]

        with transaction.atomic():
            wallet, _ = Wallet.objects.select_for_update().get_or_create(
                user=request.user,
                defaults={"wallet_balance": Decimal("0")},
            )
            tid = f"RC-{uuid.uuid4().hex[:16].upper()}"
            Transaction.objects.create(
                wallet=wallet,
                transaction_id=tid,
                transaction_type="Recharge",
                visa_type=_mask_card(last4),
                amount=amount,
            )
            wallet.wallet_balance = (wallet.wallet_balance or Decimal("0")) + amount
            wallet.save(update_fields=["wallet_balance"])

        return Response(
            {
                "message": "Wallet recharged successfully.",
                "balance": str(wallet.wallet_balance),
                "currency": "EGP",
                "transaction_id": tid,
            },
            status=201,
        )
