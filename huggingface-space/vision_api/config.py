"""Paths, device, and thresholds (env overridable)."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
HF_SPACE_ROOT = PACKAGE_DIR.parent
MODELS_DIR = Path(os.environ.get("VISION_MODELS_DIR", str(HF_SPACE_ROOT / "models"))).resolve()

CAR_WEIGHTS = MODELS_DIR / "yolo8_last_version_car(must).pt"
PLATE_WEIGHTS = MODELS_DIR / "plattes_detect_model.pt"
OCR_WEIGHTS = MODELS_DIR / "best.pt"

CAR_CONF = float(os.environ.get("CAR_CONF", "0.25"))
PLATE_CONF = float(os.environ.get("PLATE_CONF", "0.2"))
OCR_CONF = float(os.environ.get("OCR_CONF", "0.15"))

CROP_MARGIN_FRAC = float(os.environ.get("CROP_MARGIN_FRAC", "0.08"))
PLATE_CROP_MARGIN_FRAC = float(os.environ.get("PLATE_CROP_MARGIN_FRAC", "0.12"))

USE_FP16 = os.environ.get("USE_FP16", "1").lower() not in ("0", "false", "no")
