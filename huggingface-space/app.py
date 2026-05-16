# ===================================================
# app.py — TRAFFIC SURVEILLANCE PIPELINE
# Car Detection → Plate Detection → OCR → Database
# ===================================================

import os, time, tempfile, json, sqlite3, datetime
import cv2
import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="TrafficVision AI",
    layout="wide",
    page_icon="🚦",
    initial_sidebar_state="expanded"
)

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&family=Orbitron:wght@400;700;900&display=swap');

    /* Base theme */
    html, body, [class*="css"] {
        background-color: #0a0d12;
        color: #c8d8e8;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0d12 0%, #0d1520 50%, #091018 100%);
        min-height: 100vh;
    }

    /* Scanline overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 255, 170, 0.015) 2px,
            rgba(0, 255, 170, 0.015) 4px
        );
        pointer-events: none;
        z-index: 9999;
    }

    /* Header */
    .main-header {
        font-family: 'Orbitron', monospace;
        font-size: 2.4rem;
        font-weight: 900;
        color: #00ffaa;
        text-shadow: 0 0 20px rgba(0,255,170,0.5), 0 0 60px rgba(0,255,170,0.2);
        letter-spacing: 0.1em;
        margin-bottom: 0;
        line-height: 1.1;
    }

    .sub-header {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.85rem;
        color: #4a7a6a;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* Pipeline stage cards */
    .pipeline-card {
        background: linear-gradient(135deg, #0f1a24 0%, #111d2a 100%);
        border: 1px solid #1a3040;
        border-left: 3px solid #00ffaa;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 12px;
        font-family: 'Rajdhani', sans-serif;
        position: relative;
        overflow: hidden;
    }

    .pipeline-card::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 60px; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0,255,170,0.03));
    }

    .pipeline-stage-num {
        font-family: 'Orbitron', monospace;
        font-size: 1.8rem;
        font-weight: 900;
        color: #00ffaa;
        opacity: 0.15;
        position: absolute;
        right: 16px;
        top: 8px;
    }

    .pipeline-stage-title {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #00ffaa;
        letter-spacing: 0.05em;
    }

    .pipeline-stage-desc {
        font-size: 0.82rem;
        color: #5a8a7a;
        font-family: 'Share Tech Mono', monospace;
        margin-top: 2px;
    }

    /* Stat boxes */
    .stat-box {
        background: #0d1820;
        border: 1px solid #1a3040;
        border-top: 2px solid #00ffaa;
        border-radius: 4px;
        padding: 14px 16px;
        text-align: center;
    }

    .stat-value {
        font-family: 'Orbitron', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #00ffaa;
        text-shadow: 0 0 12px rgba(0,255,170,0.4);
        line-height: 1;
    }

    .stat-label {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem;
        color: #4a6a5a;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        margin-top: 6px;
    }

    /* Section headers */
    .section-title {
        font-family: 'Orbitron', monospace;
        font-size: 0.9rem;
        color: #00ffaa;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        border-bottom: 1px solid #1a3040;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00ffaa 0%, #00cc88 100%);
        color: #0a0d12;
        font-family: 'Orbitron', monospace;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        border: none;
        border-radius: 4px;
        padding: 12px 28px;
        text-transform: uppercase;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 4px 20px rgba(0,255,170,0.25);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #00ffcc 0%, #00ffaa 100%);
        box-shadow: 0 4px 30px rgba(0,255,170,0.45);
        transform: translateY(-1px);
    }

    /* File uploader */
    .stFileUploader {
        background: #0d1820;
        border: 1px dashed #1a3a4a;
        border-radius: 6px;
        padding: 8px;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00ffaa, #00cc88);
        border-radius: 2px;
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid #1a3040;
        border-radius: 4px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #080c10;
        border-right: 1px solid #1a3040;
    }

    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stCheckbox label {
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.9rem;
        color: #8abaaa;
        font-weight: 600;
        letter-spacing: 0.05em;
    }

    /* Status badge */
    .status-live {
        display: inline-block;
        background: rgba(0,255,170,0.1);
        border: 1px solid #00ffaa;
        color: #00ffaa;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        padding: 2px 10px;
        border-radius: 2px;
        animation: blink 1.5s step-end infinite;
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .status-idle {
        display: inline-block;
        background: rgba(100,100,100,0.1);
        border: 1px solid #334;
        color: #556;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        padding: 2px 10px;
        border-radius: 2px;
    }

    /* Plate tag */
    .plate-tag {
        display: inline-block;
        background: #0a1a10;
        border: 1px solid #00ffaa;
        color: #00ffaa;
        font-family: 'Share Tech Mono', monospace;
        font-size: 1rem;
        padding: 4px 14px;
        border-radius: 3px;
        letter-spacing: 0.15em;
        margin: 2px 4px;
    }

    /* Alert boxes */
    .alert-success {
        background: rgba(0,255,170,0.08);
        border-left: 3px solid #00ffaa;
        padding: 10px 16px;
        border-radius: 3px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.85rem;
        color: #00ffaa;
        margin: 8px 0;
    }

    /* DB log entry */
    .log-entry {
        background: #0d1820;
        border-bottom: 1px solid #1a2a34;
        padding: 8px 12px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.78rem;
        color: #7aaaa0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .log-entry:hover {
        background: #101e2a;
    }

    .log-plate {
        color: #00ffaa;
        font-weight: bold;
        font-size: 0.95rem;
        letter-spacing: 0.1em;
    }

    /* Hide streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #1a3040;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)


# ===================== DATABASE =====================
DB_PATH = "traffic_surveillance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            frame_idx   INTEGER,
            car_id      INTEGER,
            car_bbox    TEXT,
            vehicle_class TEXT,
            plate_bbox  TEXT,
            plate_text  TEXT,
            ocr_conf    REAL,
            video_name  TEXT
        )
    """)
    # vehicle_stats: best detection per (session_id, car_id)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            car_id INTEGER NOT NULL,
            vehicle_class TEXT,
            best_plate_text TEXT,
            best_ocr_conf REAL,
            first_seen TEXT,
            last_seen TEXT,
            frame_idx INTEGER,
            car_bbox TEXT,
            video_name TEXT,
            UNIQUE(session_id, car_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            started_at  TEXT NOT NULL,
            video_name  TEXT,
            total_frames INTEGER DEFAULT 0,
            total_cars   INTEGER DEFAULT 0,
            total_plates INTEGER DEFAULT 0,
            fps_avg      REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

    # Ensure column exists for older DBs
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cols = [r[1] for r in c.execute("PRAGMA table_info(detections)")]
    if 'vehicle_class' not in cols:
        try:
            c.execute("ALTER TABLE detections ADD COLUMN vehicle_class TEXT")
            conn.commit()
        except Exception:
            pass
    conn.close()

    # ensure vehicle_stats exists if older DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            car_id INTEGER NOT NULL,
            vehicle_class TEXT,
            best_plate_text TEXT,
            best_ocr_conf REAL,
            first_seen TEXT,
            last_seen TEXT,
            frame_idx INTEGER,
            car_bbox TEXT,
            video_name TEXT,
            UNIQUE(session_id, car_id)
        )
    """)
    conn.commit()
    conn.close()

def insert_detection(session_id, frame_idx, car_id, car_bbox, plate_bbox, plate_text, ocr_conf, video_name, vehicle_class=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Insert including vehicle_class if the column exists
    cols = [r[1] for r in c.execute("PRAGMA table_info(detections)")]
    if 'vehicle_class' in cols:
        c.execute("""
            INSERT INTO detections
                (session_id, timestamp, frame_idx, car_id, car_bbox, vehicle_class, plate_bbox, plate_text, ocr_conf, video_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            datetime.datetime.now().isoformat(timespec='milliseconds'),
            frame_idx,
            car_id,
            json.dumps(car_bbox),
            vehicle_class,
            json.dumps(plate_bbox),
            plate_text,
            ocr_conf,
            video_name
        ))
    else:
        c.execute("""
            INSERT INTO detections
                (session_id, timestamp, frame_idx, car_id, car_bbox, plate_bbox, plate_text, ocr_conf, video_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            datetime.datetime.now().isoformat(timespec='milliseconds'),
            frame_idx,
            car_id,
            json.dumps(car_bbox),
            json.dumps(plate_bbox),
            plate_text,
            ocr_conf,
            video_name
        ))
    conn.commit()
    conn.close()

def update_session(session_id, total_frames, total_cars, total_plates, fps_avg):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE sessions SET total_frames=?, total_cars=?, total_plates=?, fps_avg=?
        WHERE id=?
    """, (total_frames, total_cars, total_plates, round(fps_avg, 2), session_id))
    conn.commit()
    conn.close()

def create_session(session_id, video_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO sessions (id, started_at, video_name)
        VALUES (?, ?, ?)
    """, (session_id, datetime.datetime.now().isoformat(), video_name))
    conn.commit()
    conn.close()

def get_all_detections():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM detections ORDER BY id DESC LIMIT 500", conn
    )
    conn.close()
    return df

def get_session_stats():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM sessions ORDER BY started_at DESC LIMIT 20", conn
    )
    conn.close()
    return df

def get_unique_plates():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT plate_text, COUNT(*) as detections, MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
        FROM detections WHERE plate_text != '' AND plate_text IS NOT NULL
        GROUP BY plate_text
        ORDER BY detections DESC
        LIMIT 100
    """, conn)
    conn.close()
    return df

def get_db_counts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
    unique_plates = c.execute("SELECT COUNT(DISTINCT plate_text) FROM detections WHERE plate_text != ''").fetchone()[0]
    sessions = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    conn.close()
    return total, unique_plates, sessions


def rebuild_vehicle_stats(session_id: str | None = None):
    """Recompute vehicle_stats table: choose the best detection (highest ocr_conf)
    per (session_id, car_id) and store aggregated row in vehicle_stats.
    If session_id is None, rebuild for all sessions.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM detections", conn)
    if df.empty:
        conn.close()
        return

    if session_id is not None:
        df = df[df['session_id'] == session_id]

    # normalize columns
    if 'ocr_conf' not in df.columns:
        df['ocr_conf'] = 0.0
    df['plate_text'] = df['plate_text'].fillna('')

    # compute plate text length and plate bbox area (if available)
    def plate_len(s):
        try:
            return len(s)
        except Exception:
            return 0

    def plate_area(b):
        try:
            bb = json.loads(b) if isinstance(b, str) else b
            if isinstance(bb, (list, tuple)) and len(bb) == 4:
                return max(0, (bb[2]-bb[0])) * max(0, (bb[3]-bb[1]))
        except Exception:
            pass
        return 0

    df['has_plate'] = df['plate_text'].apply(lambda x: 1 if plate_len(x) > 0 else 0)
    df['plate_len'] = df['plate_text'].apply(plate_len)
    if 'plate_bbox' in df.columns:
        df['plate_area'] = df['plate_bbox'].apply(plate_area)
    else:
        df['plate_area'] = 0

    # sort by preference: has_plate, plate_len, ocr_conf, plate_area, earliest timestamp
    df_sorted = df.sort_values(['has_plate','plate_len','ocr_conf','plate_area','timestamp'], ascending=[False, False, False, False, True])
    grouped = df_sorted.groupby(['session_id','car_id'], as_index=False).first()

    # write to vehicle_stats (insert or update existing rows)
    cur = conn.cursor()
    for _, row in grouped.iterrows():
        session = row['session_id']
        car_id = int(row['car_id']) if row['car_id'] is not None else 0
        vehicle_class = row.get('vehicle_class') if 'vehicle_class' in row else None
        best_plate = row.get('plate_text') if row.get('plate_text') else None
        best_conf = float(row.get('ocr_conf') or 0.0)
        first_seen = row.get('timestamp')
        last_seen = row.get('timestamp')
        frame_idx = int(row.get('frame_idx') or 0)
        car_bbox_json = json.dumps(row.get('car_bbox')) if row.get('car_bbox') is not None else None
        video_name = row.get('video_name')

        cur.execute('''
            INSERT INTO vehicle_stats (session_id, car_id, vehicle_class, best_plate_text, best_ocr_conf, first_seen, last_seen, frame_idx, car_bbox, video_name)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(session_id, car_id) DO UPDATE SET
                vehicle_class=excluded.vehicle_class,
                best_plate_text=excluded.best_plate_text,
                best_ocr_conf=excluded.best_ocr_conf,
                first_seen=excluded.first_seen,
                last_seen=excluded.last_seen,
                frame_idx=excluded.frame_idx,
                car_bbox=excluded.car_bbox,
                video_name=excluded.video_name
        ''', (
            session, car_id, vehicle_class, best_plate, best_conf, first_seen, last_seen, frame_idx, car_bbox_json, video_name
        ))
    conn.commit()
    conn.close()


# ===================== MODEL LOADING =====================
@st.cache_resource
def load_models(car_pt, plate_pt, ocr_pt):
    from ultralytics import YOLO
    car_model   = YOLO(car_pt)
    plate_model = YOLO(plate_pt)
    ocr_model   = YOLO(ocr_pt)
    return car_model, plate_model, ocr_model


# ===================== DRAWING HELPERS =====================
def draw_label(img, text, x, y, scale=0.6, color=(0,255,170)):
    cv2.putText(img, text, (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, 2, cv2.LINE_AA)

def draw_rect(img, x1, y1, x2, y2, color, thickness=2):
    cv2.rectangle(img, (x1,y1), (x2,y2), color, thickness)

def draw_corner_rect(img, x1, y1, x2, y2, color=(0,255,170), t=2, l=18):
    """Draws corner-style rectangle (surveillance aesthetic)."""
    # Top-left
    cv2.line(img,(x1,y1),(x1+l,y1),color,t)
    cv2.line(img,(x1,y1),(x1,y1+l),color,t)
    # Top-right
    cv2.line(img,(x2,y1),(x2-l,y1),color,t)
    cv2.line(img,(x2,y1),(x2,y1+l),color,t)
    # Bottom-left
    cv2.line(img,(x1,y2),(x1+l,y2),color,t)
    cv2.line(img,(x1,y2),(x1,y2-l),color,t)
    # Bottom-right
    cv2.line(img,(x2,y2),(x2-l,y2),color,t)
    cv2.line(img,(x2,y2),(x2,y2-l),color,t)


# ===================== STAGE 1: CAR DETECTION =====================
def stage1_detect_cars(frame, car_model, conf_car, imgsz=1280):
    """Returns list of car detections: (track_id, x1,y1,x2,y2, crop)"""
    pred = car_model.track(frame, persist=True, verbose=False, conf=conf_car, imgsz=imgsz)[0]
    cars = []
    if pred.boxes is None:
        return cars
    for box in pred.boxes:
        x1,y1,x2,y2 = map(int, box.xyxy[0])
        track_id = int(box.id[0]) if box.id is not None else -1
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        class_id = int(box.cls[0]) if box.cls is not None else None
        class_name = "Unknown"
        if class_id is not None:
            names = car_model.names
            if isinstance(names, dict):
                class_name = names.get(class_id, "Unknown")
            elif isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
                class_name = names[class_id]
        cars.append({
            "track_id": track_id,
            "bbox": (x1,y1,x2,y2),
            "crop": crop,
            "class_id": class_id,
            "class_name": class_name
        })
    return cars


# ===================== STAGE 2: PLATE DETECTION =====================
def stage2_detect_plates(car_data, plate_model, conf_plate, imgsz=640):
    """Takes car crops, returns plate detections with global coords."""
    results = []
    for car in car_data:
        x1,y1,x2,y2 = car["bbox"]
        crop = car["crop"]
        pred = plate_model.predict(crop, conf=conf_plate, imgsz=imgsz, verbose=False)[0]
        if pred.boxes is None:
            continue
        for pb in pred.boxes:
            px1,py1,px2,py2 = map(int, pb.xyxy[0])
            # Convert to global frame coords
            gx1,gy1 = x1+px1, y1+py1
            gx2,gy2 = x1+px2, y1+py2
            plate_crop = crop[py1:py2, px1:px2]
            if plate_crop.size == 0:
                continue
            results.append({
                "car_id": car["track_id"],
                "car_bbox": car["bbox"],
                "vehicle_class": car.get("class_name", "Unknown"),
                "plate_bbox": (gx1,gy1,gx2,gy2),
                "plate_crop": plate_crop
            })
    return results


# ===================== STAGE 3: OCR =====================
def stage3_run_ocr(plate_data, ocr_model, conf_ocr, imgsz=640, min_plate_width=320):
    """Takes plate crops, runs OCR, returns plate text + confidence."""
    results = []
    for pd_item in plate_data:
        plate_crop = pd_item["plate_crop"]
        # Preprocess plate crop: grayscale, CLAHE, denoise, sharpen, morphology
        try:
            plate_proc = plate_crop.copy()
            gray = cv2.cvtColor(plate_proc, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            # Morphological close to fill gaps
            kernel = np.ones((3,3), np.uint8)
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            # Sharpen
            kernel_sharp = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
            gray = cv2.filter2D(gray, -1, kernel_sharp)
            plate_proc = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        except Exception:
            plate_proc = plate_crop

        h, w = plate_proc.shape[:2]
        if w > 0 and w < min_plate_width:
            scale = min_plate_width / float(w)
            new_w = int(round(w * scale))
            new_h = int(round(h * scale))
            plate_proc = cv2.resize(plate_proc, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        res = ocr_model.predict(plate_proc, conf=conf_ocr, imgsz=imgsz, verbose=False)[0]
        chars = []
        confs = []
        if res.boxes is not None:
            for b in res.boxes:
                x1 = int(b.xyxy[0][0])
                c  = ocr_model.names[int(b.cls[0])]
                cf = float(b.conf[0])
                chars.append((x1, c))
                confs.append(cf)
        chars_sorted = sorted(chars, key=lambda x: x[0])
        text = "".join([c for _,c in chars_sorted])
        avg_conf = float(np.mean(confs)) if confs else 0.0
        results.append({
            **pd_item,
            "plate_text": text,
            "ocr_conf": round(avg_conf, 3)
        })
    return results


# ===================== FULL PIPELINE FRAME =====================
def process_frame(frame, car_model, plate_model, ocr_model,
                  conf_car, conf_plate, conf_ocr,
                  session_id, frame_idx, video_name,
                  show_car_id=True, show_conf=True,
                  track_imgsz=1280, plate_imgsz=640, ocr_imgsz=640):
    """
    Pipeline: Stage1 → Stage2 → Stage3
    Draws annotations and saves to DB.
    Returns (annotated_frame, frame_detections)
    """
    frame_detections = []

    # ── STAGE 1 ──────────────────────────────────────────
    cars = stage1_detect_cars(frame, car_model, conf_car, imgsz=track_imgsz)

    # ── STAGE 2 ──────────────────────────────────────────
    plates = stage2_detect_plates(cars, plate_model, conf_plate, imgsz=plate_imgsz)

    # ── STAGE 3 ──────────────────────────────────────────
    ocr_results = stage3_run_ocr(plates, ocr_model, conf_ocr, imgsz=ocr_imgsz)

    # ── DRAW ─────────────────────────────────────────────
    # Draw car/vehicle boxes (corner style)
    for car in cars:
        x1,y1,x2,y2 = car["bbox"]
        draw_corner_rect(frame, x1, y1, x2, y2, color=(0,255,170), t=2, l=20)
        # Always show detected class; show track id if requested
        cls_label = car.get("class_name", "CAR")
        id_part = f"#{car['track_id']}" if show_car_id and car.get('track_id', -1) >= 0 else ""
        draw_label(frame, f"{cls_label.upper()}{id_part}", x1, max(y1-10,14), 0.55, (0,255,170))

    # Draw plate boxes and OCR text
    for det in ocr_results:
        gx1,gy1,gx2,gy2 = det["plate_bbox"]
        draw_rect(frame, gx1, gy1, gx2, gy2, (0,80,255), 2)

        label = det["plate_text"]
        if show_conf and det["ocr_conf"] > 0:
            label += f" [{det['ocr_conf']:.2f}]"
        if label:
            # Background for text
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            cv2.rectangle(frame, (gx1, gy2+2), (gx1+tw+6, gy2+th+14), (0,0,0), -1)
            draw_label(frame, label, gx1+3, gy2+th+8, 0.65, (0,200,255))

        # ── DATABASE ────────────────────────────────────
        insert_detection(
            session_id=session_id,
            frame_idx=frame_idx,
            car_id=det["car_id"],
            car_bbox=list(det["car_bbox"]),
            plate_bbox=list(det["plate_bbox"]),
            plate_text=det["plate_text"],
            ocr_conf=det["ocr_conf"],
            video_name=video_name,
            vehicle_class=det.get("vehicle_class")
        )

        frame_detections.append(det)

    # HUD overlay
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw_label(frame, f"FRAME {frame_idx:05d}", 10, 22, 0.5, (0,255,170))
    draw_label(frame, ts, 10, frame.shape[0]-10, 0.45, (60,160,120))
    draw_label(frame, f"CARS:{len(cars)} PLATES:{len(ocr_results)}", 10, 44, 0.5, (0,200,180))

    return frame, frame_detections


# ===================== INIT DB =====================
init_db()

# ===================== SESSION STATE =====================
if "processing" not in st.session_state:
    st.session_state.processing = False
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("""
    <div style='font-family: Orbitron, monospace; font-size: 1.1rem; color: #00ffaa;
                letter-spacing: 0.15em; padding: 12px 0 18px 0; border-bottom: 1px solid #1a3040;
                text-align: center;'>
        ⚙ SYSTEM CONFIG
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">📂 MODEL PATHS</div>', unsafe_allow_html=True)

    car_pt   = st.text_input("Car Detection Model (.pt)",
                              value=r"D:\Grad_project\Car detect\yolo8_last_version(must).pt",
                              help="Path to your YOLOv8 car detection model")
    plate_pt = st.text_input("Plate Detection Model (.pt)",
                              value=r"D:\Grad_project\Plattes_detect\plattes_car.pt",
                              help="Path to your plate detection model")
    ocr_pt   = st.text_input("OCR Model (.pt)",
                              value=r"D:\Grad_project\merged_models\ocr.pt",
                              help="Path to your OCR model")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎛 CONFIDENCE THRESHOLDS</div>', unsafe_allow_html=True)

    conf_car   = st.slider("Stage 1 — Car Detection",   0.1, 1.0, 0.85, 0.05)
    conf_plate = st.slider("Stage 2 — Plate Detection", 0.05, 1.0, 0.10, 0.05)
    conf_ocr   = st.slider("Stage 3 — OCR",             0.05, 1.0, 0.10, 0.05)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🖥 DISPLAY OPTIONS</div>', unsafe_allow_html=True)

    show_car_id = st.checkbox("Show Car IDs", value=True)
    show_conf   = st.checkbox("Show OCR Confidence", value=True)
    skip_frames = st.slider("Process every Nth frame", 1, 5, 1,
                             help="1 = every frame; 2 = every other frame (faster)")

    st.markdown("<hr>", unsafe_allow_html=True)

    # DB quick stats
    total_det, unique_plates, total_sessions = get_db_counts()
    st.markdown(f"""
    <div style='font-family: Share Tech Mono, monospace; font-size: 0.72rem; color: #4a7a6a;
                line-height: 2;'>
        <span style='color:#00ffaa'>■</span> TOTAL DETECTIONS: {total_det}<br>
        <span style='color:#00ffaa'>■</span> UNIQUE PLATES: {unique_plates}<br>
        <span style='color:#00ffaa'>■</span> SESSIONS: {total_sessions}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑 Clear Database", use_container_width=True):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM detections")
        conn.execute("DELETE FROM sessions")
        conn.commit()
        conn.close()
        st.success("Database cleared.")
        st.rerun()


# ===================== MAIN LAYOUT =====================

# Header
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown("""
    <div>
        <div class='main-header'>🚦 TRAFFICVISION AI</div>
        <div class='sub-header'>▸ VEHICLE SURVEILLANCE &amp; PLATE RECOGNITION SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    status_html = '<span class="status-live">● LIVE</span>' if st.session_state.processing else '<span class="status-idle">○ IDLE</span>'
    st.markdown(f"""
    <div style='text-align:right; padding-top:18px;'>
        {status_html}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Pipeline diagram
st.markdown('<div class="section-title">▸ PROCESSING PIPELINE</div>', unsafe_allow_html=True)

pcol1, parrow1, pcol2, parrow2, pcol3 = st.columns([4, 0.5, 4, 0.5, 4])
with pcol1:
    st.markdown("""
    <div class='pipeline-card'>
        <div class='pipeline-stage-num'>01</div>
        <div class='pipeline-stage-title'>⬡ CAR DETECTION</div>
        <div class='pipeline-stage-desc'>YOLOv8 Tracker · Bounding box + Track ID</div>
    </div>
    """, unsafe_allow_html=True)
with parrow1:
    st.markdown("<div style='text-align:center; padding-top:22px; font-size:1.4rem; color:#00ffaa;'>→</div>", unsafe_allow_html=True)
with pcol2:
    st.markdown("""
    <div class='pipeline-card'>
        <div class='pipeline-stage-num'>02</div>
        <div class='pipeline-stage-title'>⬡ PLATE DETECTION</div>
        <div class='pipeline-stage-desc'>YOLOv8 · Locates license plate in car crop</div>
    </div>
    """, unsafe_allow_html=True)
with parrow2:
    st.markdown("<div style='text-align:center; padding-top:22px; font-size:1.4rem; color:#00ffaa;'>→</div>", unsafe_allow_html=True)
with pcol3:
    st.markdown("""
    <div class='pipeline-card'>
        <div class='pipeline-stage-num'>03</div>
        <div class='pipeline-stage-title'>⬡ OCR RECOGNITION</div>
        <div class='pipeline-stage-desc'>Character detection · Sorted left→right</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Upload + Run
st.markdown('<div class="section-title">▸ VIDEO INPUT</div>', unsafe_allow_html=True)

up_col, btn_col = st.columns([3,1])
with up_col:
    video_file = st.file_uploader(
        "Upload surveillance video",
        type=["mp4","avi","mov","mkv"],
        label_visibility="collapsed"
    )
with btn_col:
    run_btn = st.button("▶ START PIPELINE", use_container_width=True)

# ===================== PROCESSING =====================
if video_file and run_btn:

    # Validate model paths
    for path, name in [(car_pt,"Car"), (plate_pt,"Plate"), (ocr_pt,"OCR")]:
        if not os.path.exists(path):
            st.error(f"❌ {name} model not found at: `{path}`")
            st.stop()

    st.session_state.processing = True

    # Session ID
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.session_id = session_id
    video_name = video_file.name
    create_session(session_id, video_name)

    # Save temp file
    temp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_in.write(video_file.read())
    temp_in.close()

    # Load models
    with st.spinner("Loading models..."):
        try:
            car_model, plate_model, ocr_model = load_models(car_pt, plate_pt, ocr_pt)
        except Exception as e:
            st.error(f"Failed to load models: {e}")
            st.stop()

    cap = cv2.VideoCapture(temp_in.name)
    fps_src  = cap.get(cv2.CAP_PROP_FPS) or 25
    width    = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    desired_min_width = 1280
    output_width = max(width, desired_min_width)
    output_height = int(round(height * (output_width / width))) if width > 0 else height

    track_imgsz = min(max(640, max(width, height)), 1280)
    plate_imgsz = 640
    ocr_imgsz   = 640

    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_out.close()
    writer = cv2.VideoWriter(
        temp_out.name,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps_src, (output_width, output_height)
    )

    # UI placeholders
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">▸ LIVE FEED</div>', unsafe_allow_html=True)

    live_frame = st.empty()
    progress   = st.progress(0)

    metric_cols = st.columns(5)
    metric_placeholders = [c.empty() for c in metric_cols]

    st.markdown('<div class="section-title" style="margin-top:20px;">▸ LIVE DATABASE LOG</div>', unsafe_allow_html=True)
    db_log_ph  = st.empty()

    # Processing loop
    frame_idx = 0
    processed_count = 0
    t0 = time.time()
    all_detections = []
    total_cars_seen = set()
    total_plates_seen = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Skip frames if configured
        if (frame_idx % skip_frames) != 0:
            if frame.shape[1] != output_width or frame.shape[0] != output_height:
                frame_to_write = cv2.resize(frame, (output_width, output_height), interpolation=cv2.INTER_CUBIC)
            else:
                frame_to_write = frame
            writer.write(frame_to_write)
            progress.progress(min(frame_idx / total_frames, 1.0))
            continue

        processed_count += 1

        # Upscale low-resolution frames for better detection / OCR
        desired_min_width = 1280
        h, w = frame.shape[:2]
        if w > 0 and w < desired_min_width:
            scale = desired_min_width / float(w)
            new_w = int(round(w * scale))
            new_h = int(round(h * scale))
            frame_proc = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        else:
            frame_proc = frame

        annotated, detections = process_frame(
            frame_proc, car_model, plate_model, ocr_model,
            conf_car, conf_plate, conf_ocr,
            session_id, frame_idx, video_name,
            show_car_id, show_conf,
            track_imgsz=track_imgsz,
            plate_imgsz=plate_imgsz,
            ocr_imgsz=ocr_imgsz
        )

        all_detections.extend(detections)
        for d in detections:
            total_cars_seen.add(d["car_id"])
            if d["plate_text"]:
                total_plates_seen.add(d["plate_text"])

        if annotated.shape[1] != output_width or annotated.shape[0] != output_height:
            annotated_to_write = cv2.resize(annotated, (output_width, output_height), interpolation=cv2.INTER_CUBIC)
        else:
            annotated_to_write = annotated
        writer.write(annotated_to_write)

        # Live preview
        live_frame.image(
            cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
            channels="RGB",
            use_container_width=True
        )

        progress.progress(min(frame_idx / total_frames, 1.0))

        # Metrics
        elapsed = time.time() - t0
        curr_fps = processed_count / elapsed if elapsed > 0 else 0
        metric_labels = ["FRAME", "CARS", "PLATES", "FPS", "TIME"]
        metric_values = [
            f"{frame_idx}/{total_frames}",
            str(len(total_cars_seen)),
            str(len(total_plates_seen)),
            f"{curr_fps:.1f}",
            f"{elapsed:.0f}s"
        ]
        for ph, val, lbl in zip(metric_placeholders, metric_values, metric_labels):
            ph.markdown(f"""
            <div class='stat-box'>
                <div class='stat-value'>{val}</div>
                <div class='stat-label'>{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

        # Live DB log (last 6 detections)
        if all_detections:
            recent = all_detections[-6:][::-1]
            log_html = "<div style='border:1px solid #1a3040; border-radius:4px; overflow:hidden;'>"
            for d in recent:
                plate = d["plate_text"] or "—"
                log_html += f"""
                <div class='log-entry'>
                    <span>CAR#{d['car_id']} &nbsp; F:{d.get('frame','?')}</span>
                    <span class='log-plate'>{plate}</span>
                    <span style='color:#2a6a5a'>{d['ocr_conf']:.2f}</span>
                </div>
                """
            log_html += "</div>"
            db_log_ph.markdown(log_html, unsafe_allow_html=True)

    cap.release()
    writer.release()
    # Rebuild vehicle_stats for this session
    try:
        rebuild_vehicle_stats(session_id=session_id)
    except Exception:
        pass
    st.session_state.processing = False

    # Final session update
    dur = time.time() - t0
    final_fps = processed_count / dur if dur > 0 else 0
    update_session(session_id, frame_idx, len(total_cars_seen), len(total_plates_seen), final_fps)

    st.markdown(f"""
    <div class='alert-success'>
        ✔ PROCESSING COMPLETE &nbsp;|&nbsp; {frame_idx} frames &nbsp;|&nbsp;
        {len(total_cars_seen)} cars &nbsp;|&nbsp; {len(total_plates_seen)} unique plates &nbsp;|&nbsp;
        avg {final_fps:.2f} FPS &nbsp;|&nbsp; {dur:.1f}s total
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">▸ OUTPUT & DOWNLOAD</div>', unsafe_allow_html=True)

    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        st.video(temp_out.name)
        with open(temp_out.name, "rb") as f:
            st.download_button("⬇ Download Annotated Video", f, "output_annotated.mp4",
                               use_container_width=True)

    with dl_col2:
        json_data = json.dumps(all_detections, indent=2)
        st.download_button("⬇ Download JSON Results", json_data,
                           "detections.json", "application/json",
                           use_container_width=True)

    with dl_col3:
        with open(DB_PATH, "rb") as f:
            st.download_button("⬇ Download Database (.db)", f,
                               "traffic_surveillance.db",
                               use_container_width=True)

    # Temp cleanup
    try:
        os.unlink(temp_in.name)
    except:
        pass
# ===================== DASHBOARD =====================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-title">▸ DASHBOARD — STATISTICS</div>', unsafe_allow_html=True)

# Load detections and aggregate
db_df = get_all_detections()
total_det, unique_plates, total_sessions = get_db_counts()

if db_df.empty:
    st.markdown("<div style='color:#334; font-family:Share Tech Mono,monospace; padding:20px; text-align:center;'>NO DATA YET — RUN THE PIPELINE TO POPULATE THE DATABASE</div>", unsafe_allow_html=True)
else:
    # Top metrics
    m1, m2, m3, m4 = st.columns(4)
    avg_ocr = db_df['ocr_conf'].mean() if 'ocr_conf' in db_df.columns else 0.0
    with m1:
        st.metric("Total Detections", f"{total_det}")
    with m2:
        st.metric("Unique Plates", f"{unique_plates}")
    with m3:
        st.metric("Sessions", f"{total_sessions}")
    with m4:
        st.metric("Avg OCR Confidence", f"{avg_ocr:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Time series
    try:
        db_df['ts'] = pd.to_datetime(db_df['timestamp'])
        ts = db_df.groupby(db_df['ts'].dt.date).size()
        st.subheader("Detections Over Time")
        fig, ax = plt.subplots()
        ax.plot([str(x) for x in ts.index], ts.values, marker='o')
        ax.set_xlabel('Date')
        ax.set_ylabel('Detections')
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)
    except Exception:
        pass

    # Top plates
    st.subheader("Top Plates")
    top_plates = db_df['plate_text'].fillna('—').value_counts().head(10)
    fig2, ax2 = plt.subplots()
    ax2.bar([str(x) for x in top_plates.index], top_plates.values)
    ax2.set_xlabel('Plate')
    ax2.set_ylabel('Count')
    ax2.tick_params(axis='x', rotation=45)
    st.pyplot(fig2)

    # Recent detections
    st.subheader("Recent Detections")
    recent = db_df.sort_values('id', ascending=False).head(10)
    st.dataframe(recent[['id','timestamp','frame_idx','car_id','plate_text','ocr_conf','video_name']], use_container_width=True)

    # Vehicle stats (best per track id)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Vehicle Stats (best detection per track)")
    conn = sqlite3.connect(DB_PATH)
    # prefer current session if available
    current_session = st.session_state.get("session_id", None)
    try:
        if current_session:
            vs_df = pd.read_sql_query("SELECT * FROM vehicle_stats WHERE session_id=? ORDER BY best_ocr_conf DESC", conn, params=(current_session,))
        else:
            vs_df = pd.read_sql_query("SELECT * FROM vehicle_stats ORDER BY best_ocr_conf DESC", conn)
    except Exception:
        vs_df = pd.DataFrame()
    conn.close()
    if vs_df.empty:
        st.markdown("<div style='color:#334; font-family:Share Tech Mono,monospace; padding:10px;'>No vehicle stats yet.</div>", unsafe_allow_html=True)
    else:
        st.dataframe(vs_df[['session_id','car_id','vehicle_class','best_plate_text','best_ocr_conf','first_seen','frame_idx','video_name']], use_container_width=True)


# ===================== DATABASE VIEWER =====================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-title">▸ SURVEILLANCE DATABASE</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 All Detections", "🔢 Unique Plates", "📁 Sessions"])

with tab1:
    df = get_all_detections()
    if df.empty:
        st.markdown("<div style='color:#334; font-family:Share Tech Mono,monospace; padding:20px; text-align:center;'>NO DATA YET — RUN THE PIPELINE TO POPULATE THE DATABASE</div>", unsafe_allow_html=True)
    else:
        # Quick filter
        filter_text = st.text_input("🔍 Filter by plate text", placeholder="e.g. ABC123",
                                     label_visibility="visible", key="filter_plates")
        if filter_text:
            df = df[df["plate_text"].str.contains(filter_text, case=False, na=False)]
        st.dataframe(
            df[["id","timestamp","frame_idx","car_id","plate_text","ocr_conf","video_name","session_id"]],
            use_container_width=True,
            height=350
        )
        st.markdown(f"<div style='font-family:Share Tech Mono,monospace; font-size:0.7rem; color:#4a6a5a;'>SHOWING {len(df)} RECORDS (LAST 500)</div>", unsafe_allow_html=True)

with tab2:
    up_df = get_unique_plates()
    if up_df.empty:
        st.markdown("<div style='color:#334; font-family:Share Tech Mono,monospace; padding:20px; text-align:center;'>NO PLATES DETECTED YET</div>", unsafe_allow_html=True)
    else:
        # Show as cards + table
        st.markdown("**Recently detected plates:**")
        plate_html = ""
        for _, row in up_df.head(20).iterrows():
            plate_html += f"<span class='plate-tag'>{row['plate_text']}</span>"
        st.markdown(plate_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(up_df, use_container_width=True, height=300)

with tab3:
    sess_df = get_session_stats()
    if sess_df.empty:
        st.markdown("<div style='color:#334; font-family:Share Tech Mono,monospace; padding:20px; text-align:center;'>NO SESSIONS YET</div>", unsafe_allow_html=True)
    else:
        st.dataframe(sess_df, use_container_width=True, height=300)
