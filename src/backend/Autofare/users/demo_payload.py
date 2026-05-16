"""
Deterministic demo data (seeded by user id) when the account has no real trips
and no wallet transactions. Keeps wallet totals, trip stats, violations, alerts,
and monthly graphs consistent with each other.
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

# Synthetic demo data only (not shown for users with real vehicles/trips).
DEMO_PLATE = "DEMO-PLATE"

GATES = [
    ("6th October Gate", "Giza, 6th October"),
    ("Smart Village Gate", "Giza, Smart Village"),
    ("New Cairo Toll", "Cairo, New Cairo"),
    ("Ring Road North", "Qalyubia, Ring Road"),
    ("Alexandria East Gate", "Alexandria, Agricultural Road"),
    ("October Corridor", "Giza, Corridor"),
    ("Ain Sokhna Road Gate", "Suez, Sokhna Road"),
    ("Helwan Link Gate", "Cairo, Helwan"),
]

_ALERT_TYPES = (
    "Toll evasion risk",
    "Unpaid gate pass",
    "Late payment notice",
    "Violation pending",
)


def _rng(user_id: int) -> random.Random:
    return random.Random(user_id * 10007 + 12345)


def _money(d: float | Decimal) -> Decimal:
    return Decimal(str(d)).quantize(Decimal("0.01"))


def build_synthetic_demo(user_id: int) -> dict:
    r = _rng(user_id)
    now = timezone.now()
    plate = DEMO_PLATE

    n_trips = r.randint(16, 28)
    trip_rows: list[dict] = []
    for i in range(n_trips):
        days_ago = r.randint(0, 115)
        trip_time = now - timedelta(
            days=days_ago,
            hours=r.randint(6, 22),
            minutes=r.randint(0, 59),
        )
        fare_f = float(r.choice([12, 15, 18, 22, 25, 28, 32, 38, 45, 52, 60]))
        is_paid = r.random() < 0.82
        viol_f = 0.0
        if not is_paid:
            viol_f = float(r.choice([55, 75, 100, 120, 150, 185, 220]))
        gate_name, loc = r.choice(GATES)
        gov = loc.split(",")[0].strip()
        trip_rows.append(
            {
                "trip_time": trip_time,
                "fare": fare_f,
                "paid": is_paid,
                "violation": viol_f,
                "gate": gate_name,
                "gov": gov,
                "id": 800_000 + user_id * 5_000 + i,
            }
        )

    trip_rows.sort(key=lambda x: x["trip_time"], reverse=True)

    trips_api = []
    for tr in trip_rows:
        tt = tr["trip_time"]
        trips_api.append(
            {
                "id": tr["id"],
                "dateIso": tt.date().isoformat(),
                "dateTime": tt.strftime("%b %d, %Y %I:%M %p"),
                "governorate": tr["gov"],
                "vehiclePlate": plate,
                "gateName": tr["gate"],
                "fareAmount": tr["fare"],
                "status": "Paid" if tr["paid"] else "Not Paid",
                "violationAmount": tr["violation"],
            }
        )

    today = now.date()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)
    first_this_month = month_start
    last_day_prev = first_this_month - timedelta(days=1)
    prev_month_start = last_day_prev.replace(day=1)

    total_trips = len(trip_rows)
    total_paid_fare = _money(
        sum(tr["fare"] for tr in trip_rows if tr["paid"])
    )
    total_fare_all = _money(sum(tr["fare"] for tr in trip_rows))
    unpaid_count = sum(1 for tr in trip_rows if not tr["paid"])
    total_viol_amount = _money(sum(tr["violation"] for tr in trip_rows))

    today_trips = sum(1 for tr in trip_rows if tr["trip_time"].date() == today)
    yesterday_trips = sum(1 for tr in trip_rows if tr["trip_time"].date() == yesterday)

    monthly_paid = _money(
        sum(
            tr["fare"]
            for tr in trip_rows
            if tr["paid"] and tr["trip_time"].date() >= month_start
        )
    )
    last_month_paid = _money(
        sum(
            tr["fare"]
            for tr in trip_rows
            if tr["paid"]
            and prev_month_start <= tr["trip_time"].date() < first_this_month
        )
    )

    recent_trips = []
    for tr in trip_rows[:8]:
        tt = tr["trip_time"]
        recent_trips.append(
            {
                "id": tr["id"],
                "vehicle": plate,
                "vehicle_type": "car",
                "time": tt.strftime("%b %d, %Y %I:%M %p"),
                "fare": tr["fare"],
                "status": "Completed" if tr["paid"] else "Not Paid",
                "violation_amount": tr["violation"],
            }
        )

    alerts = []
    aid = 1
    for tr in trip_rows:
        if not tr["paid"] and tr["violation"] > 0:
            tt = tr["trip_time"]
            alerts.append(
                {
                    "id": aid,
                    "alert_type": r.choice(_ALERT_TYPES),
                    "alert_description": f"{_money(tr['violation'])} EGP — plate {plate} · {tr['gate']}",
                    "time_elapsed": tt.strftime("%b %d, %Y %I:%M %p"),
                    "severity": "critical",
                }
            )
            aid += 1
            if len(alerts) >= 5:
                break
    if not alerts:
        alerts.append(
            {
                "id": 1,
                "alert_type": "All clear",
                "alert_description": f"No unpaid violations — plate {plate}",
                "time_elapsed": now.strftime("%b %d, %Y %I:%M %p"),
                "severity": "warning",
            }
        )

    # Wallet: chronological forward, then reverse for API (newest first)
    n_tx = r.randint(12, 22)
    tx_events: list[tuple] = []
    cursor = now - timedelta(days=160)
    balance = Decimal("0")
    for j in range(n_tx):
        cursor += timedelta(days=r.randint(2, 18))
        if cursor > now - timedelta(hours=2):
            cursor = now - timedelta(days=r.randint(0, 3), hours=r.randint(1, 20))
        kind = r.choices(
            ["Recharge", "Fare", "Fare", "Fine"],
            weights=[2, 5, 5, 2],
            k=1,
        )[0]
        if kind == "Recharge":
            amt = _money(r.randint(4, 28) * 100)
            balance += amt
            tx_events.append(
                (
                    cursor,
                    "Recharge",
                    amt,
                    f"Card *{r.randint(1000, 9999)}",
                )
            )
        elif kind == "Fare":
            amt = -_money(r.uniform(12, 55))
            balance += amt
            tx_events.append((cursor, "Fare", amt, r.choice(GATES)[0]))
        else:
            amt = -_money(r.choice([40, 60, 80, 100, 120]))
            balance += amt
            tx_events.append((cursor, "Fine", amt, "Violation settlement"))

    if balance < _money(350):
        topup = _money(r.randint(15, 35) * 100)
        balance += topup
        tx_events.append((now - timedelta(hours=r.randint(5, 48)), "Recharge", topup, "Card *4242"))

    tx_events.sort(key=lambda x: x[0])
    recharged = sum((e[2] for e in tx_events if e[1] == "Recharge"), Decimal("0"))
    fares = sum((e[2] for e in tx_events if e[1] == "Fare"), Decimal("0"))
    fines = sum((e[2] for e in tx_events if e[1] == "Fine"), Decimal("0"))

    transactions_list = []
    for idx, (dt, typ, amt, src) in enumerate(reversed(tx_events)):
        transactions_list.append(
            {
                "id": -(idx + 1),
                "date": dt.isoformat(),
                "type": typ,
                "amount": str(amt),
                "source": src,
                "status": "Completed",
            }
        )

    wallet_response = {
        "balance": str(balance.quantize(Decimal("0.01"))),
        "currency": "EGP",
        "summary": {
            "total_recharged": str(recharged.quantize(Decimal("0.01"))),
            "total_fares": str(abs(fares).quantize(Decimal("0.01"))),
            "total_fines": str(abs(fines).quantize(Decimal("0.01"))),
        },
        "transactions": transactions_list,
    }

    me_stats = {
        "total_trips": total_trips,
        "unpaid_violations": unpaid_count,
        "total_fare_paid": str(total_paid_fare),
        "total_fare_all": str(total_fare_all),
        "wallet_balance": wallet_response["balance"],
        "today_trips": today_trips,
        "yesterday_trips": yesterday_trips,
        "monthly_paid_fare": str(monthly_paid),
        "last_month_paid_fare": str(last_month_paid),
    }

    return {
        "trips": trips_api,
        "trip_stats": {
            "totalTrips": total_trips,
            "totalFarePaid": float(total_paid_fare),
            "totalViolations": float(total_viol_amount),
        },
        "wallet": wallet_response,
        "me_stats": me_stats,
        "recent_trips": recent_trips,
        "alerts": alerts,
        "wallet_balance": wallet_response["balance"],
    }


def filter_demo_trips(
    trips: list[dict],
    date_from: str | None,
    date_to: str | None,
    governorate: str | None,
) -> list[dict]:
    out = trips
    if governorate:
        out = [t for t in out if t.get("governorate") == governorate]
    if date_from:
        out = [t for t in out if t.get("dateIso", "") >= date_from]
    if date_to:
        out = [t for t in out if t.get("dateIso", "") <= date_to]
    return out


def trip_stats_from_list(trips: list[dict]) -> dict:
    total_trips = len(trips)
    total_fare = sum(t["fareAmount"] for t in trips if t["status"] == "Paid")
    total_viol = sum(t["violationAmount"] for t in trips)
    return {
        "totalTrips": total_trips,
        "totalFarePaid": total_fare,
        "totalViolations": total_viol,
    }


def should_use_demo(user) -> bool:
    from toll.models import Trip

    from .models import Transaction, Wallet

    if Trip.objects.filter(vehicle__user=user).exists():
        return False
    wallet, _ = Wallet.objects.get_or_create(user=user)
    if Transaction.objects.filter(wallet=wallet).exists():
        return False
    return True
