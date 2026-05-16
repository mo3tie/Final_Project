from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from toll.models import Trip

from .demo_payload import (
    build_synthetic_demo,
    filter_demo_trips,
    should_use_demo,
    trip_stats_from_list,
)
from vehicles.models import Vehicle

from .demo_payload import DEMO_PLATE
from .me_utils import _display_plate


def _user_display_plate(user) -> str:
    v = Vehicle.objects.filter(user=user).order_by("id").first()
    return (v.license_plate or "").strip() if v else ""


def _governorate_from_location(gate_location: str) -> str:
    loc = (gate_location or "").strip()
    if not loc:
        return ""
    return loc.split(",")[0].strip()


class TripHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        governorate = (request.query_params.get("governorate") or "").strip()

        if should_use_demo(user):
            demo = build_synthetic_demo(user.id)
            trips = filter_demo_trips(
                demo["trips"],
                date_from,
                date_to,
                governorate or None,
            )
            return Response(
                {
                    "stats": trip_stats_from_list(trips),
                    "trips": trips,
                    "display_plate": DEMO_PLATE,
                    "synthetic_demo": True,
                }
            )

        qs = (
            Trip.objects.filter(vehicle__user=user)
            .select_related("vehicle", "gate")
            .order_by("-trip_time")
        )

        if date_from:
            qs = qs.filter(trip_time__date__gte=date_from)
        if date_to:
            qs = qs.filter(trip_time__date__lte=date_to)

        rows = list(qs[:500])
        if governorate:
            rows = [
                t
                for t in rows
                if _governorate_from_location(t.gate.gate_location) == governorate
            ]

        trips = []
        for t in rows:
            st = t.status or "Pending"
            if st == "Paid":
                display_status = "Paid"
            elif st == "Unpaid":
                display_status = "Not Paid"
            else:
                display_status = st
            gov = _governorate_from_location(t.gate.gate_location)
            trips.append(
                {
                    "id": t.trip_id,
                    "dateIso": t.trip_time.date().isoformat(),
                    "dateTime": t.trip_time.strftime("%b %d, %Y %I:%M %p"),
                    "governorate": gov or "—",
                    "vehiclePlate": _display_plate(t.vehicle.license_plate),
                    "gateName": t.gate.gate_name,
                    "fareAmount": float(t.fare_amount),
                    "status": display_status,
                    "violationAmount": 0.0,
                }
            )

        total_trips = len(trips)
        total_fare = sum(
            t["fareAmount"] for t in trips if t["status"] == "Paid"
        )
        total_viol = sum(t["violationAmount"] for t in trips)

        return Response(
            {
                "stats": {
                    "totalTrips": total_trips,
                    "totalFarePaid": total_fare,
                    "totalViolations": total_viol,
                },
                "trips": trips,
                "display_plate": _user_display_plate(user),
            }
        )
