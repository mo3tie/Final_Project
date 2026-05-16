from datetime import date

from django.contrib.auth.models import User
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from toll.models import Trip
from users.models import Transaction, Wallet
from violations.models import Violation
from .me_utils import fleet_id_for_user
from .permissions import IsAdminUser


def _user_label(user: User) -> str:
    full = (user.get_full_name() or "").strip()
    return full or user.first_name or user.email or user.username


class AdminAccountListView(APIView):
    """List non-staff accounts for admin vehicle registration."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = (
            User.objects.filter(is_active=True, is_staff=False)
            .order_by("email")
            .select_related("profile")[:500]
        )
        rows = []
        for u in qs:
            profile = getattr(u, "profile", None)
            rows.append(
                {
                    "id": u.id,
                    "name": _user_label(u),
                    "email": u.email,
                    "phone": profile.phone if profile else "",
                    "fleet_id": fleet_id_for_user(u),
                }
            )
        return Response(rows)


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = date.today()
        current_year = today.year

        total_users = User.objects.filter(is_active=True, is_staff=False).count()
        wallet_balance = (
            Wallet.objects.aggregate(total=Sum("wallet_balance"))[
                "total"
            ]
            or 0
        )
        total_trips = Trip.objects.count()
        active_violations = Violation.objects.filter(status__iexact="Unpaid").count()
        violations_fines = (
            Violation.objects.filter(status__iexact="Unpaid").aggregate(
                total=Sum("base_penalty")
            )["total"]
            or 0
        )

        revenue_by_month = []
        trips_by_month = []
        for month in range(1, 13):
            paid_value = (
                Trip.objects.filter(
                    trip_time__year=current_year,
                    trip_time__month=month,
                    status__iexact="Paid",
                )
                .aggregate(total=Sum("fare_amount"))
                ["total"]
                or 0
            )
            trip_count = (
                Trip.objects.filter(
                    trip_time__year=current_year,
                    trip_time__month=month,
                )
                .count()
            )
            revenue_by_month.append(
                {"monthIndex": month, "amount": float(paid_value)}
            )
            trips_by_month.append(
                {"monthIndex": month, "count": trip_count}
            )

        recent_trips = []
        for trip in Trip.objects.select_related("vehicle__user").order_by("-trip_time")[:5]:
            recent_trips.append(
                {
                    "id": trip.trip_id,
                    "vehicle": trip.vehicle.license_plate,
                    "time": trip.trip_time.isoformat(),
                    "fare": float(trip.fare_amount),
                    "status": trip.status,
                    "user": trip.vehicle.user.email,
                }
            )

        return Response(
            {
                "total_users": total_users,
                "wallet_balance": float(wallet_balance),
                "total_trips": total_trips,
                "active_violations": active_violations,
                "violations_fines": float(violations_fines),
                "revenue_by_month": revenue_by_month,
                "trips_by_month": trips_by_month,
                "recent_trips": recent_trips,
            }
        )


class AdminTripsListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        trips = Trip.objects.select_related("vehicle__user", "gate").order_by("-trip_time")[:100]
        rows = []
        for trip in trips:
            user = trip.vehicle.user if trip.vehicle else None
            rows.append(
                {
                    "id": trip.trip_id,
                    "date_time": trip.trip_time.isoformat(),
                    "governorate": getattr(trip.gate, "gate_location", "—"),
                    "vehicle_plate": trip.vehicle.license_plate if trip.vehicle else "—",
                    "vehicle_type": trip.vehicle.vehicle_type if trip.vehicle else "—",
                    "gate_name": trip.gate.gate_name if trip.gate else "—",
                    "fare_amount": float(trip.fare_amount),
                    "status": trip.status,
                    "user_email": user.email if user else "—",
                }
            )

        total_revenue = Trip.objects.aggregate(total=Sum("fare_amount"))["total"] or 0
        total_violations = Violation.objects.count()

        return Response(
            {
                "trips": rows,
                "total_system_revenue": float(total_revenue),
                "total_system_violations": total_violations,
            }
        )


class AdminWalletStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = date.today()
        current_year = today.year

        total_liquidity = (
            Wallet.objects.aggregate(total=Sum("wallet_balance"))[
                "total"
            ]
            or 0
        )
        total_revenue = Trip.objects.aggregate(total=Sum("fare_amount"))[
            "total"
        ] or 0
        total_unpaid_fines = (
            Violation.objects.filter(status__iexact="Unpaid").aggregate(
                total=Sum("base_penalty")
            )["total"]
            or 0
        )

        revenue_by_month = []
        for month in range(1, 13):
            paid_value = (
                Trip.objects.filter(
                    trip_time__year=current_year,
                    trip_time__month=month,
                    status__iexact="Paid",
                )
                .aggregate(total=Sum("fare_amount"))
                ["total"]
                or 0
            )
            revenue_by_month.append(
                {"monthIndex": month, "month": date(current_year, month, 1).strftime("%b"), "revenue": float(paid_value)}
            )

        recent_transactions = []
        transactions = Transaction.objects.select_related("wallet__user").order_by("-date")[:10]
        for tx in transactions:
            user = tx.wallet.user if tx.wallet else None
            recent_transactions.append(
                {
                    "id": tx.id,
                    "date": tx.date.isoformat(),
                    "user_id": user.id if user else None,
                    "user_name": user.get_full_name() or user.email if user else "—",
                    "plate": "—",
                    "amount": float(tx.amount),
                    "method": tx.transaction_type,
                    "status": "Paid",
                }
            )

        return Response(
            {
                "total_liquidity": float(total_liquidity),
                "total_revenue": float(total_revenue),
                "total_unpaid_fines": float(total_unpaid_fines),
                "revenue_by_month": revenue_by_month,
                "recent_transactions": recent_transactions,
            }
        )
