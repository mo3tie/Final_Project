"""Ultralytics YOLO wrappers: vehicle crop + plate crop."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from ultralytics import YOLO

from . import config

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


def _clip_xyxy(x1: float, y1: float, x2: float, y2: float, w: int, h: int) -> tuple[int, int, int, int]:
    xi1 = int(max(0, min(w - 1, round(x1))))
    yi1 = int(max(0, min(h - 1, round(y1))))
    xi2 = int(max(0, min(w, round(x2))))
    yi2 = int(max(0, min(h, round(y2))))
    if xi2 <= xi1:
        xi2 = min(w, xi1 + 1)
    if yi2 <= yi1:
        yi2 = min(h, yi1 + 1)
    return xi1, yi1, xi2, yi2


def _expand_xyxy(x1: float, y1: float, x2: float, y2: float, frac: float, w: int, h: int) -> tuple[float, float, float, float]:
    bw = x2 - x1
    bh = y2 - y1
    pad_x = frac * bw
    pad_y = frac * bh
    return x1 - pad_x, y1 - pad_y, x2 + pad_x, y2 + pad_y


class CarDetector:
    def __init__(self, weights_path: str, device: str, half: bool = False) -> None:
        self._device = device
        self._half = bool(half and str(device).startswith("cuda"))
        self._model = YOLO(weights_path)
        self._model.to(device)

    @property
    def names(self) -> Any:
        return self._model.names

    def best_vehicle(
        self, rgb: np.ndarray, conf_thres: float
    ) -> tuple[str | None, tuple[int, int, int, int] | None, float]:
        """
        Highest-confidence detection (any class).
        Returns (vehicle_type, xyxy full image int, confidence).
        """
        h, w = rgb.shape[:2]
        r = self._model.predict(
            rgb, conf=conf_thres, verbose=False, device=self._device, half=self._half
        )[0]
        if r.boxes is None or len(r.boxes) == 0:
            return None, None, 0.0
        try:
            data = r.boxes.data.cpu().numpy()
        except Exception as e:
            log.warning("car boxes read failed: %s", e)
            return None, None, 0.0

        best_i = int(np.argmax(data[:, 4]))
        row = data[best_i]
        x1, y1, x2, y2, conf, cls = (float(row[j]) for j in range(6))
        cls_id = int(round(cls))
        label = _class_label(self._model.names, cls_id)
        x1e, y1e, x2e, y2e = _expand_xyxy(x1, y1, x2, y2, config.CROP_MARGIN_FRAC, w, h)
        xyxy = _clip_xyxy(x1e, y1e, x2e, y2e, w, h)
        log.debug("car pick cls=%s conf=%.3f xyxy=%s", label, conf, xyxy)
        return label, xyxy, float(conf)


class PlateDetector:
    def __init__(self, weights_path: str, device: str, half: bool = False) -> None:
        self._device = device
        self._half = bool(half and str(device).startswith("cuda"))
        self._model = YOLO(weights_path)
        self._model.to(device)

    def best_plate_in_crop(
        self, vehicle_rgb: np.ndarray, conf_thres: float
    ) -> tuple[tuple[int, int, int, int] | None, float]:
        """Best plate box in vehicle crop coordinates."""
        h, w = vehicle_rgb.shape[:2]
        r = self._model.predict(
            vehicle_rgb, conf=conf_thres, verbose=False, device=self._device, half=self._half
        )[0]
        if r.boxes is None or len(r.boxes) == 0:
            return None, 0.0
        try:
            data = r.boxes.data.cpu().numpy()
        except Exception as e:
            log.warning("plate boxes read failed: %s", e)
            return None, 0.0

        best_i = int(np.argmax(data[:, 4]))
        row = data[best_i]
        x1, y1, x2, y2, conf, _ = (float(row[j]) for j in range(6))
        x1e, y1e, x2e, y2e = _expand_xyxy(x1, y1, x2, y2, config.PLATE_CROP_MARGIN_FRAC, w, h)
        xyxy = _clip_xyxy(x1e, y1e, x2e, y2e, w, h)
        log.debug("plate conf=%.3f xyxy=%s", conf, xyxy)
        return xyxy, float(conf)


def crop_rgb(rgb: np.ndarray, xyxy: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = xyxy
    return rgb[y1:y2, x1:x2].copy()
