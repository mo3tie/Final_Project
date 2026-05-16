"""Orchestrate car → plate crop → OCR YOLO."""

from __future__ import annotations

import logging

import numpy as np

from . import config
from .detector import CarDetector, PlateDetector, crop_rgb
from .ocr import PlateReader

log = logging.getLogger(__name__)


class VisionPipeline:
    def __init__(self, car: CarDetector, plate: PlateDetector, reader: PlateReader) -> None:
        self._car = car
        self._plate = plate
        self._reader = reader

    def predict(self, rgb: np.ndarray) -> dict[str, str | None]:
        """
        Returns exactly {"vehicle_type": str|None, "plate_text": str|None}.
        Confidence is logged only at DEBUG.
        """
        if rgb is None or rgb.size == 0:
            log.debug("empty image")
            return {"vehicle_type": None, "plate_text": None}

        vtype, car_xyxy, car_conf = self._car.best_vehicle(rgb, config.CAR_CONF)
        if vtype is None or car_xyxy is None:
            log.debug("no vehicle car_conf=%.4f", car_conf)
            return {"vehicle_type": None, "plate_text": None}

        vehicle = crop_rgb(rgb, car_xyxy)
        plate_xyxy, plate_conf = self._plate.best_plate_in_crop(vehicle, config.PLATE_CONF)
        if plate_xyxy is None:
            log.debug("no plate plate_conf=%.4f vehicle=%s", plate_conf, vtype)
            return {"vehicle_type": vtype, "plate_text": None}

        plate_img = crop_rgb(vehicle, plate_xyxy)
        text, ocr_conf = self._reader.read_text(plate_img, config.OCR_CONF)
        log.debug(
            "pipeline ok vehicle=%s car_conf=%.3f plate_conf=%.3f ocr_conf=%.3f text=%r",
            vtype,
            car_conf,
            plate_conf,
            ocr_conf,
            text,
        )
        return {"vehicle_type": vtype, "plate_text": text}
