from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from toll.models import Trip
from violations.models import Violation

from vehicles.models import Vehicle

from .models import UserProfile, Wallet


def fleet_id_for_user(user) -> str:
    return f"GP-{user.id:06d}"


def _display_plate(stored: str) -> str:
    """Return stored plate only — no synthetic fallback."""
    return (stored or "").strip()


def _primary_display_plate(vehicle_data: list, latest_scan: dict | None) -> str:
    if vehicle_data:
        p = (vehicle_data[0].get("plate") or "").strip()
        if p:
            return p
    if latest_scan:
        p = (latest_scan.get("detected_plate_text") or latest_scan.get("registered_plate") or "").strip()
        if p:
            return p
    return ""


def _absolute_media_url(request, relative_url: str) -> str:
    if not relative_url:
        return ""
    if request:
        return request.build_absolute_uri(relative_url)
    return relative_url


def build_me_payload(user, request=None):
    profile = UserProfile.objects.filter(user=user).first()

    wallet, _ = Wallet.objects.get_or_create(user=user)

    vehicles = Vehicle.objects.filter(user=user).order_by("id")

    vehicle_data = []
    for v in vehicles:
        label = dict(Vehicle.VEHICLE_TYPES).get(v.vehicle_type, v.vehicle_type)
        vehicle_data.append(
            {
                "id": v.id,
                "plate": _display_plate(v.license_plate),
                "model": v.model_label or label,
                "color": v.color or "",
                "type": label,
                "vehicle_type": v.vehicle_type,
                "status": "Active" if v.is_active else "Inactive",
                "is_active": v.is_active,
            }
        )

    trip_agg = Trip.objects.filter(vehicle__user=user).aggregate(
        total=Count("trip_id"),
    )
    total_trips = trip_agg["total"] or 0

    paid_fare_agg = Trip.objects.filter(vehicle__user=user, status="Paid").aggregate(
        s=Sum("fare_amount")
    )
    total_paid_fare = paid_fare_agg["s"] or Decimal("0")

    all_fare_agg = Trip.objects.filter(vehicle__user=user).aggregate(
        s=Sum("fare_amount")
    )
    total_fare_all = all_fare_agg["s"] or Decimal("0")

    now = timezone.now()
    today = now.date()
    today_trips = Trip.objects.filter(vehicle__user=user, trip_time__date=today).count()
    yesterday = today - timedelta(days=1)
    yesterday_trips = Trip.objects.filter(
        vehicle__user=user, trip_time__date=yesterday
    ).count()

    month_start = today.replace(day=1)
    monthly_paid_fare = (
        Trip.objects.filter(
            vehicle__user=user,
            status="Paid",
            trip_time__date__gte=month_start,
        ).aggregate(s=Sum("fare_amount"))["s"]
        or Decimal("0")
    )

    first_this_month = today.replace(day=1)
    last_day_prev = first_this_month - timedelta(days=1)
    prev_month_start = last_day_prev.replace(day=1)
    last_month_paid_fare = (
        Trip.objects.filter(
            vehicle__user=user,
            status="Paid",
            trip_time__date__gte=prev_month_start,
            trip_time__date__lt=first_this_month,
        ).aggregate(s=Sum("fare_amount"))["s"]
        or Decimal("0")
    )

    unpaid_violations = Violation.objects.filter(
        vehicle__user=user, status="Unpaid"
    ).count()

    recent = (
        Trip.objects.filter(vehicle__user=user)
        .select_related("vehicle", "gate")
        .order_by("-trip_time")[:8]
    )
    recent_trips = []
    for t in recent:
        st = t.status or "Pending"
        if st == "Paid":
            display = "Completed"
        elif st == "Unpaid":
            display = "Not Paid"
        else:
            display = st
        recent_trips.append(
            {
                "id": t.trip_id,
                "vehicle": _display_plate(t.vehicle.license_plate),
                "vehicle_type": t.vehicle.vehicle_type,
                "time": t.trip_time.strftime("%b %d, %Y %I:%M %p"),
                "fare": float(t.fare_amount),
                "status": display,
                "violation_amount": 0.0,
            }
        )

    name = (user.get_full_name() or "").strip() or user.first_name or user.email

    photo_url = ""
    if profile and profile.photo:
        photo_url = _absolute_media_url(request, profile.photo.url)

    violations_recent = (
        Violation.objects.filter(vehicle__user=user, status="Unpaid")
        .select_related("vehicle")
        .order_by("-violation_date")[:5]
    )
    alerts = []
    for v in violations_recent:
        alerts.append(
            {
                "id": v.id,
                "alert_type": (v.violation_type or "Violation").replace("_", " ").title(),
                "alert_description": f"{v.base_penalty} EGP — plate {_display_plate(v.vehicle.license_plate)}",
                "time_elapsed": v.violation_date.strftime("%b %d, %Y %I:%M %p"),
                "severity": "critical",
            }
        )

    from ai.models import PlateScan
    from ai.services import scan_to_dict

    recent_scans = [
        scan_to_dict(s, request)
        for s in PlateScan.objects.filter(user=user).select_related("vehicle")[:5]
    ]
    latest_scan = recent_scans[0] if recent_scans else None

    payload = {
        "id": user.id,
        "name": name,
        "email": user.email,
        "phone": profile.phone if profile else "",
        "national_id": profile.national_id if profile else "",
        "photo_url": photo_url,
        "fleet_id": fleet_id_for_user(user),
        "wallet_balance": str(wallet.wallet_balance),
        "currency": "EGP",
        "vehicles": vehicle_data,
        "stats": {
            "total_trips": total_trips,
            "unpaid_violations": unpaid_violations,
            "total_fare_paid": str(total_paid_fare),
            "total_fare_all": str(total_fare_all),
            "wallet_balance": str(wallet.wallet_balance),
            "today_trips": today_trips,
            "yesterday_trips": yesterday_trips,
            "monthly_paid_fare": str(monthly_paid_fare),
            "last_month_paid_fare": str(last_month_paid_fare),
        },
        "recent_trips": recent_trips,
        "alerts": alerts,
        "display_plate": _primary_display_plate(vehicle_data, latest_scan),
        "plate_scans": recent_scans,
        "latest_plate_scan": latest_scan,
    }

    from .demo_payload import build_synthetic_demo, should_use_demo

    if should_use_demo(user):
        demo = build_synthetic_demo(user.id)
        payload["wallet_balance"] = demo["wallet_balance"]
        payload["stats"].update(demo["me_stats"])
        payload["recent_trips"] = demo["recent_trips"]
        payload["alerts"] = demo["alerts"]
        payload["synthetic_demo"] = True

    return payload
