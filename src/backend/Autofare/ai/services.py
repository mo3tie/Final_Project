"""Bridge to huggingface-space YOLO pipeline."""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile

from vehicles.models import Vehicle

from .image_io import decode_bytes_to_bgr, read_upload_bytes

from .gate_service import (
    PlateBelongsToOtherUser,
    PlateNotDetected,
    canonical_plate,
    record_gate_pass,
    resolve_or_create_vehicle,
)
from .models import PlateScan

log = logging.getLogger(__name__)

_HF_ROOT = Path(settings.BASE_DIR).resolve().parent.parent.parent / "huggingface-space"


def _ensure_vision_path() -> None:
    p = str(_HF_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)


def normalize_plate(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def plates_match(registered: str, detected: str) -> bool:
    a = normalize_plate(registered)
    b = normalize_plate(detected)
    if not a or not b:
        return False
    if a == b:
        return True
    return a in b or b in a


def run_vision_pipeline(image_bgr: np.ndarray) -> dict:
    _ensure_vision_path()
    from vision_api.full_pipeline import analyze_image_bgr

    rtl = True
    return analyze_image_bgr(
        image_bgr,
        rtl=rtl,
        car_conf=float(getattr(settings, "AI_CAR_CONF", 0.12)),
        plate_conf=float(getattr(settings, "AI_PLATE_CONF", 0.15)),
        ocr_conf=float(getattr(settings, "AI_OCR_CONF", 0.10)),
    )


def create_plate_scan(
    user,
    uploaded_file,
    *,
    source: str = PlateScan.SOURCE_MANUAL,
    signup_vehicle_type: str | None = None,
    signup_model: str = "",
    signup_color: str = "",
    record_gate_pass_trip: bool | None = None,
) -> PlateScan:
    """
    Run Car + Plate + OCR, resolve vehicle from detected plate, optionally simulate gate fare.
    """
    if record_gate_pass_trip is None:
        record_gate_pass_trip = source == PlateScan.SOURCE_MANUAL

    default_type = signup_vehicle_type or "car"

    scan = PlateScan(
        user=user,
        vehicle=None,
        source=source,
        registered_plate="",
    )

    raw_bytes = read_upload_bytes(uploaded_file) if uploaded_file else b""
    bgr = decode_bytes_to_bgr(raw_bytes) if raw_bytes else None

    if bgr is None:
        scan.models_ready = False
        scan.error_message = (
            "Could not read image. Use JPG or PNG and try again."
            if not raw_bytes
            else "Could not decode image format."
        )
        scan.save()
        return scan

    if raw_bytes:
        fname = getattr(uploaded_file, "name", None) or "upload.jpg"
        scan.image.save(fname, ContentFile(raw_bytes), save=False)

    gate_payload: dict | None = None
    vehicle_created = False

    try:
        result = run_vision_pipeline(bgr)
        scan.detected_vehicle_type = (result.get("vehicle_type") or "")[:64]
        scan.detected_plate_text = canonical_plate(result.get("plate_text") or "")[:128]
        scan.raw_result = {
            "vehicle_detections": result.get("vehicle_detections") or [],
            "plate_detections": result.get("plate_detections") or [],
            "plate_ocr_reads": result.get("plate_ocr_reads") or [],
        }
        annotated = result.get("annotated_bgr")
        if annotated is not None:
            ok, buf = cv2.imencode(".jpg", annotated)
            if ok:
                scan.annotated_image.save(
                    f"annotated_{user.id}.jpg",
                    ContentFile(buf.tobytes()),
                    save=False,
                )

        if not scan.detected_plate_text:
            scan.models_ready = True
            scan.error_message = "No license plate detected in the image."
            scan.save()
            raise PlateNotDetected()

        vehicle, vehicle_created = resolve_or_create_vehicle(
            user,
            scan.detected_plate_text,
            scan.detected_vehicle_type,
            default_vehicle_type=default_type,
            model_label=signup_model,
            color=signup_color,
        )
        scan.vehicle = vehicle
        scan.registered_plate = vehicle.license_plate
        scan.plate_match = True

        if record_gate_pass_trip:
            gate_payload = record_gate_pass(vehicle)

        scan.raw_result["gate_pass"] = gate_payload or {}
        scan.raw_result["vehicle_created"] = vehicle_created

    except (PlateBelongsToOtherUser, PlateNotDetected):
        scan.save()
        raise
    except FileNotFoundError as e:
        scan.models_ready = False
        scan.error_message = str(e)
        log.exception("AI weights missing")
    except Exception as e:
        scan.models_ready = False
        scan.error_message = str(e)[:500]
        log.exception("AI pipeline failed")

    scan.save()
    return scan


def scan_to_dict(scan: PlateScan, request=None) -> dict:
    def _url(field):
        if not field:
            return ""
        try:
            if request:
                return request.build_absolute_uri(field.url)
            return field.url
        except Exception:
            return ""

    raw = scan.raw_result or {}
    gate = raw.get("gate_pass") if isinstance(raw.get("gate_pass"), dict) else {}

    owner = scan.user
    owner_name = ""
    owner_email = ""
    if owner:
        owner_name = (owner.get_full_name() or "").strip() or owner.first_name or ""
        owner_email = owner.email or ""

    return {
        "id": scan.id,
        "source": scan.source,
        "owner_user_id": scan.user_id,
        "owner_name": owner_name,
        "owner_email": owner_email,
        "registered_plate": scan.registered_plate,
        "detected_vehicle_type": scan.detected_vehicle_type,
        "detected_plate_text": scan.detected_plate_text,
        "plate_match": scan.plate_match,
        "models_ready": scan.models_ready,
        "error_message": scan.error_message,
        "vehicle_id": scan.vehicle_id,
        "vehicle_created": bool(raw.get("vehicle_created")),
        "image_url": _url(scan.image),
        "annotated_image_url": _url(scan.annotated_image),
        "raw_result": scan.raw_result,
        "created_at": scan.created_at.isoformat(),
        "gate_pass": {
            "trip_id": gate.get("trip_id"),
            "fare_amount": gate.get("fare_amount"),
            "trip_status": gate.get("trip_status"),
            "paid": gate.get("paid"),
            "wallet_balance": gate.get("wallet_balance"),
            "gate_name": gate.get("gate_name"),
        }
        if gate
        else None,
    }
