import os
import json
import time
import random
from typing import Optional

import numpy as np
import streamlit as st
import cv2
from ultralytics import YOLO

# =========================================================
# STREAMLIT PAGE
# =========================================================

st.set_page_config(
    page_title="Plate Reader (YOLO)",
    layout="wide"
)

st.title("📷 Plate Character Reader (Images → Boxes → String → JSON)")

# =========================================================
# MODEL PATHS (car weights: your checkpoint + ./models fallback)
# =========================================================

_APP_ROOT = os.path.dirname(os.path.abspath(__file__))


def _resolve_car_weights() -> str:
    """
    Resolve yolo8_last_version_car(must).pt.
    Prefer ./models beside this file (Docker / Hugging Face Spaces).
    """
    rel = os.path.join(_APP_ROOT, "models", "yolo8_last_version_car(must).pt")
    for p in (rel,):
        if os.path.isfile(p):
            return os.path.abspath(p)
    return os.path.abspath(rel)


def _resolve_plate_weights() -> str:
    rel = os.path.join(_APP_ROOT, "models", "plattes_detect_model.pt")
    for p in (rel,):
        if os.path.isfile(p):
            return os.path.abspath(p)
    return os.path.abspath(rel)


def _resolve_ocr_weights() -> str:
    rel = os.path.join(_APP_ROOT, "models", "best.pt")
    for p in (rel,):
        if os.path.isfile(p):
            return os.path.abspath(p)
    return os.path.abspath(rel)


CAR_MODEL_PATH = _resolve_car_weights()
PLATE_MODEL_PATH = _resolve_plate_weights()
OCR_MODEL_PATH = _resolve_ocr_weights()

DEFAULT_MODEL = OCR_MODEL_PATH


def _class_name(names, cls_id: int) -> str:
    """Resolve Ultralytics `model.names` to a string label (vehicle type / plate / char)."""
    if isinstance(names, dict):
        if cls_id in names:
            return str(names[cls_id])
        sk = str(cls_id)
        if sk in names:
            return str(names[sk])
    if isinstance(names, (list, tuple)) and 0 <= cls_id < len(names):
        return str(names[cls_id])
    return str(cls_id)


def _names_values(names) -> list[str]:
    if isinstance(names, dict):
        return [str(v) for v in names.values()]
    if isinstance(names, (list, tuple)):
        return [str(x) for x in names]
    return []


# =========================================================
# LOAD MODEL
# =========================================================

@st.cache_resource
def load_model(path: str):
    return YOLO(path)


@st.cache_resource
def load_car_plate_ocr_models(car_weights: str, plate_weights: str, ocr_weights: str):
    """Car + plate detectors + OCR character YOLO. Paths are cache keys."""
    return YOLO(car_weights), YOLO(plate_weights), YOLO(ocr_weights)

# =========================================================
# BUILD PLATE TEXT
# =========================================================

def build_plate_text(dets, rtl=False, y_line_threshold=25):

    if not dets:
        return "", [], {"two_lines": False, "y_range": 0.0}

    ys = [d["center"][1] for d in dets]

    y_min = min(ys)
    y_max = max(ys)

    y_range = y_max - y_min

    two_lines = y_range > y_line_threshold

    ordered = []

    if not two_lines:

        ordered = sorted(
            dets,
            key=lambda d: d["center"][0],
            reverse=rtl
        )

    else:

        ys_sorted = sorted(ys)
        y_med = ys_sorted[len(ys_sorted) // 2]

        top = [
            d for d in dets
            if d["center"][1] <= y_med
        ]

        bottom = [
            d for d in dets
            if d["center"][1] > y_med
        ]

        top_sorted = sorted(
            top,
            key=lambda d: d["center"][0],
            reverse=rtl
        )

        bottom_sorted = sorted(
            bottom,
            key=lambda d: d["center"][0],
            reverse=rtl
        )

        ordered = top_sorted + bottom_sorted

    text = "".join([d["char"] for d in ordered])

    meta = {
        "two_lines": two_lines,
        "y_range": float(y_range)
    }

    return text, ordered, meta

# =========================================================
# PREDICT + DRAW
# =========================================================

def predict_and_annotate(
    model,
    image_bgr,
    imgsz: int,
    conf: float,
    iou: float,
    rtl: bool,
    y_line_threshold: int
):

    res = model.predict(
        image_bgr,
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        verbose=False
    )[0]

    names = model.names

    dets = []

    if res.boxes is not None and len(res.boxes) > 0:

        for b in res.boxes:

            cls_id = int(b.cls[0])

            confv = float(b.conf[0])

            x1, y1, x2, y2 = [
                float(v)
                for v in b.xyxy[0].tolist()
            ]

            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            label = _class_name(names, cls_id)

            dets.append({
                "char": label,
                "vehicle_type": label,
                "conf": round(confv, 4),
                "xyxy": [
                    round(x1, 2),
                    round(y1, 2),
                    round(x2, 2),
                    round(y2, 2)
                ],
                "center": [
                    round(cx, 2),
                    round(cy, 2)
                ]
            })

    plate_text, ordered_dets, sort_meta = build_plate_text(
        dets,
        rtl=rtl,
        y_line_threshold=y_line_threshold
    )

    annotated_bgr = res.plot()

    annotated_rgb = cv2.cvtColor(
        annotated_bgr,
        cv2.COLOR_BGR2RGB
    )

    return (
        plate_text,
        dets,
        ordered_dets,
        sort_meta,
        annotated_rgb
    )


def _clip_xyxy_int(
    x1: float, y1: float, x2: float, y2: float, w: int, h: int
) -> tuple[int, int, int, int]:
    xi1 = int(max(0, min(w - 1, round(x1))))
    yi1 = int(max(0, min(h - 1, round(y1))))
    xi2 = int(max(0, min(w, round(x2))))
    yi2 = int(max(0, min(h, round(y2))))
    if xi2 <= xi1:
        xi2 = min(w, xi1 + 1)
    if yi2 <= yi1:
        yi2 = min(h, yi1 + 1)
    return xi1, yi1, xi2, yi2


def _bbox_iou(
    ax1: float,
    ay1: float,
    ax2: float,
    ay2: float,
    bx1: float,
    by1: float,
    bx2: float,
    by2: float,
) -> float:
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return float(inter / union) if union > 0 else 0.0


def _assign_vehicle_to_plate(
    plate_xyxy: list[float],
    vehicle_dets: list,
) -> Optional[dict]:
    """
    Pick the vehicle box that owns this plate: plate center inside vehicle,
    else highest IoU with plate, else nearest vehicle center.
    """
    if not vehicle_dets:
        return None

    px1, py1, px2, py2 = plate_xyxy
    pcx = (px1 + px2) * 0.5
    pcy = (py1 + py2) * 0.5

    inside: list[tuple[int, dict, float]] = []
    for j, vd in enumerate(vehicle_dets):
        x1, y1, x2, y2 = vd["xyxy"]
        if x1 <= pcx <= x2 and y1 <= pcy <= y2:
            inside.append((j, vd, float(vd["conf"])))

    if inside:
        j, vd, _ = max(inside, key=lambda t: t[2])
    else:
        best_j: Optional[int] = None
        best_vd: Optional[dict] = None
        best_iou = 0.0
        for j, vd in enumerate(vehicle_dets):
            x1, y1, x2, y2 = vd["xyxy"]
            iou = _bbox_iou(px1, py1, px2, py2, x1, y1, x2, y2)
            if iou > best_iou:
                best_iou = iou
                best_j = j
                best_vd = vd
        if best_j is not None and best_vd is not None and best_iou >= 0.001:
            j, vd = best_j, best_vd
        else:
            best_d: Optional[float] = None
            j, vd = 0, vehicle_dets[0]
            for jj, vdd in enumerate(vehicle_dets):
                x1, y1, x2, y2 = vdd["xyxy"]
                vcx = (x1 + x2) * 0.5
                vcy = (y1 + y2) * 0.5
                d = (pcx - vcx) ** 2 + (pcy - vcy) ** 2
                if best_d is None or d < best_d:
                    best_d = d
                    j, vd = jj, vdd

    return {
        "vehicle_index": j,
        "vehicle_type": vd["vehicle_type"],
        "vehicle_conf": vd["conf"],
        "vehicle_xyxy": [round(float(x), 2) for x in vd["xyxy"]],
    }


def ocr_plate_crop(
    ocr_model,
    crop_bgr,
    imgsz: int,
    ocr_conf: float,
    iou: float,
    rtl: bool,
    y_line_threshold: int,
):
    """Run character YOLO on a BGR plate crop; same ordering rules as full-image OCR tab."""
    if crop_bgr is None or crop_bgr.size == 0:
        return "", [], {"two_lines": False, "y_range": 0.0}, []

    h, w = crop_bgr.shape[:2]
    if h < 4 or w < 4:
        return "", [], {"two_lines": False, "y_range": 0.0}, []

    res = ocr_model.predict(
        crop_bgr,
        imgsz=imgsz,
        conf=ocr_conf,
        iou=iou,
        verbose=False,
    )[0]

    names = ocr_model.names
    dets = []

    if res.boxes is not None and len(res.boxes) > 0:

        for b in res.boxes:

            cls_id = int(b.cls[0])
            confv = float(b.conf[0])
            x1, y1, x2, y2 = [float(v) for v in b.xyxy[0].tolist()]
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            label = _class_name(names, cls_id)

            dets.append(
                {
                    "char": label,
                    "conf": round(confv, 4),
                    "xyxy": [
                        round(x1, 2),
                        round(y1, 2),
                        round(x2, 2),
                        round(y2, 2),
                    ],
                    "center": [round(cx, 2), round(cy, 2)],
                }
            )

    plate_text, ordered_dets, sort_meta = build_plate_text(
        dets,
        rtl=rtl,
        y_line_threshold=y_line_threshold,
    )

    return plate_text, ordered_dets, sort_meta, dets


def _draw_plate_ocr_labels(canvas_bgr, plate_ocr_reads: list):
    """Draw OCR strings under each plate box (BGR)."""
    h, w = canvas_bgr.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    for read in plate_ocr_reads:
        x1, y1, x2, y2 = (float(v) for v in read["plate_xyxy"])
        xi1, yi1, xi2, yi2 = _clip_xyxy_int(x1, y1, x2, y2, w, h)
        raw = read.get("plate_text") or ""
        vt = read.get("vehicle_type")
        prefix = f"{vt} · " if vt else ""
        line = prefix + raw
        txt = line if len(line) <= 40 else line[:37] + "..."
        if not raw.strip() and not vt:
            txt = "(no OCR)"
        elif not raw.strip() and vt:
            txt = f"{vt} · (no OCR)"
        fs = max(0.35, min(h, w) / 2200.0)
        thk = max(1, min(h, w) // 900)
        (tw, th), _ = cv2.getTextSize(txt, font, fs, thk)
        bx1 = max(0, xi1)
        by2 = min(h - 1, yi2 + 6 + th)
        by1 = max(0, by2 - th - 8)
        bx2 = min(w - 1, max(bx1 + 1, bx1 + tw + 8))
        cv2.rectangle(canvas_bgr, (bx1, by1), (bx2, by2), (40, 40, 40), -1)
        cv2.putText(
            canvas_bgr,
            txt,
            (bx1 + 4, by2 - 4),
            font,
            fs,
            (255, 255, 200),
            thk,
            cv2.LINE_AA,
        )


def _detections_from_result(res, names, label_field: str):
    """Parse Ultralytics result into a list of dicts with a human-readable label field."""
    out = []
    if res.boxes is None or len(res.boxes) == 0:
        return out
    for b in res.boxes:
        cls_id = int(b.cls[0])
        confv = float(b.conf[0])
        x1, y1, x2, y2 = [float(v) for v in b.xyxy[0].tolist()]
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        label = _class_name(names, cls_id)
        row = {
            label_field: label,
            "conf": round(confv, 4),
            "xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            "center": [round(cx, 2), round(cy, 2)],
        }
        out.append(row)
    return out


def _draw_labelled_boxes(
    image_bgr,
    dets,
    label_key: str,
    color_bgr,
    prefix: str,
):
    """Draw rectangles and short labels on a BGR image (mutates a copy)."""
    canvas = image_bgr.copy()
    h, w = canvas.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(1, min(h, w) // 600)
    for d in dets:
        x1, y1, x2, y2 = (int(round(v)) for v in d["xyxy"])
        x1 = max(0, min(w - 1, x1))
        x2 = max(0, min(w, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(0, min(h, y2))
        if x2 <= x1:
            x2 = min(w, x1 + 1)
        if y2 <= y1:
            y2 = min(h, y1 + 1)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color_bgr, 2 + thickness)
        name = str(d.get(label_key, ""))
        txt = f"{prefix}{name} {d['conf']:.2f}"
        (tw, th), _ = cv2.getTextSize(txt, font, 0.5 + 0.2 * thickness, 1 + thickness)
        ty = max(y1 - 4, th + 4)
        cv2.rectangle(canvas, (x1, ty - th - 4), (x1 + tw + 4, ty), color_bgr, -1)
        cv2.putText(
            canvas,
            txt,
            (x1 + 2, ty - 2),
            font,
            0.5 + 0.2 * thickness,
            (255, 255, 255),
            1 + thickness,
            cv2.LINE_AA,
        )
    return canvas


def predict_car_and_plates(
    car_model,
    plate_model,
    image_bgr,
    imgsz: int,
    conf: float,
    iou: float,
    *,
    car_conf: Optional[float] = None,
    plate_conf: Optional[float] = None,
    ocr_model=None,
    ocr_conf: Optional[float] = None,
    rtl: bool = False,
    y_line_threshold: int = 25,
):
    """
    Full-image car (class = vehicle type) + plate boxes; optional OCR YOLO on each plate crop.
    Each plate OCR row includes the matched vehicle_type (geometry: center in box, else IoU, else nearest).
    """
    car_t = float(conf if car_conf is None else car_conf)
    plate_t = float(conf if plate_conf is None else plate_conf)

    car_res = car_model.predict(
        image_bgr,
        imgsz=imgsz,
        conf=car_t,
        iou=iou,
        verbose=False,
    )[0]
    plate_res = plate_model.predict(
        image_bgr,
        imgsz=imgsz,
        conf=plate_t,
        iou=iou,
        verbose=False,
    )[0]

    vehicle_dets = _detections_from_result(
        car_res, car_model.names, label_field="vehicle_type"
    )
    plate_dets = _detections_from_result(
        plate_res, plate_model.names, label_field="class"
    )

    plate_ocr_reads: list = []
    combined_plate_text = ""

    if ocr_model is not None and len(plate_dets) > 0:

        ocr_t = float(conf if ocr_conf is None else ocr_conf)
        ih, iw = image_bgr.shape[:2]
        parts: list[str] = []

        for i, pd in enumerate(plate_dets):

            x1, y1, x2, y2 = pd["xyxy"]
            xi1, yi1, xi2, yi2 = _clip_xyxy_int(x1, y1, x2, y2, iw, ih)
            crop = image_bgr[yi1:yi2, xi1:xi2]

            pt, ordered, smeta, ch_dets = ocr_plate_crop(
                ocr_model,
                crop,
                imgsz,
                ocr_t,
                iou,
                rtl,
                y_line_threshold,
            )

            vm = _assign_vehicle_to_plate(
                [float(v) for v in pd["xyxy"]],
                vehicle_dets,
            )

            row = {
                "plate_index": i,
                "plate_xyxy": [round(v, 2) for v in pd["xyxy"]],
                "plate_text": pt,
                "sort_meta": smeta,
                "n_chars": len(ch_dets),
                "ordered_chars": ordered,
            }
            if vm:
                row.update(vm)
            else:
                row["vehicle_index"] = None
                row["vehicle_type"] = None
                row["vehicle_conf"] = None
                row["vehicle_xyxy"] = None

            plate_ocr_reads.append(row)

            if pt:

                parts.append(pt)

        combined_plate_text = " | ".join(parts)

    # Cars: green BGR; plates: orange BGR
    vis = _draw_labelled_boxes(
        image_bgr, vehicle_dets, "vehicle_type", (0, 200, 0), "car: "
    )
    vis = _draw_labelled_boxes(vis, plate_dets, "class", (0, 165, 255), "plate: ")

    if plate_ocr_reads:

        _draw_plate_ocr_labels(vis, plate_ocr_reads)

    annotated_rgb = cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)
    sort_meta = {"two_lines": False, "y_range": 0.0}

    return {
        "plate_text": combined_plate_text,
        "dets": [],
        "ordered_dets": [],
        "sort_meta": sort_meta,
        "annotated_rgb": annotated_rgb,
        "vehicle_detections": vehicle_dets,
        "plate_detections": plate_dets,
        "plate_ocr_reads": plate_ocr_reads,
    }


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("Settings")

    # =============================
    # MODEL SELECTOR
    # =============================

    model_choice = st.selectbox(
        "Choose model",
        [
            "OCR Characters Model",
            "Plate Detection Model",
            "Car Detection Model",
            "Car + Plate + OCR (3 models)",
        ],
        help=(
            "Car YOLO: vehicle type (bus / car / truck / z-minibus). "
            "Plate YOLO: plate boxes. OCR YOLO: characters per plate crop. "
            "Each plate row is linked to the best-matching vehicle box."
        ),
    )

    triple_mode = model_choice == "Car + Plate + OCR (3 models)"
    car_only = model_choice == "Car Detection Model"

    if model_choice == "OCR Characters Model":
        model_path = OCR_MODEL_PATH

    elif model_choice == "Plate Detection Model":
        model_path = PLATE_MODEL_PATH

    elif triple_mode:
        model_path = (
            f"{CAR_MODEL_PATH}\n+\n{PLATE_MODEL_PATH}\n+\n{OCR_MODEL_PATH}"
        )

    else:
        model_path = CAR_MODEL_PATH

    st.success(f"Using model:\n{model_path}")

    # =============================
    # INFERENCE
    # =============================

    st.subheader("Inference")

    imgsz = st.slider(
        "imgsz",
        320,
        1280,
        960,
        step=32
    )

    conf = st.slider(
        "conf",
        0.01,
        0.90,
        0.20,
        step=0.01
    )

    iou = st.slider(
        "iou",
        0.10,
        0.90,
        0.50,
        step=0.05
    )

    if triple_mode or car_only:

        car_conf = st.slider(
            "Car model confidence",
            0.01,
            0.90,
            0.12,
            step=0.01,
            help=(
                f"Confidence threshold for `{os.path.basename(CAR_MODEL_PATH)}`. "
                "Lower this if vehicles are missing. "
                "Vehicle type is the class name from this model."
            ),
        )

    else:

        car_conf = conf

    if triple_mode:

        plate_conf = st.slider(
            "Plate model confidence",
            0.01,
            0.90,
            0.20,
            step=0.01,
            help="Threshold for the plate-box model (full image).",
        )

        ocr_conf = st.slider(
            "OCR model confidence",
            0.01,
            0.90,
            0.15,
            step=0.01,
            help=(
                f"Character YOLO on each plate crop (`{os.path.basename(OCR_MODEL_PATH)}`)."
            ),
        )

    else:

        plate_conf = conf
        ocr_conf = conf

    # =============================
    # READING ORDER
    # =============================

    st.subheader("Reading order")

    rtl = st.checkbox(
        "Arabic RTL (right-to-left)",
        value=False
    )

    y_line_threshold = st.slider(
        "Two-line Y threshold",
        5,
        120,
        25,
        step=1
    )

    show_table = st.checkbox(
        "Show detections table",
        value=True
    )

    show_sort_debug = st.checkbox(
        "Show sorting debug",
        value=False
    )

# =========================================================
# CHECK MODEL
# =========================================================

if triple_mode:

    if not os.path.exists(CAR_MODEL_PATH):

        st.error(f"Car model not found:\n{CAR_MODEL_PATH}")
        st.stop()

    if not os.path.exists(PLATE_MODEL_PATH):

        st.error(f"Plate model not found:\n{PLATE_MODEL_PATH}")
        st.stop()

    if not os.path.exists(OCR_MODEL_PATH):

        st.error(f"OCR model not found:\n{OCR_MODEL_PATH}")
        st.stop()

else:

    if not os.path.exists(model_path):

        st.error(f"Model not found:\n{model_path}")
        st.stop()

# =========================================================
# LOAD MODEL
# =========================================================

try:

    if triple_mode:

        car_model, plate_model, ocr_model = load_car_plate_ocr_models(
            CAR_MODEL_PATH,
            PLATE_MODEL_PATH,
            OCR_MODEL_PATH,
        )
        model = None

    else:

        car_model, plate_model, ocr_model = None, None, None
        model = load_model(model_path)

except Exception as e:

    st.error("Failed to load model.")
    st.exception(e)
    st.stop()

st.success("Model loaded successfully ✅")

if triple_mode or car_only:

    _car_for_classes = car_model if triple_mode else model
    _cls = ", ".join(_names_values(_car_for_classes.names)) or "(no class names in checkpoint)"
    _ocr_extra = ""
    if triple_mode:
        _ocr_labels = ", ".join(_names_values(ocr_model.names)) or "—"
        _ocr_extra = (
            f"\n\n**OCR checkpoint:** `{OCR_MODEL_PATH}`\n\n"
            f"**OCR classes (chars/tokens):** {_ocr_labels}"
        )
    st.sidebar.info(
        f"**Car checkpoint:** `{CAR_MODEL_PATH}`\n\n"
        f"**Type labels (classes):** {_cls}"
        f"{_ocr_extra}"
    )

# =========================================================
# TABS
# =========================================================

tab1, tab2 = st.tabs([
    "Upload images",
    "Random 10 from folder"
])

# =========================================================
# TAB 1
# =========================================================

with tab1:

    st.subheader("Upload one or multiple images")

    files = st.file_uploader(
        "Choose images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if files:

        out_json = []

        for f in files:

            img_bytes = f.read()

            img_bgr = cv2.imdecode(
                np.frombuffer(img_bytes, np.uint8),
                cv2.IMREAD_COLOR
            )

            if img_bgr is None:
                st.error(f"Could not read image: {f.name}")
                continue

            if triple_mode:

                merged = predict_car_and_plates(
                    car_model,
                    plate_model,
                    img_bgr,
                    imgsz,
                    conf,
                    iou,
                    car_conf=car_conf,
                    plate_conf=plate_conf,
                    ocr_model=ocr_model,
                    ocr_conf=ocr_conf,
                    rtl=rtl,
                    y_line_threshold=y_line_threshold,
                )
                plate_text = merged["plate_text"]
                dets = merged["dets"]
                ordered_dets = merged["ordered_dets"]
                sort_meta = merged["sort_meta"]
                annotated_rgb = merged["annotated_rgb"]
                vehicle_detections = merged["vehicle_detections"]
                plate_detections = merged["plate_detections"]
                plate_ocr_reads = merged["plate_ocr_reads"]

            else:

                plate_ocr_reads = []

                infer_conf = car_conf if car_only else conf

                (
                    plate_text,
                    dets,
                    ordered_dets,
                    sort_meta,
                    annotated_rgb,
                ) = predict_and_annotate(
                    model,
                    img_bgr,
                    imgsz,
                    infer_conf,
                    iou,
                    rtl,
                    y_line_threshold,
                )
                vehicle_detections = []
                plate_detections = []

            c1, c2 = st.columns([2, 1])

            with c1:

                st.image(
                    annotated_rgb,
                    caption=f.name,
                    use_container_width=True
                )

            with c2:

                if triple_mode:

                    types_unique = sorted(
                        {str(d["vehicle_type"]) for d in vehicle_detections}
                    )
                    st.markdown(
                        f"**Vehicles:** {len(vehicle_detections)} — "
                        f"`{', '.join(types_unique) if types_unique else '—'}`"
                    )
                    st.markdown(
                        f"**Plate regions:** {len(plate_detections)}"
                    )
                    st.markdown(
                        f"**Plate text (OCR):** `{plate_text if plate_text else '—'}`"
                    )
                    if plate_ocr_reads:
                        linked_types = sorted(
                            {
                                str(r["vehicle_type"])
                                for r in plate_ocr_reads
                                if r.get("vehicle_type")
                            }
                        )
                        st.markdown(
                            "**Vehicle type (matched to each plate):** "
                            f"`{', '.join(linked_types) if linked_types else '—'}`"
                        )
                    st.caption(
                        "Each plate is assigned to a vehicle by center-in-box, "
                        "else overlap, else nearest vehicle. "
                        "OCR uses `best.pt` and the Reading order settings above."
                    )

                else:

                    st.markdown(
                        f"**Plate text:** `{plate_text if plate_text else '—'}`"
                    )
                    st.markdown(
                        f"**Detections:** {len(dets)}"
                    )

                if show_sort_debug and not triple_mode and not car_only:

                    st.write("Sorting:", sort_meta)

                if show_table:

                    if triple_mode or car_only:

                        if vehicle_detections:

                            st.markdown("**Vehicles**")

                            st.dataframe(
                                vehicle_detections,
                                use_container_width=True
                            )

                        if plate_detections:

                            st.markdown("**Plate regions**")

                            st.dataframe(
                                plate_detections,
                                use_container_width=True
                            )

                        if plate_ocr_reads:

                            st.markdown("**OCR per plate**")

                            st.dataframe(
                                [
                                    {
                                        "plate_index": r["plate_index"],
                                        "vehicle_type": r.get("vehicle_type"),
                                        "vehicle_conf": r.get("vehicle_conf"),
                                        "plate_text": r["plate_text"],
                                        "n_chars": r["n_chars"],
                                    }
                                    for r in plate_ocr_reads
                                ],
                                use_container_width=True,
                            )

                            if show_sort_debug:

                                for r in plate_ocr_reads:

                                    st.write(
                                        f"Plate {r['plate_index']} sort:",
                                        r["sort_meta"],
                                    )

                        if (
                            not vehicle_detections
                            and not plate_detections
                        ):

                            st.info(
                                "No vehicles or plates above the confidence threshold."
                            )

                    elif len(dets) > 0:

                        hdr = (
                            "**Detections (reading order):**"
                            if not car_only
                            else "**Detections (per box, vehicle_type):**"
                        )
                        st.markdown(hdr)

                        st.dataframe(
                            ordered_dets,
                            use_container_width=True
                        )

            record = {

                "image_name": f.name,
                "plate_text": plate_text,
                "rtl": rtl,
                "y_line_threshold": y_line_threshold,
                "sort_meta": sort_meta,

            }

            if triple_mode:

                record["vehicle_detections"] = vehicle_detections
                record["plate_detections"] = plate_detections
                record["plate_ocr_reads"] = plate_ocr_reads
                record["n_vehicles"] = len(vehicle_detections)
                record["n_plates"] = len(plate_detections)
                record["car_model_path"] = CAR_MODEL_PATH
                record["ocr_model_path"] = OCR_MODEL_PATH

            else:

                record["n"] = len(dets)
                record["detections"] = dets
                record["ordered_detections"] = ordered_dets
                if car_only:
                    record["car_model_path"] = CAR_MODEL_PATH

            out_json.append(record)

            st.divider()

        ts = int(time.time())

        st.download_button(
            "Download JSON for uploaded images",
            data=json.dumps(
                out_json,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8"),
            file_name=f"uploaded_results_{ts}.json",
            mime="application/json"
        )

# =========================================================
# TAB 2
# =========================================================

with tab2:

    st.subheader("Pick random images from a local folder")

    folder = st.text_input(
        "Folder path",
        value=r"C:\Users\Mahmoud Magdy\Downloads"
    )

    n = st.number_input(
        "How many random images?",
        min_value=1,
        max_value=50,
        value=10,
        step=1
    )

    if st.button("Run random demo"):

        if not os.path.isdir(folder):

            st.error("Folder not found.")
            st.stop()

        exts = (
            ".jpg",
            ".jpeg",
            ".png",
            ".JPG",
            ".JPEG",
            ".PNG"
        )

        all_imgs = []

        for root, _, files in os.walk(folder):

            for fn in files:

                if fn.endswith(exts):

                    all_imgs.append(
                        os.path.join(root, fn)
                    )

        if not all_imgs:

            st.error("No images found in that folder.")
            st.stop()

        sample = random.sample(
            all_imgs,
            k=min(int(n), len(all_imgs))
        )

        out_json = []

        for p in sample:

            img_bgr = cv2.imread(p)

            if img_bgr is None:
                continue

            if triple_mode:

                merged = predict_car_and_plates(
                    car_model,
                    plate_model,
                    img_bgr,
                    imgsz,
                    conf,
                    iou,
                    car_conf=car_conf,
                    plate_conf=plate_conf,
                    ocr_model=ocr_model,
                    ocr_conf=ocr_conf,
                    rtl=rtl,
                    y_line_threshold=y_line_threshold,
                )
                plate_text = merged["plate_text"]
                dets = merged["dets"]
                ordered_dets = merged["ordered_dets"]
                sort_meta = merged["sort_meta"]
                annotated_rgb = merged["annotated_rgb"]
                vehicle_detections = merged["vehicle_detections"]
                plate_detections = merged["plate_detections"]
                plate_ocr_reads = merged["plate_ocr_reads"]

            else:

                plate_ocr_reads = []

                infer_conf = car_conf if car_only else conf

                (
                    plate_text,
                    dets,
                    ordered_dets,
                    sort_meta,
                    annotated_rgb,
                ) = predict_and_annotate(
                    model,
                    img_bgr,
                    imgsz,
                    infer_conf,
                    iou,
                    rtl,
                    y_line_threshold,
                )
                vehicle_detections = []
                plate_detections = []

            st.image(
                annotated_rgb,
                caption=os.path.basename(p),
                use_container_width=True
            )

            if triple_mode:

                types_unique = sorted(
                    {str(d["vehicle_type"]) for d in vehicle_detections}
                )
                st.markdown(
                    f"**Vehicles:** {len(vehicle_detections)} "
                    f"(`{', '.join(types_unique) if types_unique else '—'}`) | "
                    f"**Plate regions:** {len(plate_detections)}"
                )
                st.markdown(
                    f"**Plate text (OCR):** `{plate_text if plate_text else '—'}`"
                )
                if plate_ocr_reads:
                    linked_types = sorted(
                        {
                            str(r["vehicle_type"])
                            for r in plate_ocr_reads
                            if r.get("vehicle_type")
                        }
                    )
                    st.markdown(
                        "**Vehicle type (matched to each plate):** "
                        f"`{', '.join(linked_types) if linked_types else '—'}`"
                    )

            else:

                st.markdown(
                    f"**Plate text:** `{plate_text if plate_text else '—'}` | **n:** {len(dets)}"
                )

            if show_sort_debug and not triple_mode and not car_only:

                st.write("Sorting:", sort_meta)

            if show_table:

                if triple_mode:

                    if vehicle_detections:

                        st.markdown("**Vehicles**")

                        st.dataframe(
                            vehicle_detections,
                            use_container_width=True
                        )

                    if plate_detections:

                        st.markdown("**Plate regions**")

                        st.dataframe(
                            plate_detections,
                            use_container_width=True
                        )

                    if plate_ocr_reads:

                        st.markdown("**OCR per plate**")

                        st.dataframe(
                            [
                                {
                                    "plate_index": r["plate_index"],
                                    "vehicle_type": r.get("vehicle_type"),
                                    "vehicle_conf": r.get("vehicle_conf"),
                                    "plate_text": r["plate_text"],
                                    "n_chars": r["n_chars"],
                                }
                                for r in plate_ocr_reads
                            ],
                            use_container_width=True,
                        )

                        if show_sort_debug:

                            for r in plate_ocr_reads:

                                st.write(
                                    f"Plate {r['plate_index']} sort:",
                                    r["sort_meta"],
                                )

                    if (
                        not vehicle_detections
                        and not plate_detections
                    ):

                        st.info(
                            "No vehicles or plates above the confidence threshold."
                        )

                elif len(dets) > 0:

                    if car_only:

                        st.markdown("**Detections (vehicle_type per box):**")

                    st.dataframe(
                        ordered_dets,
                        use_container_width=True
                    )

            st.divider()

            rec2 = {

                "image_path": p,
                "plate_text": plate_text,
                "rtl": rtl,
                "y_line_threshold": y_line_threshold,
                "sort_meta": sort_meta,

            }

            if triple_mode:

                rec2["vehicle_detections"] = vehicle_detections
                rec2["plate_detections"] = plate_detections
                rec2["plate_ocr_reads"] = plate_ocr_reads
                rec2["n_vehicles"] = len(vehicle_detections)
                rec2["n_plates"] = len(plate_detections)
                rec2["car_model_path"] = CAR_MODEL_PATH
                rec2["ocr_model_path"] = OCR_MODEL_PATH

            else:

                rec2["n"] = len(dets)
                rec2["detections"] = dets
                rec2["ordered_detections"] = ordered_dets
                if car_only:
                    rec2["car_model_path"] = CAR_MODEL_PATH

            out_json.append(rec2)

        ts = int(time.time())

        st.download_button(
            "Download JSON for random batch",
            data=json.dumps(
                out_json,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8"),
            file_name=f"random_results_{ts}.json",
            mime="application/json"
        )