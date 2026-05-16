"""
Full Car + Plate + OCR pipeline for Django / API use (no Streamlit).
"""

from __future__ import annotations

import os
import threading
from typing import Any, Optional

import cv2
import numpy as np
from ultralytics import YOLO

from . import config

_lock = threading.Lock()
_models: tuple[YOLO, YOLO, YOLO] | None = None

MIN_PLATE_OCR_PX = 48


def _load_models() -> tuple[YOLO, YOLO, YOLO]:
    global _models
    with _lock:
        if _models is None:
            car_p = str(config.CAR_WEIGHTS)
            plate_p = str(config.PLATE_WEIGHTS)
            ocr_p = str(config.OCR_WEIGHTS)
            for p, label in ((car_p, "car"), (plate_p, "plate"), (ocr_p, "ocr")):
                if not os.path.isfile(p):
                    raise FileNotFoundError(f"Missing {label} weights: {p}")
            _models = (YOLO(car_p), YOLO(plate_p), YOLO(ocr_p))
        return _models


def _class_name(names: Any, cls_id: int) -> str:
    if isinstance(names, dict):
        if cls_id in names:
            return str(names[cls_id])
        sk = str(cls_id)
        if sk in names:
            return str(names[sk])
    if isinstance(names, (list, tuple)) and 0 <= cls_id < len(names):
        return str(names[cls_id])
    return str(cls_id)


def _parse_boxes(res, names, label_key: str) -> list[dict]:
    out: list[dict] = []
    if res.boxes is None or len(res.boxes) == 0:
        return out
    for b in res.boxes:
        cls_id = int(b.cls[0])
        confv = float(b.conf[0])
        x1, y1, x2, y2 = [float(v) for v in b.xyxy[0].tolist()]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        out.append(
            {
                label_key: _class_name(names, cls_id),
                "conf": round(confv, 4),
                "xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "center": [round(cx, 2), round(cy, 2)],
            }
        )
    return out


def _clip_xyxy(x1, y1, x2, y2, iw: int, ih: int) -> tuple[int, int, int, int]:
    xi1 = int(max(0, min(iw - 1, round(x1))))
    yi1 = int(max(0, min(ih - 1, round(y1))))
    xi2 = int(max(0, min(iw, round(x2))))
    yi2 = int(max(0, min(ih, round(y2))))
    if xi2 <= xi1:
        xi2 = min(iw, xi1 + 1)
    if yi2 <= yi1:
        yi2 = min(ih, yi1 + 1)
    return xi1, yi1, xi2, yi2


def _expand_xyxy(x1, y1, x2, y2, iw: int, ih: int, margin_frac: float) -> tuple[float, float, float, float]:
    w = x2 - x1
    h = y2 - y1
    mx = w * margin_frac
    my = h * margin_frac
    return (
        max(0, x1 - mx),
        max(0, y1 - my),
        min(iw, x2 + mx),
        min(ih, y2 + my),
    )


def _prepare_plate_crop(crop: np.ndarray) -> np.ndarray:
    if crop is None or crop.size == 0:
        return crop
    h, w = crop.shape[:2]
    if max(h, w) < MIN_PLATE_OCR_PX:
        scale = MIN_PLATE_OCR_PX / max(h, w)
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return crop


def _build_plate_text(dets: list, rtl: bool = True) -> str:
    if not dets:
        return ""
    ys = [d["center"][1] for d in dets]
    y_range = max(ys) - min(ys)
    two_lines = y_range > 25
    if not two_lines:
        ordered = sorted(dets, key=lambda d: d["center"][0], reverse=rtl)
    else:
        y_med = sorted(ys)[len(ys) // 2]
        top = [d for d in dets if d["center"][1] <= y_med]
        bottom = [d for d in dets if d["center"][1] > y_med]
        ordered = sorted(top, key=lambda d: d["center"][0], reverse=rtl) + sorted(
            bottom, key=lambda d: d["center"][0], reverse=rtl
        )
    return "".join(d.get("char", d.get("label", "")) for d in ordered)


def _ocr_on_crop(
    ocr_model: YOLO,
    crop: np.ndarray,
    *,
    imgsz: int,
    ocr_t: float,
    iou: float,
    rtl: bool,
) -> tuple[str, list[dict]]:
    crop = _prepare_plate_crop(crop)
    if crop is None or crop.size == 0 or min(crop.shape[:2]) < 4:
        return "", []

    ocr_res = ocr_model.predict(crop, imgsz=imgsz, conf=ocr_t, iou=iou, verbose=False)[0]
    ch_dets: list[dict] = []
    if ocr_res.boxes is not None:
        for b in ocr_res.boxes:
            cls_id = int(b.cls[0])
            x1c, y1c, x2c, y2c = [float(v) for v in b.xyxy[0].tolist()]
            cx, cy = (x1c + x2c) / 2, (y1c + y2c) / 2
            ch_dets.append(
                {
                    "char": _class_name(ocr_model.names, cls_id),
                    "conf": round(float(b.conf[0]), 4),
                    "center": [round(cx, 2), round(cy, 2)],
                }
            )
    return _build_plate_text(ch_dets, rtl=rtl), ch_dets


def _vehicle_for_plate(pd: dict, vehicle_dets: list[dict]) -> Optional[str]:
    if not vehicle_dets:
        return None
    pcx = (pd["xyxy"][0] + pd["xyxy"][2]) / 2
    pcy = (pd["xyxy"][1] + pd["xyxy"][3]) / 2
    for vd in vehicle_dets:
        vx1, vy1, vx2, vy2 = vd["xyxy"]
        if vx1 <= pcx <= vx2 and vy1 <= pcy <= vy2:
            return vd["vehicle_type"]
    return vehicle_dets[0]["vehicle_type"]


def analyze_image_bgr(
    image_bgr: np.ndarray,
    *,
    car_conf: float | None = None,
    plate_conf: float | None = None,
    ocr_conf: float | None = None,
    imgsz: int = 960,
    iou: float = 0.5,
    rtl: bool = True,
) -> dict[str, Any]:
    """Run 3-model pipeline; returns JSON-serializable result."""
    car_model, plate_model, ocr_model = _load_models()
    car_t = float(car_conf if car_conf is not None else config.CAR_CONF)
    plate_t = float(plate_conf if plate_conf is not None else config.PLATE_CONF)
    ocr_t = float(ocr_conf if ocr_conf is not None else config.OCR_CONF)

    ih, iw = image_bgr.shape[:2]

    car_res = car_model.predict(image_bgr, imgsz=imgsz, conf=car_t, iou=iou, verbose=False)[0]
    plate_res = plate_model.predict(image_bgr, imgsz=imgsz, conf=plate_t, iou=iou, verbose=False)[0]

    vehicle_dets = _parse_boxes(car_res, car_model.names, "vehicle_type")
    plate_dets = _parse_boxes(plate_res, plate_model.names, "class")

    if not plate_dets and plate_t > 0.05:
        plate_res = plate_model.predict(
            image_bgr, imgsz=imgsz, conf=max(0.05, plate_t * 0.5), iou=iou, verbose=False
        )[0]
        plate_dets = _parse_boxes(plate_res, plate_model.names, "class")

    plate_ocr_reads: list[dict] = []
    parts: list[str] = []
    margin = float(config.PLATE_CROP_MARGIN_FRAC)

    for i, pd in enumerate(plate_dets):
        x1, y1, x2, y2 = _expand_xyxy(*pd["xyxy"], iw, ih, margin)
        xi1, yi1, xi2, yi2 = _clip_xyxy(x1, y1, x2, y2, iw, ih)
        crop = image_bgr[yi1:yi2, xi1:xi2]
        plate_text, ch_dets = _ocr_on_crop(
            ocr_model, crop, imgsz=imgsz, ocr_t=ocr_t, iou=iou, rtl=rtl
        )
        if not plate_text and crop.size > 0:
            plate_text, ch_dets = _ocr_on_crop(
                ocr_model,
                crop,
                imgsz=min(1280, imgsz + 320),
                ocr_t=max(0.05, ocr_t * 0.7),
                iou=iou,
                rtl=rtl,
            )

        plate_ocr_reads.append(
            {
                "plate_index": i,
                "plate_text": plate_text,
                "vehicle_type": _vehicle_for_plate(pd, vehicle_dets),
                "n_chars": len(ch_dets),
            }
        )
        if plate_text:
            parts.append(plate_text)

    if not parts and vehicle_dets:
        vx1, vy1, vx2, vy2 = vehicle_dets[0]["xyxy"]
        xi1, yi1, xi2, yi2 = _clip_xyxy(vx1, vy1, vx2, vy2, iw, ih)
        car_crop = image_bgr[yi1:yi2, xi1:xi2]
        plate_text, ch_dets = _ocr_on_crop(
            ocr_model, car_crop, imgsz=imgsz, ocr_t=ocr_t, iou=iou, rtl=rtl
        )
        if plate_text:
            parts.append(plate_text)
            plate_ocr_reads.append(
                {
                    "plate_index": 0,
                    "plate_text": plate_text,
                    "vehicle_type": vehicle_dets[0]["vehicle_type"],
                    "n_chars": len(ch_dets),
                    "fallback": "vehicle_roi",
                }
            )

    if not parts:
        plate_text, ch_dets = _ocr_on_crop(
            ocr_model, image_bgr, imgsz=imgsz, ocr_t=max(0.05, ocr_t * 0.8), iou=iou, rtl=rtl
        )
        if plate_text:
            parts.append(plate_text)
            plate_ocr_reads.append(
                {
                    "plate_index": 0,
                    "plate_text": plate_text,
                    "vehicle_type": vehicle_dets[0]["vehicle_type"] if vehicle_dets else None,
                    "n_chars": len(ch_dets),
                    "fallback": "full_frame",
                }
            )

    vis = image_bgr.copy()
    for vd in vehicle_dets:
        x1, y1, x2, y2 = (int(v) for v in vd["xyxy"])
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 200, 0), 2)
    for pd in plate_dets:
        x1, y1, x2, y2 = (int(v) for v in pd["xyxy"])
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 165, 255), 2)

    primary_vehicle = vehicle_dets[0]["vehicle_type"] if vehicle_dets else None
    combined_plate = " | ".join(parts)

    return {
        "vehicle_type": primary_vehicle,
        "plate_text": combined_plate,
        "vehicle_detections": vehicle_dets,
        "plate_detections": plate_dets,
        "plate_ocr_reads": plate_ocr_reads,
        "annotated_bgr": vis,
    }
