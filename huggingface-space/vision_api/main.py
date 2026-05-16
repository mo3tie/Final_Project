"""
FastAPI: POST /predict → {"vehicle_type": "...", "plate_text": "..."|null}
"""

from __future__ import annotations

import io
import logging
import os
from contextlib import asynccontextmanager

import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from . import config
from .detector import CarDetector, PlateDetector
from .ocr import PlateReader
from .pipeline import VisionPipeline

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("vision_api")

_pipeline: VisionPipeline | None = None


def _device() -> str:
    if os.environ.get("FORCE_CPU", "").lower() in ("1", "true", "yes"):
        return "cpu"
    if torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def _load_rgb_from_upload(raw: bytes) -> np.ndarray | None:
    try:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        return np.asarray(im)
    except Exception as e:
        log.warning("image decode failed: %s", e)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline
    device = _device()
    log.info("device=%s", device)
    missing = [p for p in (config.CAR_WEIGHTS, config.PLATE_WEIGHTS, config.OCR_WEIGHTS) if not p.is_file()]
    if missing:
        for p in missing:
            log.error("missing weights: %s", p)
        _pipeline = None
    else:
        half = bool(device.startswith("cuda") and config.USE_FP16)
        car = CarDetector(str(config.CAR_WEIGHTS), device, half=half)
        plate = PlateDetector(str(config.PLATE_WEIGHTS), device, half=half)
        reader = PlateReader(str(config.OCR_WEIGHTS), device, half=half)
        _pipeline = VisionPipeline(car, plate, reader)
        log.info("models loaded car=%s plate=%s ocr=%s", config.CAR_WEIGHTS.name, config.PLATE_WEIGHTS.name, config.OCR_WEIGHTS.name)
    yield
    _pipeline = None


app = FastAPI(title="Vision pipeline API", lifespan=lifespan)


def _json_body(vehicle_type: str | None, plate_text: str | None) -> dict:
    return {"vehicle_type": vehicle_type, "plate_text": plate_text}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if _pipeline is None:
        return JSONResponse(_json_body(None, None), status_code=503)

    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(_json_body(None, None), status_code=400)

    raw = await file.read()
    if not raw:
        return JSONResponse(_json_body(None, None), status_code=400)

    rgb = _load_rgb_from_upload(raw)
    if rgb is None:
        return JSONResponse(_json_body(None, None), status_code=400)

    try:
        out = _pipeline.predict(rgb)
    except Exception as e:
        log.exception("predict failed: %s", e)
        return JSONResponse(_json_body(None, None), status_code=500)

    return JSONResponse(out)
