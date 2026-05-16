"""Read uploaded images reliably for the vision pipeline."""

from __future__ import annotations

import io
import logging

import cv2
import numpy as np

log = logging.getLogger(__name__)


def read_upload_bytes(uploaded_file) -> bytes:
    if uploaded_file is None:
        return b""
    try:
        if hasattr(uploaded_file, "read"):
            raw = uploaded_file.read()
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            return raw or b""
        if isinstance(uploaded_file, (bytes, bytearray)):
            return bytes(uploaded_file)
    except Exception as e:
        log.warning("read_upload_bytes failed: %s", e)
    return b""


def decode_bytes_to_bgr(raw: bytes) -> np.ndarray | None:
    if not raw:
        return None

    arr = np.frombuffer(raw, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is not None and bgr.size > 0:
        return bgr

    try:
        from PIL import Image

        pil = Image.open(io.BytesIO(raw))
        pil.load()
        if pil.mode != "RGB":
            pil = pil.convert("RGB")
        rgb = np.asarray(pil)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as e:
        log.warning("PIL decode failed: %s", e)
        return None
