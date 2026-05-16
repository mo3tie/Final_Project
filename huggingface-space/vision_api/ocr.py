"""Plate reading using the third YOLO checkpoint (best.pt) — ordered class labels."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from ultralytics import YOLO

log = logging.getLogger(__name__)


def _class_label(names: Any, cls_id: int) -> str:
    if not names:
        return str(cls_id)
    if isinstance(names, dict):
        if cls_id in names:
            return str(names[cls_id])
        sk = str(cls_id)
        if sk in names:
            return str(names[sk])
    return str(cls_id)


class PlateReader:
    """Runs YOLO on the plate crop; builds a string from left-to-right detections."""

    def __init__(self, weights_path: str, device: str, half: bool = False) -> None:
        self._device = device
        self._half = bool(half and str(device).startswith("cuda"))
        self._model = YOLO(weights_path)
        self._model.to(device)

    def read_text(self, plate_rgb: np.ndarray, conf_thres: float) -> tuple[str | None, float]:
        """
        Returns (assembled_text_or_none, mean_confidence_of_used_boxes).
        """
        if plate_rgb.size == 0 or min(plate_rgb.shape[:2]) < 4:
            return None, 0.0

        r = self._model.predict(
            plate_rgb, conf=conf_thres, verbose=False, device=self._device, half=self._half
        )[0]
        if r.boxes is None or len(r.boxes) == 0:
            log.debug("ocr yolo: no boxes")
            return None, 0.0

        try:
            data = r.boxes.data.cpu().numpy()
        except Exception as e:
            log.warning("ocr boxes read failed: %s", e)
            return None, 0.0

        rows: list[tuple[float, str, float]] = []
        for i in range(data.shape[0]):
            x1, y1, x2, y2, conf, cls = (float(data[i, j]) for j in range(6))
            cls_id = int(round(cls))
            label = _class_label(self._model.names, cls_id)
            cx = (x1 + x2) * 0.5
            rows.append((cx, label, float(conf)))

        rows.sort(key=lambda t: t[0])
        parts = [t[1] for t in rows]
        confs = [t[2] for t in rows]
        mean_conf = float(sum(confs) / max(1, len(confs)))

        if len(parts) == 1:
            text = parts[0].strip()
            log.debug("ocr single token: %s mean_conf=%.3f", text, mean_conf)
            return text or None, mean_conf

        if all(len(p.strip()) <= 1 for p in parts):
            joined = "".join(p.strip() for p in parts)
        else:
            joined = " ".join(p.strip() for p in parts if p.strip())

        log.debug("ocr assembled=%r mean_conf=%.3f", joined, mean_conf)
        return (joined if joined else None), mean_conf
