"""Simulated gate pass: Trip + wallet fare on each AI portal scan."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import transaction

from toll.models import Gate, Trip
from users.models import Transaction, Wallet
from vehicles.models import Vehicle

DEFAULT_GATE_ID = "GATE-001"


class PlateBelongsToOtherUser(Exception):
    """Detected plate is registered to another account."""


class PlateNotDetected(Exception):
    """OCR did not return a readable plate."""


def canonical_plate(value: str) -> str:
    return " ".join((value or "").split()).strip()[:20]


def map_ai_vehicle_type(ai_label: str, fallback: str = "car") -> str:
    low = (ai_label or "").lower()
    for key in ("truck", "bus", "minibus", "van", "motorcycle", "car"):
        if key in low:
            return key
    allowed = {c[0] for c in Vehicle.VEHICLE_TYPES}
    return fallback if fallback in allowed else "car"


def find_vehicle_by_plate(plate: str) -> Vehicle | None:
    p = canonical_plate(plate)
    if not p:
        return None
    return Vehicle.objects.filter(license_plate__iexact=p).first()


def get_default_gate() -> Gate:
    gate, _ = Gate.objects.get_or_create(
        gate_id=DEFAULT_GATE_ID,
        defaults={
            "gate_name": "Misr-Gate Auto",
            "gate_location": "Simulated toll gate",
        },
    )
    return gate


def resolve_or_create_vehicle(
    user,
    plate: str,
    ai_vehicle_type: str,
    *,
    default_vehicle_type: str = "car",
    model_label: str = "",
    color: str = "",
) -> tuple[Vehicle, bool]:
    """
    Return (vehicle, created).
    Raises PlateBelongsToOtherUser if plate belongs to another account.
    """
    stored = canonical_plate(plate)
    if not stored:
        raise PlateNotDetected()

    existing = find_vehicle_by_plate(stored)
    if existing:
        if existing.user_id != user.id:
            raise PlateBelongsToOtherUser()
        return existing, False

    vtype = map_ai_vehicle_type(ai_vehicle_type, default_vehicle_type)
    vehicle = Vehicle.objects.create(
        user=user,
        vehicle_type=vtype,
        license_plate=stored,
        model_label=(model_label or "")[:120],
        color=(color or "")[:50],
    )
    return vehicle, True


@transaction.atomic
def record_gate_pass(vehicle: Vehicle, *, gate: Gate | None = None) -> dict:
    """Create a trip and debit wallet when balance allows (gate simulation)."""
    gate = gate or get_default_gate()
    trip = Trip(vehicle=vehicle, gate=gate, fare_amount=Decimal("0"))
    trip.save()

    wallet, _ = Wallet.objects.select_for_update().get_or_create(
        user=vehicle.user,
        defaults={"wallet_balance": Decimal("0")},
    )
    fare = trip.fare_amount
    paid = False

    if wallet.wallet_balance >= fare:
        tid = f"FARE-{trip.trip_id}-{uuid.uuid4().hex[:8].upper()}"
        Transaction.objects.create(
            wallet=wallet,
            transaction_id=tid,
            transaction_type="Fare",
            visa_type=gate.gate_name,
            amount=-fare,
        )
        wallet.wallet_balance -= fare
        wallet.save(update_fields=["wallet_balance"])
        trip.status = "Paid"
        trip.save(update_fields=["status"])
        paid = True
    else:
        trip.status = "Unpaid"
        trip.save(update_fields=["status"])

    return {
        "trip_id": trip.trip_id,
        "fare_amount": str(fare),
        "trip_status": trip.status,
        "paid": paid,
        "wallet_balance": str(wallet.wallet_balance),
        "gate_name": gate.gate_name,
    }
